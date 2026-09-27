# Autonomous Resource Control Plane

Stand: 2026-09-27

Der Control Plane übernimmt wiederkehrende technische Dispatcher-Arbeit, ohne Research-Governance zu automatisieren.

Automatisiert werden: explizit CLI-freigegebene Engineering-Issues erkennen; maximal zwei freie CLI-Lanes befüllen; veröffentlichte Agent-Branches erkennen und obsolete Queue-Requests entfernen; Actions-/Queue-/Runner-Telemetrie als Artefakt sichern.

Lebenszyklus: Issue -> Control Plane -> lane0/lane1 request -> bounded Copilot CLI -> owner branch/PR -> review/merge -> stale request retirement.

Fail-closed guards:
- Ein `task_id` wird höchstens einmal pro Plan vergeben; doppelte bereits eingereihte IDs lassen den Plan fehlschlagen.
- Vor Queue-Mutationen muss der API-Lane-Snapshot mit den Request-Dateien des ausgecheckten Repository-Zustands übereinstimmen. Fehlende oder inkonsistente Queue-Daten werden nicht als freie Kapazität gewertet.
- Beim Resolve wird der Issue-Zustand erneut geprüft: Das Ziel muss offen, kein Pull Request und weiterhin mit `agent-cli-ready` markiert sein.
- `source_master_sha` wird ausschließlich aus dem explizit übergebenen `--master-sha` übernommen und gegen das SHA-Format validiert; die Python-Planung leitet keine Ref ab.

Nicht automatisiert werden Research-Hypothesen, Kandidatenauswahl, Parameter/Assets/Schwellen/Horizonte/Holdouts, Research-Gates, Promotion, Live-Ausführung oder kostenpflichtige Nutzung.

agent-cli-ready ist ausschließlich für die bounded CLI-Queue. Der Cloud-Agent-Dispatcher erhält einen separaten, expliziten cloud-agent-ready Trigger.

Der Control Plane merge't keine PRs und verändert keine Research-Evidence.