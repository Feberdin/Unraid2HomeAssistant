"""Update Coordinator fuer Unraid Docker Daten."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .unraid_api import UnraidApiClient, UnraidApiError

_LOGGER = logging.getLogger(__name__)


class UnraidDockerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Koordiniert zyklische Datenabfragen am Unraid Host."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: UnraidApiClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Laedt Host- und Containerdaten in einem Polling-Zyklus."""
        try:
            host_info, containers = await self._fetch_all()
            return {"host": host_info, "containers": containers}
        except UnraidApiError as err:
            raise UpdateFailed(f"Unraid Daten konnten nicht geladen werden: {err}") from err

    async def _fetch_all(self) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        """Hilfsmethode fuer gemeinsame Datenabfrage."""
        host_info, containers = await asyncio.gather(
            self.api.fetch_host_info(),
            self.api.fetch_containers(),
        )
        return host_info, containers
