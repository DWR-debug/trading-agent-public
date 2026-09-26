# Entwicklungsorchestrierung

Stand: 2026-09-26

Dieses Dokument definiert die technische Umsetzung des Prinzips:

> Arbeit, die ein Runner, Worker oder Agent parallel erledigen kann, soll nicht auf den Haupt-Chat warten.

## Zielarchitektur

\`\`\`
Steuer-/Research-Agent
        |
        +--> Coding-Agenten (asynchron, PR-basiert)
        |       +--> Engineering
        |       +--> Tests / Review
        |
        +--> Self-hosted Research Worker
        |       +--> QA
        |       +--> Reproduktion
        |       +--> vorbereitende Rechenlast
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
\`\`\`

## Rollen

Der Steuer-/Research-Agent führt fachlich und administrativ.

Der Coding-Agent übernimmt klar abgegrenzte PR-fähige Engineering-, Test- und
Dokumentationsarbeit.

Der Self-hosted Research Worker stellt zusätzliche lokale Rechenzeit für QA, Reproduktion
und vorbereitende nicht-kanonische Berechnungen bereit. Er wird nicht als allgemeiner
PR-Runner verwendet.

GitHub-hosted Actions bleiben der kanonische Pfad für CI sowie formale, reproduzierbare
Research-Ausführung.

## Betriebsmodell

1. Der Steuer-Agent klassifiziert die Aufgabe.
2. Bounded Engineering geht an den Coding-Agenten.
3. QA/Reproduktion/vorbereitende Rechenlast kann an den Self-hosted Worker delegiert werden.
4. Kanonische Berechnung läuft auf reproduzierbaren GitHub-hosted Pfaden.
5. CI und unabhängige QA prüfen Diff, Testresultate und Provenienz.
6. Evidence- und Statusdateien werden erst nach belastbaren Meilensteinen synchronisiert.

## Keine künstliche Serialisierung

Parallelisieren, sofern keine Abhängigkeit fehlt:

- unabhängige Test-/Lint-/Review-Jobs;
- unabhängige Daten-Chunks;
- unabhängige diagnostische Analysen;
- getrennte Coverage-Preflights;
- mehrere klar isolierte Engineering-Aufgaben;
- Self-hosted QA-/Reproduktionsläufe.

Seriell bleiben:

- Freeze -> Analyse desselben Frozen Inputs;
- formale Freigabe -> formaler Trial;
- Ergebnis -> Evidence-Gate;
- PR-Review -> Merge.

## Sicherheitsgrenze

Der öffentliche Repository-Kontext darf keinen untrusted Fork-/PR-Code automatisch auf
einem Self-hosted Runner ausführen. Der vorgesehene Workflow akzeptiert deshalb nur manuelle,
owner-gesteuerte Ausführung und vertrauenswürdige Refs.

Der Runner erhält keine Trading-Secrets und keine Live-Ausführungsrechte.

## Agenten- und Sicherheitsgrenzen

Agenten dürfen keine Live-Ausführung herstellen, keine automatische Promotion aktivieren
und keine Research-Gates umgehen. Agentenoutput ist Hypothese/Implementierung/Review-
Material, nicht selbst Evidenz.

\`Self-hosted Worker -> Artefakt -> kanonische Reproduktion -> Evidence-Gate\` bleibt die
Regel für wissenschaftlich relevante Ergebnisse.

## Kontinuität über Chats

Der Einstiegspunkt bleibt \`docs/TRADING_AGENT_CHAT_ENTRYPOINT.md\`. Handoff-Text aus dem
letzten Chat wird gegen kanonische Quellen geprüft; er ersetzt diese nicht.

## Project-State-Freshness

\`automation/project_state_freshness_check.py\` vergleicht den unveränderten
\`project_state.json\` mit \`current_project_checkpoint.json\` und der verifizierten
Master-Revision. In Pull-Request-Actions stammt die Revision aus
\`pull_request.base.sha\`, auf einem Master-Push aus \`GITHUB_SHA\`, lokal aus
\`refs/heads/master\` beziehungsweise ersatzweise aus \`origin/refs/heads/master\`.
Abweichende Workflow-Run-, Artifact- oder Fingerprint-Referenzen
werden mit den betroffenen Quellen ausgegeben. Der Check schreibt keine Evidence;
eine veraltete Meldung wird nicht durch eine automatische Änderung historischer
Evidence-Dateien behoben.
