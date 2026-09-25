# Trading Agent — Agentenvertrag

Dieses Repository ist die technische Referenz für den paper-only Trading Agent.

## Hierarchie

- Der übergeordnete Steuer-/Research-Agent koordiniert Ziele, Research-Governance und Freigaben.
- Coding-Agenten arbeiten als nachgeordnete Implementierungs-Worker auf eigenen Branches und liefern Pull Requests.
- Deterministische Berechnung läuft in GitHub Actions bzw. lokalen reproduzierbaren Runnern.
- Kein nachgeordneter Agent besitzt Entscheidungshoheit über Research-Freigaben oder Promotion.

## Verbindliche Startprüfung

Vor jeder Aufgabe:

1. `docs/TRADING_AGENT_CHAT_ENTRYPOINT.md`
2. `docs/PROJECT_CONTEXT.md`
3. `PROJECT_STATUS.md`
4. `research/evidence/project_state.json`
5. relevante Trial-/Evidence-Dateien und aktuelle Workflows

Eine im Chat übergebene Kopie des „aktuellen Standes aus dem letzten Chat“ ist nur Handoff-Kontext. Technische und wissenschaftliche Aussagen müssen gegen die kanonischen Repository-/Evidence-Quellen geprüft werden.

## Sicherheitsinvarianten

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `orders_enabled=False`
- `automatic_promotion=False`

Diese Werte dürfen durch Agentenarbeit nicht gelockert werden.

## Engineering-Regeln

- Kleine, isolierte Änderungen; bevorzugt ein zusammenhängender PR pro Aufgabe.
- Tests vor Abschluss ausführen und relevante Regressionen ergänzen.
- Research-Code darf keine nachträgliche Parameter-, Asset-, Threshold- oder Holdout-Selektion einführen.
- Keine wissenschaftliche Behauptung aus Agentenoutput allein.
- Workflow-/Artifact-Provenienz erhalten.
- Technische Fehler zuerst deterministisch reproduzieren, dann beheben.
- Bei Unsicherheit nicht raten; den Konflikt dokumentieren und gegen die kanonische Quelle auflösen.
