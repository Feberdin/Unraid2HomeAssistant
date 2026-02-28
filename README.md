# Unraid Docker Control (Home Assistant + HACS)

Diese Custom Integration verbindet Home Assistant per SSH mit einem Unraid-Server und bietet:

- Auslesen von Host-Informationen (Hostname, Uptime, Unraid-Version)
- Ueberwachung von Docker-Containern (Status, CPU, RAM)
- Steuerung von Containern (Start/Stop/Restart)

## Features

- HACS-kompatible Struktur
- Config Flow in Home Assistant UI
- Polling ueber `DataUpdateCoordinator`
- Services fuer Container-Steuerung
- Umfangreiches Logging fuer Debugging
- Kommentierter Code fuer einfache Erweiterbarkeit

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

## Voraussetzungen

- Home Assistant mit Unterstuetzung fuer Custom Integrations
- HACS installiert
- SSH-Zugriff auf Unraid aktiviert
- Benutzer mit Berechtigung fuer `docker` Kommandos auf Unraid

## Installation mit HACS

1. Repository in HACS als Custom Repository hinzufuegen:
   - URL: `https://github.com/Feberdin/Unraid2HomeAssistant`
   - Kategorie: `Integration`
2. Integration `Unraid Docker Control` installieren.
3. Home Assistant neu starten.
4. Unter `Einstellungen -> Geraete & Dienste -> Integration hinzufuegen` nach `Unraid Docker Control` suchen.

## Konfiguration

Beim Einrichten werden folgende Felder abgefragt:

- `Host`: IP oder DNS-Name deines Unraid-Servers
- `SSH Port`: Standard `22`
- `Benutzername`
- `Passwort`
- `Known hosts` (optional)
- `Polling Intervall` (Sekunden, Standard `30`)

## Entitaeten

Die Integration erzeugt automatisch:

- Pro Container:
  - `switch.<container>` (Start/Stop)
  - `binary_sensor.<container>_running`
  - `sensor.<container>_status`
  - `sensor.<container>_cpu`
  - `sensor.<container>_memory`
- Pro Host:
  - `sensor.<host>_host_uptime`

## Services

### `unraid_docker.start_container`
Startet einen Container.

### `unraid_docker.stop_container`
Stoppt einen Container.

### `unraid_docker.restart_container`
Startet einen Container neu.

Gemeinsame Parameter:

- `container` (Pflicht): Name oder ID des Containers
- `entry_id` (optional): Bei mehreren Unraid-Instanzen gezielt eine Config Entry auswaehlen

Beispiel (Developer Tools -> Services):

```yaml
service: unraid_docker.restart_container
data:
  container: plex
```

## Debugging

In `configuration.yaml` kannst du Debug-Logs aktivieren:

```yaml
logger:
  default: info
  logs:
    custom_components.unraid_docker: debug
    asyncssh: debug
```

Typische Fehlerbilder:

- `Authentication failed`
  - Benutzername/Passwort pruefen
  - SSH Zugriff auf Unraid pruefen
- `docker --version` Fehler im Config Flow
  - Benutzer hat keine Docker-Berechtigung
  - Docker-Service auf Unraid nicht aktiv
- `Timeout` bei Kommandos
  - Netzwerk/Latenz pruefen
  - Polling-Intervall ggf. erhoehen

## Sicherheitshinweise

- Verwende nach Moeglichkeit einen dedizierten Unraid-Benutzer mit minimalen Rechten.
- Wenn moeglich, nutze SSH Keys statt Passwort (kann als Erweiterung eingebaut werden).
- Leite den SSH-Port nicht ungeschuetzt ins Internet weiter.

## Entwicklung

Empfohlene lokale Pruefung:

```bash
python3 -m py_compile custom_components/unraid_docker/*.py
```

## Roadmap

- SSH-Key-Authentifizierung
- Detaillierte Unraid-Array Sensoren
- Buttons fuer Container-Neustart in UI
- Diagnostics-Unterstuetzung

## Lizenz

Derzeit keine Lizenz gesetzt. Fuer Open-Source-Freigabe bitte `LICENSE` ergaenzen.
