> **BINDING PROJECT STATUTES:** Vor Agentenarbeit `docs/TRADING_AGENT_PROJECT_STATUTES.md` lesen. Nutzkapazitäts-Maxime: **Es darf keine künstliche Arbeit erzeugt werden. Es darf ausschließlich wertvolle und hilfreiche Rechenarbeit ausgeführt werden. Und das so viel wie möglich, kontinuierlich. Wir müssen immer besser werden.**

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
2. `docs/CURRENT_STATUS.md`
3. `research/evidence/current_operational_state.json`
4. `docs/PROJECT_CONTEXT.md`
3. `PROJECT_STATUS.md`
4. `research/evidence/project_state.json`
7. relevante Trial-/Evidence-Dateien und aktuelle Workflows
8. **Live-Ressourcen-/Kapazitäts-Preflight:** GitHub-hosted Actions, Self-hosted Research Worker,
   Copilot-CLI-Queue, Copilot-CLI-CI-Repair, Copilot Cloud Agent/Entitlement und weitere tatsächlich
   verfügbare kostenlose Compute-Pfade.
9. Für jede Ressource bewerten: verfügbar, belegt, deaktiviert, nicht zugänglich oder nicht sinnvoll.

Eine im Chat übergebene Kopie des „aktuellen Standes aus dem letzten Chat“ ist nur Handoff-Kontext. Technische und wissenschaftliche Aussagen müssen gegen die kanonischen Repository-/Evidence-Quellen geprüft werden.

Nach dem Preflight gilt für unabhängige, zulässige und sinnvolle Arbeit:
**verfügbare kostenlose Ressource => aktiv einsetzen; nicht künstlich Arbeit erzeugen; laufende Arbeit nicht duplizieren.**
Der Preflight wird nach relevanten Meilensteinen wiederholt, sobald Kapazität frei wird.

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


## Kostenfreie Ressourcen

Lies vor agentischer Arbeit docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md.

Cloud Agent nur für begrenzte, PR-fähige Engineering-, QA- und Dokumentationsaufgaben einsetzen, wenn die Funktion im Benutzerkonto bereits ohne Zusatzkosten verfügbar ist. Keine bezahlten Upgrades, keine Overages.

Deterministische Research-Berechnung bleibt auf reproduzierbaren Actions-/lokalen Workern. Holdout- und Promotionsentscheidungen bleiben außerhalb nachgeordneter Agenten.