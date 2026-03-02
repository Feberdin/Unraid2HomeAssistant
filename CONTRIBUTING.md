# Contributing

Danke fuer deinen Beitrag zu `Unraid Docker Control`.

## Entwicklung lokal

1. Repository klonen
2. In Home Assistant als Custom Integration laden
3. Aenderungen machen
4. Syntaxpruefung ausfuehren:

```bash
python3 -m py_compile custom_components/unraid_docker/*.py
```

## Pull Request Regeln

- Kleine, fokussierte PRs
- Klare Commit-Messages (`feat:`, `fix:`, `docs:`)
- Bei neuen Features README und `services.yaml` aktualisieren
- Auf saubere Fehlermeldungen und Logging achten

## Code-Qualitaet

- Lesbarer, kommentierter Code
- Defensive Fehlerbehandlung
- Keine sensiblen Daten in Logs oder Commits
