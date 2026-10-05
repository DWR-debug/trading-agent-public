> **Dauerhafte Nutzkapazitäts-Regel:** `docs/TRADING_AGENT_PROJECT_STATUTES.md` ist verbindlich. Frei werdende sinnvolle Kapazität wird ereignisgesteuert nachbeschickt; Cron ist Recovery, nicht der primäre Kontinuitätsmechanismus.

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


## Multi-Model Worker Fabric — 2026-09-28

Die Orchestrierung wurde erweitert, damit die derzeit verfügbaren Ressourcen
gleichzeitig Fortschritt erzeugen können.

### Parallele Ebenen

Ebene A — Deterministische Rechenlast
- Python
- GitHub-hosted Research Runner
- Self-hosted PC Research Runner

Ebene B — Engineering/QA
- bounded GitHub Agent Queue
- Self-hosted QA
- Cloud-/Coding-Worker, sofern ohne Zusatzkosten verfügbar

Ebene C — Externe KI-Worker
- Gemini CLI als primärer opportunistischer Worker
- Claude CLI als optionaler Worker bei ausdrücklich kostenfreiem Zugriff

Diese Ebenen blockieren einander nicht.

### Aufgaben für externe KI-Worker

Zulässig sind ausschließlich bounded Research-Support-Aufgaben:
Hypothesengenerierung, adversarial review, Research-Design, Architektur-Review,
Testentwürfe und technische Dokumentation.

Keine externe KI darf:
- formale Performanceberechnung durchführen oder als Evidenz ausgeben;
- Holdout-/Parameter-/Asset-/Horizon-Selektion entscheiden;
- Gates, Authorizations oder Promotion verändern;
- Live-Ausführung ermöglichen.

### Betriebsprinzip

1. Steueragent zerlegt die Aufgabe in unabhängige, bounded Work Units.
2. Deterministische Jobs werden sofort an freie Rechenpfade gegeben.
3. Agent-Engineering läuft parallel in seiner eigenen Queue.
4. Externe AI-Worker erhalten unabhängige Denk-/Review-Aufträge.
5. Worker-Outputs werden als nicht-wissenschaftliches Material protokolliert.
6. Jede fachlich relevante Aussage muss anschließend durch Repository, Tests,
   deterministische Reproduktion und Evidence-Governance bestätigt werden.

### Permanente Ressourcenorchestrierung

Die aktuelle Priorität der Ausführung ist:

1. **Deterministische Forschung/QA** auf GitHub-hosted Workflows.
2. **Beide self-hosted Windows-Runner parallel** für die zwei unabhängigen
   `trading-agent-research`-Lanes.
3. **Lokale AI-Diagnostik** auf dem PC erst nach Abschluss der beiden
   Forschungs-Lanes, damit sie keinen Forschungs-Slot verdrängt.
4. **Copilot** ab **2026-10-01T00:00:00Z** als geschützte, einzelne
   Engineering-Session-Lane; maximal 30 AI-Credits pro reservierter Session,
   vier Reservierungen pro Monat und keinerlei Overages.
5. **Gemini/Claude** opportunistisch, wenn die kostenlose Authentifizierung
   tatsächlich verfügbar ist.

Jede Ressource bleibt optional und fail-closed: fehlt eine Voraussetzung, wird
nicht kostenpflichtig ausgewichen. Neue Arbeit wird nur erzeugt, wenn sie einen
unabhängigen verwertbaren Fortschritt erwarten lässt.

### Fail-closed

Die AI-Worker-Fabric verweigert einen Provider-Lauf, wenn Free-only-Zugriff,
Authentifizierung oder Task-Sicherheitsvertrag fehlen. Es gibt keinen automatischen
paid fallback.

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False

Für bounded Agent-Publikationen ist `automation.agent_dispatch.validate_scope_paths`
die gemeinsame Allowlist-Prüfung. Sie validiert die normalisierten Vertragspfade
und jede Änderung aus Index, Worktree und nicht ignorierten untracked Dateien;
Workflow-YAML darf diese Regeln nicht abweichend nachbilden. Der Scope-Guard
wird vor dem Staging sowie nach `git add -A` ausgeführt. Eine legacy Workflow-
Integration, die noch inline prüft, ist im Agent Dispatch Operating Model als
bekanntes, separat zu behebendes Drift-Risiko dokumentiert.
