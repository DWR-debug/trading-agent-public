# Autonomous Resource Control Plane

Stand: 2026-09-27

Der Control Plane übernimmt wiederkehrende technische Dispatcher-Arbeit, ohne Research-Governance zu automatisieren.

Automatisiert werden: explizit CLI-freigegebene Engineering-Issues erkennen; maximal zwei freie CLI-Lanes befüllen; veröffentlichte Agent-Branches erkennen und obsolete Queue-Requests entfernen; Actions-/Queue-/Runner-Telemetrie als Artefakt sichern.

Lebenszyklus: Issue -> Control Plane -> lane0/lane1 request -> bounded Copilot CLI -> owner branch/PR -> review/merge -> stale request retirement.

Nicht automatisiert werden Research-Hypothesen, Kandidatenauswahl, Parameter/Assets/Schwellen/Horizonte/Holdouts, Research-Gates, Promotion, Live-Ausführung oder kostenpflichtige Nutzung.

agent-cli-ready ist ausschließlich für die bounded CLI-Queue. Der Cloud-Agent-Dispatcher erhält einen separaten, expliziten cloud-agent-ready Trigger.

Der Control Plane merge't keine PRs und verändert keine Research-Evidence.