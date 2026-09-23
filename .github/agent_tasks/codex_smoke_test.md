# Codex Smoke Test – Trading Agent

## Zweck

Dies ist ausschließlich ein kontrollierter Verbindungstest für Codex
innerhalb von GitHub Actions.

Das Projekt ist ein Paper-Trading-/Simulationsprojekt.

## HARTE REGELN

1. Keine Änderungen an Projektdateien.
2. Keine Commits.
3. Kein Push.
4. Keine Pull Requests erstellen.
5. Keine GitHub-Einstellungen verändern.
6. Keine Secrets auslesen, anzeigen, kopieren oder anderweitig offenlegen.
7. Keine Live-Trading-Funktion aktivieren.
8. Keine Sicherheitsprüfungen abschwächen oder entfernen.
9. Keine Dateien außerhalb des Repository-Arbeitsverzeichnisses verändern.
10. Keine echten Trades oder externen Trading-Aktionen durchführen.

## Aufgaben

1. Lies die Projektstruktur.
2. Lies insbesondere:
   - config/settings.py
   - data/quality.py
   - execution/execution_guard.py
   - execution/paper_broker.py
   - .github/workflows/tests.yml
   - .github/agent_tasks/fix_timestamp_quality.md
3. Prüfe den aktuellen Git-Status.
4. Führe die vorhandene Testsuite mit
   `python -m pytest -q`
   aus.
5. Ermittle exakt:
   - Anzahl bestandener Tests
   - Anzahl fehlgeschlagener Tests
   - Namen der fehlgeschlagenen Tests
6. Prüfe die Paper-Trading-Sicherheitswerte:
   - PAPER_ONLY muss True sein.
   - LIVE_TRADING_ENABLED muss False sein.
7. Analysiere die vier bekannten Timestamp-Fehler nicht durch Änderungen,
   sondern beschreibe nur deren Ursache anhand des vorhandenen Codes.
8. Prüfe, ob seit dem Start des Jobs Änderungen im Arbeitsverzeichnis
   vorhanden sind.
9. Nimm keinerlei Änderungen am Projekt vor.

## Ergebnis

Gib am Ende einen kurzen strukturierten Bericht aus:

STATUS:
TESTS:
FAILED TESTS:
PAPER_ONLY:
LIVE_TRADING_ENABLED:
GIT STATUS:
TIMESTAMP ISSUE:
RECOMMENDATION:

Die RECOMMENDATION darf ausschließlich eine technische nächste Maßnahme
beschreiben. Sie darf keine Änderung selbst durchführen.
