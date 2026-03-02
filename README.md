# Unraid Docker Control

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-41BDF5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange)](https://hacs.xyz/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

Steuere und ueberwache Docker-Container auf deinem Unraid-Server direkt in Home Assistant.

## Kurzbeschreibung

Diese Integration verbindet Home Assistant per SSH mit Unraid und stellt folgende Funktionen bereit:

- Container starten, stoppen und neustarten
- Laufstatus als Binary Sensoren
- CPU-/RAM-/Status-Sensoren je Container
- Host-Uptime und Unraid-Version
- Services fuer Automationen und Skripte

## Features

- Vollstaendiger Config Flow in Home Assistant
- HACS-kompatibles Repository
- Polling ueber `DataUpdateCoordinator`
- Fehler- und Debug-Logging fuer schnelle Diagnose
- Mehrere Unraid-Hosts via separater Config Entries moeglich

## Voraussetzungen

- Home Assistant (aktuelle Version)
- HACS installiert
- Unraid mit aktiviertem SSH
- Benutzer mit Docker-Rechten auf Unraid

## Installation (HACS)

1. HACS -> `Integrations` -> `Custom repositories`.
2. Repository URL hinzufuegen:
   - `https://github.com/Feberdin/Unraid2HomeAssistant`
   - Kategorie: `Integration`
3. `Unraid Docker Control` installieren.
4. Home Assistant neu starten.
5. `Einstellungen -> Geraete & Dienste -> Integration hinzufuegen` und `Unraid Docker Control` waehlen.

## Konfiguration

Der Config Flow fragt folgende Werte ab:

- `Host` (IP oder DNS von Unraid)
- `SSH Port` (Standard `22`)
- `Benutzername`
- `Passwort`
- `Known hosts` (optional)
- `Polling Intervall` in Sekunden (Standard `30`)

## Entitaeten

Pro Container:

- `switch.<container>`
- `binary_sensor.<container>_running`
- `sensor.<container>_status`
- `sensor.<container>_cpu`
- `sensor.<container>_memory`

Pro Host:

- `sensor.<host>_host_uptime`

## Services

- `unraid_docker.start_container`
- `unraid_docker.stop_container`
- `unraid_docker.restart_container`

Service-Daten:

- `container` (Pflicht): Container-Name oder Container-ID
- `entry_id` (optional): konkrete Config Entry bei mehreren Hosts

Beispiel:

```yaml
service: unraid_docker.restart_container
data:
  container: plex
```

## Troubleshooting

### Verbindung fehlgeschlagen

1. SSH-Verbindung von Home Assistant Host zu Unraid pruefen.
2. Auf Unraid sicherstellen, dass `sshd` auf dem konfigurierten Port lauscht.
3. Docker-Test auf Unraid: `docker --version`.

### AsyncSSH Konflikt mit anderen Integrationen

Home Assistant teilt Python-Abhaengigkeiten zwischen Integrationen. Bei Konflikten:

1. `ha core stop`
2. `rm -rf /config/deps/*asyncssh*`
3. `ha core start`

## Debug-Logging

```yaml
logger:
  default: info
  logs:
    custom_components.unraid_docker: debug
    asyncssh: debug
```

## Entwicklung

Lokale Syntaxpruefung:

```bash
python3 -m py_compile custom_components/unraid_docker/*.py
```

## Projektstruktur

```text
custom_components/unraid_docker/
├── __init__.py
├── binary_sensor.py
├── config_flow.py
├── const.py
├── coordinator.py
├── manifest.json
├── sensor.py
├── services.yaml
├── strings.json
├── switch.py
├── translations/
│   ├── de.json
│   └── en.json
└── unraid_api.py
```

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](./LICENSE).
