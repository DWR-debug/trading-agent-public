# Trading Agent — Chat-Einstiegspunkt

Stand: 2026-09-25

Dieses Dokument ist der **verbindliche Einstiegspunkt für neue Chats**, die mit
`trading agent` beginnen.

## Regel für den Chat-Übergang

Wenn der Benutzer in einem neuen Chat `trading agent` schreibt, ist die unmittelbar
danach bzw. anschließend vom Benutzer eingefügte Nachricht mit der Bezeichnung
**„aktueller Stand aus dem letzten Chat“** als **Handoff-Kopie der letzten
Assistant-Mitteilung** zu verstehen.

Das bedeutet:

- Die eingefügte Nachricht ist zunächst Kontext/Handoff, nicht automatisch neue
  wissenschaftliche Evidenz.
- Sie darf als Ausgangspunkt für die Kontinuitätsprüfung verwendet werden.
- Ihre Aussagen müssen gegen den aktuellen Repository-, Workflow- und Evidence-Stand
  verifiziert werden, bevor sie als technische oder wissenschaftliche Tatsache
  übernommen werden.
- **Die exakte Formulierung „aktueller Stand aus dem letzten Chat“ ist nicht erforderlich.**
  Wenn die erste substanzielle Nutzernachricht erkennbar den kopierten Inhalt einer
  vorherigen Assistant-Antwort enthält — z. B. ausführlichen Projektstatus, Commit-/Run-/Artifact-
  Referenzen, Zwischenstände, Überschriften oder typische Formulierungen einer vorherigen
  Statusmitteilung — wird sie konservativ als **möglicher Handoff** behandelt und gegen die
  kanonischen Quellen geprüft.
- Auch bei Unsicherheit gilt: lieber als möglichen Handoff prüfen als den eingefügten
  Zwischenstand ungeprüft als neue technische oder wissenschaftliche Wahrheit übernehmen.
- Bei Widersprüchen gilt die bestehende Quellenhierarchie:
  technische Wahrheit = öffentlicher `master`;
  Research-Evidenz = Ledger/Checkpoints/Workflow-Artefakte;
  Projektabsicht = `docs/PROJECT_CONTEXT.md`.

## Dauerhafte Ressourcenbeschränkung

Das Projekt verfügt aktuell über **kein verfügbares Kapital** für bezahlte externe Dienste.
Daher gilt verbindlich:

- kostenpflichtige Copilot-/Coding-Agent-Abos oder sonstige bezahlte Agentenressourcen sind **keine Option**;
- bezahlte API-Nutzung bleibt bei **0 USD**;
- Agenten-/Worker-Einsatz muss innerhalb kostenlos verfügbarer Ressourcen bzw. der vorhandenen
  GitHub-/ChatGPT-Infrastruktur organisiert werden;
- diese Beschränkung darf nicht als stillschweigend gelockerte Annahme behandelt werden.

Die Ressourcenlage beeinflusst die Architektur: kostenlose Agentencredits werden gezielt für
hochwertige Hypothesen-/Design-/Review-Arbeit eingesetzt, während deterministische Berechnung
über vorhandene kostenlose Runner bzw. lokale Ressourcen erfolgt.

## Verbindlicher Startablauf

Bei jedem neuen `trading agent`-Chat:

1. Dieses Dokument lesen.
2. `docs/PROJECT_CONTEXT.md` lesen.
3. `docs/DEVELOPMENT_ORCHESTRATION.md` lesen, insbesondere das Nicht-Warten-/Parallelisierungsmodell.
4. `PROJECT_STATUS.md` lesen.
5. `research/evidence/project_state.json` lesen.
6. `research/evidence/current_project_checkpoint.json` lesen.
7. `research/evidence/trial_ledger.json` bzw. die für den aktuellen Task
   relevanten Evidence-Dateien prüfen.
8. Aktuellen `master`, relevante Branches/PRs und laufende/letzte Workflows prüfen.
9. Erst danach Änderungen, Research oder neue Hypothesen vornehmen.

## Autonomie-Regel

Der Assistent soll innerhalb der ausdrücklich erteilten Projektfreigaben die nächsten
sinnvollen Entwicklungsschritte selbstständig durchführen. Insbesondere sollen
technische Fehler, Testfehler, Workflowfehler und Provenienzprobleme zuerst direkt
diagnostiziert und, sofern sicher behebbar, behoben werden.

Wissenschaftliche Ergebnisse werden nie durch Plausibilität ersetzt. Ein fehlerhafter
oder unvollständiger Lauf bleibt fehlerhaft bzw. unvollständig, bis seine Provenienz
und sein Ergebnis verifiziert sind.

## Sicherheitsinvariante

`PAPER_ONLY=True`
`LIVE_TRADING_ENABLED=False`
`orders_enabled=False`
`automatic_promotion=False`

Diese Invarianten dürfen durch die Chat-Kontinuitätslogik oder autonome Entwicklung
nicht gelockert werden.

## Zweck

Der Einstiegspunkt soll verhindern, dass ein neuer Chat durch eine von Benutzer
eingefügte Kopie der letzten Assistant-Antwort versehentlich einen Zwischenstand als
neue Wahrheit behandelt oder bereits bekannte Prüfungen überspringt.
