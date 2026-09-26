# Entwicklungsorchestrierung

Stand: 2026-09-25

Dieses Dokument definiert die technische Umsetzung des Prinzips:

> Arbeit, die ein Runner, Worker oder Agent parallel erledigen kann, soll nicht auf den Haupt-Chat warten.

## Zielarchitektur

```
Steuer-/Research-Agent
        |
        +--> Coding-Agenten (asynchron, PR-basiert)
        |       +--> Engineering
        |       +--> Tests / Review
        |
        +--> Deterministische Worker (GitHub Actions)
        |       +--> Daten-Collect
        |       +--> Backtests / Validation
        |       +--> Coverage / Preflight
        |
        +--> Evidence-/Status-Kontinuität
                +--> PROJECT_STATUS.md
                +--> project_state.json
                +--> trial_ledger.json
                +--> Workflow-Artefakte
```

## Canonical Data Layer

Yahoo-OHLCV-Coverage verwendet die zentrale Schicht `data/canonical_snapshot.py`. Sie bildet Study-Window, Cross-Symbol-Intersection und exakt die gemeinsame Snapshot-Geometrie an einer Stelle. Coverage-Runner dürfen keine parallele Kalender-/Snapshot-Implementierung mehr einführen.

Die Datenebene ist ein serialer Kontrollpunkt innerhalb eines Research-Laufs:

`acquisition -> coverage -> freeze -> deterministic analysis`

Unabhängige Symbole/Quellen werden innerhalb der Akquisition parallelisiert; das eingefrorene Ergebnis ist anschließend die gemeinsame Eingabe für Diagnose und formale Berechnung.

## Was bereits funktioniert

Q016 demonstriert den Worker-Pool bereits praktisch: vier unabhängige Collect-Jobs laufen parallel; danach aggregiert ein eigener Job die Checkpoints, friert den Input ein und führt die Diagnose aus. Dadurch wartet der Aggregationspfad nicht seriell auf jeden Download.

## Was der Coding-Agent ergänzt

GitHub Copilot Cloud Agent ist der asynchrone Implementierungs-Worker. Eine Aufgabe wird als GitHub Issue formuliert und Copilot zugewiesen; der Agent arbeitet autonom, erstellt einen Pull Request und fordert anschließend Review an. Das ist getrennt von deterministischen Actions und erzeugt eine überprüfbare Code-Provenienz.

Repositoryseitig vorbereitet sind:
- `.github/copilot-instructions.md`
- `AGENTS.md`
- `.github/agents/trading-agent-engineer.agent.md`
- `.github/agents/trading-agent-research-reviewer.agent.md`
- `.github/workflows/copilot-setup-steps.yml`

## Betriebsmodell

1. Der Steuer-Agent erzeugt eine klar abgegrenzte Engineering-Aufgabe.
2. Die Aufgabe wird einem Copilot-Coding-Agenten zugewiesen.
3. Der Agent arbeitet auf eigenem Branch und liefert einen PR.
4. CI führt Tests und Governance-Prüfungen aus.
5. Der Steuer-Agent prüft Diff, Testresultate und Provenienz.
6. Erst danach wird gemergt.
7. Unabhängige Rechen-/Research-Jobs werden parallel als Actions-Matrix oder getrennte Workflows gestartet.
8. Status- und Evidence-Dateien werden nach jedem belastbaren Meilenstein synchronisiert.

## Keine künstliche Serialisierung

Nicht nacheinander ausführen, wenn die Abhängigkeit fehlt:
- unabhängige Test-/Lint-/Review-Jobs
- unabhängige Daten-Chunks
- unabhängige diagnostische Analysen
- getrennte Coverage-Preflights
- mehrere klar isolierte Engineering-Aufgaben

Seriell bleiben:
- Freeze -> Analyse desselben Frozen Inputs
- formale Freigabe -> formaler Trial
- Ergebnis -> Evidence-Gate
- PR-Review -> Merge

## Agenten- und Sicherheitsgrenzen

Agenten dürfen keine Live-Ausführung herstellen, keine automatische Promotion aktivieren und keine Research-Gates umgehen. Agentenoutput ist Hypothese/Implementierung/Review-Material, nicht selbst Evidenz.

## Kontinuität über Chats

Der Einstiegspunkt bleibt `docs/TRADING_AGENT_CHAT_ENTRYPOINT.md`. Bei einem neuen Chat wird der dort definierte Verifikationsablauf ausgeführt. Handoff-Text aus dem letzten Chat wird gegen kanonische Quellen geprüft; er ersetzt diese nicht.
