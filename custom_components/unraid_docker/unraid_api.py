"""SSH-basierte API fuer Unraid und Docker Kommandos."""

from __future__ import annotations

import asyncio
import json
import logging
import shlex
from dataclasses import dataclass
from typing import Any

import asyncssh

_LOGGER = logging.getLogger(__name__)


class UnraidApiError(Exception):
    """Basisklasse fuer API-Fehler."""


class UnraidAuthenticationError(UnraidApiError):
    """Fehler bei SSH-Authentifizierung."""


class UnraidCommandError(UnraidApiError):
    """Fehler bei der Ausfuehrung eines Remote-Kommandos."""


@dataclass(slots=True)
class UnraidConnectionConfig:
    """Konfiguration fuer den SSH-Verbindungsaufbau."""

    host: str
    port: int
    username: str
    password: str
    known_hosts: str | None
    connect_timeout: int = 10
    command_timeout: int = 20


class UnraidApiClient:
    """Kapselt SSH-Kommandos gegen einen Unraid-Host."""

    def __init__(self, config: UnraidConnectionConfig) -> None:
        self._config = config

    async def _run_command(self, command: str) -> str:
        """Fuehrt ein Kommando per SSH aus und gibt stdout zurueck."""
        _LOGGER.debug("Fuehre Unraid Kommando aus: %s", command)

        known_hosts: str | None | bool = self._config.known_hosts
        if known_hosts == "":
            known_hosts = None

        try:
            conn = await asyncio.wait_for(
                asyncssh.connect(
                    self._config.host,
                    port=self._config.port,
                    username=self._config.username,
                    password=self._config.password,
                    known_hosts=known_hosts,
                ),
                timeout=self._config.connect_timeout,
            )
        except asyncssh.PermissionDenied as err:
            raise UnraidAuthenticationError(
                "SSH Anmeldung fehlgeschlagen. Bitte Zugangsdaten pruefen."
            ) from err
        except (asyncssh.Error, TimeoutError) as err:
            raise UnraidApiError(
                f"SSH Verbindung zu {self._config.host}:{self._config.port} fehlgeschlagen"
            ) from err

        try:
            result = await asyncio.wait_for(
                conn.run(command, check=False),
                timeout=self._config.command_timeout,
            )
        except TimeoutError as err:
            raise UnraidCommandError(f"Timeout bei Kommando: {command}") from err
        finally:
            conn.close()

        if result.exit_status != 0:
            stderr = (result.stderr or "").strip()
            raise UnraidCommandError(
                f"Kommando fehlgeschlagen (Exit {result.exit_status}): {command}; stderr: {stderr}"
            )

        return (result.stdout or "").strip()

    async def test_connection(self) -> None:
        """Prueft SSH Zugriff und Docker Verfuegbarkeit."""
        await self._run_command("docker --version")

    async def fetch_host_info(self) -> dict[str, Any]:
        """Liest grundlegende Host-Informationen von Unraid."""
        hostname, uptime_raw, version = await asyncio.gather(
            self._run_command("hostname"),
            self._run_command("cat /proc/uptime"),
            self._run_command("cat /etc/unraid-version 2>/dev/null || echo unknown"),
        )

        uptime_seconds = 0
        try:
            uptime_seconds = int(float(uptime_raw.split()[0]))
        except (ValueError, IndexError):
            _LOGGER.warning("Konnte Uptime nicht parsen: %s", uptime_raw)

        return {
            "hostname": hostname,
            "uptime_seconds": uptime_seconds,
            "unraid_version": version,
        }

    async def fetch_containers(self) -> dict[str, dict[str, Any]]:
        """Liest Containerliste und Laufzeitmetriken aus Docker."""
        container_lines, stats_lines = await asyncio.gather(
            self._run_command("docker ps -a --format '{{json .}}'"),
            self._run_command("docker stats --no-stream --format '{{json .}}'"),
        )

        containers: dict[str, dict[str, Any]] = {}

        for line in container_lines.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                _LOGGER.warning("Ungueltige JSON-Zeile in docker ps: %s", line)
                continue

            container_id = parsed.get("ID")
            name = parsed.get("Names")
            if not container_id or not name:
                continue

            containers[container_id] = {
                "id": container_id,
                "name": name,
                "image": parsed.get("Image", "unknown"),
                "state": parsed.get("State", "unknown"),
                "status": parsed.get("Status", "unknown"),
                "cpu_percent": 0.0,
                "mem_percent": 0.0,
                "mem_usage": "unknown",
            }

        stats_by_name: dict[str, dict[str, Any]] = {}
        for line in stats_lines.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                _LOGGER.warning("Ungueltige JSON-Zeile in docker stats: %s", line)
                continue

            stats_name = parsed.get("Name") or parsed.get("Container")
            if not stats_name:
                continue

            stats_by_name[stats_name] = parsed

        for container in containers.values():
            stats = stats_by_name.get(container["name"])
            if not stats:
                continue

            container["cpu_percent"] = _parse_percent(stats.get("CPUPerc", "0"))
            container["mem_percent"] = _parse_percent(stats.get("MemPerc", "0"))
            container["mem_usage"] = stats.get("MemUsage", "unknown")

        return containers

    async def start_container(self, container: str) -> None:
        """Startet einen Container per Name oder ID."""
        safe_container = shlex.quote(container)
        await self._run_command(f"docker start {safe_container}")

    async def stop_container(self, container: str) -> None:
        """Stoppt einen Container per Name oder ID."""
        safe_container = shlex.quote(container)
        await self._run_command(f"docker stop {safe_container}")

    async def restart_container(self, container: str) -> None:
        """Startet einen Container neu per Name oder ID."""
        safe_container = shlex.quote(container)
        await self._run_command(f"docker restart {safe_container}")


def _parse_percent(raw_value: str) -> float:
    """Wandelt Prozent-Strings wie '4.53%' in float um."""
    if not raw_value:
        return 0.0

    value = raw_value.strip().replace("%", "")
    try:
        return float(value)
    except ValueError:
        return 0.0
