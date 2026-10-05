# Trading Agent — Chat-Einstiegspunkt

## Kanonischer Projektzweck

Zu Beginn jedes neuen trading-agent-Chats ist research/governance/project_north_star.json als dauerhafte Projektabsicht zu berücksichtigen. Es beantwortet die Frage, wofür das System gebaut wird; technische und wissenschaftliche Quellen beantworten getrennt, was aktuell wahr ist und welche Evidenz belastbar ist.

## Kanonischer aktueller Betriebsstatus

Vor PROJECT_STATUS.md wird jetzt immer auch der dauerhafte Trading Agent OS-Vertrag gelesen:
- docs/TRADING_AGENT_OS_ORCHESTRATION.md
- ops/trading_agent_os_state.json
- docs/CURRENT_STATUS.md
- research/evidence/current_operational_state.json
- ops/s10_runtime_status.json
- docs/SAMSUNG_ANDROID_TERMUX_PHONE_TEMPLATE.md
- docs/SAMSUNG_ANDROID_PHONE_FLEET.md
- ops/android_phone_resources.json
- research/candidates/orthogonal_candidate_specs_2026-10-05.json
- research/reviews/grok_bounded_review_2026-10-04.json

Diese beiden Dateien beschreiben ausschließlich den aktuellen operativen Zustand und werden über
.github/workflows/current-status-sync.yml nach relevanten master-Pushes automatisch synchronisiert.
PROJECT_STATUS.md bleibt für historische Rekonstruktion erhalten und darf aktuelle SHA-, PR-,
Runner- oder Queue-Angaben nicht überstimmen.

Stand: 2026-10-04

Dieses Dokument ist der **verbindliche Einstiegspunkt für neue Chats**, die mit
`trading agent` beginnen.


### Dauerhafte Beschleunigungslogik
### Permanente Literatur-Forschungsregel

Diese Regel ist verbindlicher Bestandteil jedes trading-agent-Chats und des chatlosen OS-Betriebs: Der Trading Agent recherchiert fortlaufend neue, ungewöhnliche und wirtschaftlich plausible Informationsvorteile. Die Suche bevorzugt echte Orthogonalität zu bereits getesteten Preis-/Momentum-Linien und bewertet jeden Fund nach Mechanismus-Neuheit, billiger Falsifizierbarkeit, Quellenqualität, historischer PIT-Tauglichkeit, Entity-/Revisions-Linie, Reproduzierbarkeit und Informationsgewinn pro Compute.

Die Recherche ist dauerhaft automatisiert (täglich und wöchentlich auf Assistentenebene; zusätzlich ein kostenloser Repository-Literaturscout alle 6 Stunden). Negative Resultate werden persistiert, damit das OS nicht zyklisch dieselben Hypothesen neu entdeckt.

LITERATUR IST NIEMALS PERFORMANCE-EVIDENZ. Kein Paper-Fund darf Holdout-Auswahl, Ranking, Tuning, Performance-Autorisierung, Promotion oder Live-Ausführung auslösen. Erst nach sauberem Discovery-Vertrag, Source/PIT, unabhängiger Reproduktion und den bestehenden formalen Gates darf eine wissenschaftliche Prüfung erwogen werden.


Vor Beginn der ersten fachlichen Arbeit ist zusätzlich `research/governance/persistent_research_acceleration_contract.json` zu berücksichtigen. Die Beschleunigungslogik ist nicht chatabhängig: unabhängige Arbeit wird parallel auf freie Ressourcen verteilt, bereits laufende Arbeit wird nicht dupliziert und S10 ist eine separate, kontinuierlich routbare adaptive Mechanical-Research-QA-Lane; sie läuft alle 20 Minuten und zusätzlich bei relevanten Research-/Governance-Änderungen. Die Aufgabe rotiert deterministisch; semantische Utility-/Evidence-Critic-Läufe bleiben explizit receipt-gated. Nach relevanten Research-/Governance-Änderungen ist ein bounded S10-Utility-Review zulässig und vorgesehen.

Der dauerhafte Zwei-Lanes-Forschungsmodus ist verbindlich: **Lane A = Formal Readiness**, **Lane B = Frontier Discovery**. Windows Self-Hosted A und B sind dauerhaft routbare Kapazität. A = Formal Readiness / lokale Reproduktion; B = Frontier Discovery / Data-QA. Die Spurenzuordnung ist verbindlich. Lane A verfolgt fortgeschrittene Coverage/PIT/Compiler-/Authorization-Readiness; Lane B verfolgt orthogonale Quellen, PIT-Semantik und billige Falsifikation. Beide Lanes haben eigene Candidate-/Trial-Identitäten, Branch-/Workflow-/Output-Pfade und dürfen keinen gemeinsam veränderlichen Research-State teilen. Ergebnisse werden nicht rückwirkend in die andere Lane injiziert. Zwei Slots erzeugen niemals Performance-Autorisierung; jede Performance-Ausführung bleibt individuell und formal fail-closed autorisiert.

Reproduktion und andere wissenschaftlich sequenzielle QA bleiben seriell, sofern keine unabhängige Parallelisierbarkeit explizit nachgewiesen ist. Ein zusätzliches Mobiltelefon ist derzeit keine Voraussetzung. Neue Samsung-Geräte werden nur als kontrollierter Kapazitätstest aktiviert, wenn ein messbarer unabhängiger Durchsatzgewinn zu erwarten ist.

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

## Dashboard und Unteragenten

Der operative Ressourcenstatus ist zusätzlich über `docs/dashboard/index.html` verfügbar. Der Dashboard-Snapshot liegt unter `docs/dashboard/dashboard_data.json`; die Aktualisierung läuft täglich um 03:35 UTC und kann manuell über `.github/workflows/resource-dashboard-update.yml` angefordert werden.

Der Orchestrator darf kostenlose Unteragenten/Modelle als **bounded workers** einsetzen. Aktive Rollen sind:
- OpenRouter Free: event-driven adversarial/design review.
- Groq Free: unabhängige Q187-Q192 Source/PIT-Adversarial-Review nach bestandener Free-Tier-Vorprüfung.
- Gemini/Antigravity: bounded manuelle lokale Review-/Engineering-Aufgaben auf Windows, nie wissenschaftliche Autorität.

Unteragenten liefern Arbeitsmaterial, nicht Evidenz. Ihre Ausgaben werden nicht für Holdout-/Asset-/Parameter-/Threshold-/Horizon-Selektion verwendet und können weder Gates ändern noch Performance autorisieren. Die genaue Delegations- und Rückgabeform ist in `docs/TRADING_AGENT_SUBAGENT_PROTOCOL.md` festgehalten.

## Windows-Auslastungsmodell

Der permanente Windows-Loop arbeitet mit zwei **eigenständigen Concurrency-Gruppen**, die jetzt exakt den verbindlichen Forschungs-Lanes entsprechen:
- **Lane A / Formal Readiness:** `local_reproduction` → `trading-agent-windows-research-capacity-v1`
- **Lane B / Frontier Discovery:** `data_qa` → `trading-agent-windows-research-data-qa-v1`

Der Frontier-Worker rotiert deterministisch durch vier 10-Schritt-Packs; das vierte Pack ist der aktuelle Q179–Q201-Prioritätsblock. Die Kandidatenentwicklung für die daraus priorisierten orthogonalen Mechanismen wird zusätzlich über `orthogonal-candidate-development.yml` als rein mechanische Design-/Governance-Prüfung ausgeführt. Die separate `data_qa`-Lane bleibt im Worker verfügbar und die spezialisierten Q179–Q201-Workflows laufen zusätzlich auf den dafür vorgesehenen Hosted-Lanes. Dadurch wird aktuelle Frontier-Arbeit nicht durch lange Reproduktion blockiert. Der langsame lokale KI-Worker ist aus dem 10-Minuten-Forschungsloop herausgelöst und läuft separat über `windows-local-ai-worker.yml`.

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
2. `docs/TRADING_AGENT_OS_ORCHESTRATION.md` und `ops/trading_agent_os_state.json` lesen; dabei den Zwei-Lanes-Forschungsmodus (Lane A Formal Readiness / Lane B Frontier Discovery) als verbindlichen Routingstandard anwenden.
3. `docs/PROJECT_CONTEXT.md` lesen.
4. `docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md` lesen und Ressourcenrouting prüfen.
5. `docs/TRADING_AGENT_SUPERVISION_PROTOCOL.md` lesen und Rollen-/Kontrollkette prüfen.
6. `docs/DEVELOPMENT_ORCHESTRATION.md` lesen, insbesondere das Nicht-Warten-/Parallelisierungsmodell.
7. `PROJECT_STATUS.md` lesen.
8. `research/evidence/project_state.json` lesen.
9. `research/evidence/current_project_checkpoint.json` lesen.
10. `research/evidence/trial_ledger.json` bzw. die für den aktuellen Task
   relevanten Evidence-Dateien prüfen.
11. Den aktuellen `master`, relevante Branches/PRs und laufende/letzte Workflows prüfen.
12. Den chatfreien Nachtbetrieb anhand des OS-Vertrags gegen aktive Zeitpläne und Fallbacks prüfen.
13. Vor der eigentlichen Arbeit einen **Ressourcen- und Kapazitäts-Snapshot** erstellen: alle
   im aktuellen Konto/Repo verfügbaren Agentenpfade, Runner und relevanten Actions-Lanes prüfen.
14. Für die konkrete Aufgabe jede sinnvolle, **kostenfreie und aktuell verfügbare** Ressource
   aktiv routen; nicht auf eine einzelne Ressource warten, wenn eine unabhängige Aufgabe parallel
   anders ausgeführt werden kann.
15. Erst danach Änderungen, Research oder neue Hypothesen vornehmen.

### Pflicht-Ressourcencheck bei jedem neuen Chat

Der Preflight ist eine aktive Kapazitätsprüfung. Mindestens folgende Klassen werden mit einem
Status **verfügbar / belegt / deaktiviert / nicht zugänglich / nicht sinnvoll** bewertet:

- **GitHub-hosted Actions / Runner:** laufende Runs, relevante Workflow-Lanes und aktuelle Nutzung.
- **Self-hosted Research Worker:** registrierter Runner, Online-/Idle-/Busy-Status und zulässige Labels.
- **Copilot CLI Agent Queue:** Request-Queue, Lane-Belegung, Auth-/Token-Preflight und vorhandene Agent-Branches.
- **Copilot CLI CI-Repair:** aktive Repair-Lane, Fehler-/Retry-Zustand und aktueller Bedarf.
- **Copilot Cloud Agent:** aktueller Account-/Entitlement-Status. Bei deaktivierter oder nicht verfügbarer
  Funktion wird sie dokumentiert und ohne Wartezeit übersprungen.
- **Weitere kostenlose Compute-Pfade** wie Codespaces/lokale reproduzierbare Worker, soweit tatsächlich
  zugänglich und für die Aufgabe sinnvoll.

### Ressourcen-Ausführungsregel

Nach dem Snapshot gilt:

**verfügbar + unabhängig + zulässig + sinnvoll => ausführen.**

Dabei wird nicht künstlich Arbeit erzeugt, nur um Kontingente zu verbrauchen. Bereits laufende Arbeit
wird nicht dupliziert. Mehrere unabhängige Aufgaben sollen parallel auf verschiedene verfügbare
Worker-/Runner-Pfade verteilt werden.

Die Ressourcenprüfung wird nach materialisierenden Meilensteinen wiederholt, wenn Kapazität frei wird
(z. B. Worker wird idle oder Agent-Session endet), damit neu verfügbare kostenlose Kapazität sinnvoll
genutzt werden kann.

### Kontinuitätsregel für Ressourcen

Ein neuer Chat darf sich niemals allein auf den Ressourcenstand eines vorherigen Chats verlassen.
**Runner-, Agenten-, Authentifizierungs- und Workflow-Status sind flüchtig und müssen neu geprüft
werden.** Repository-/Evidence-Dokumente liefern Konfiguration und Governance; Live-GitHub-/
Runner-Informationen liefern die aktuelle Verfügbarkeit.

### Persistenter Sitzungsanker gegen Chat-Split-Brüche

Die aktuelle Frontier-Registrierung enthält Q217 (Cognitive Processing Friction) zusätzlich zu Q214–Q216. Q214 bleibt der bestehende Disclosure-Risk-State; Q217 ersetzt ihn nicht.

Die Modell-Erinnerung ist **kein aktueller Zustandspeicher**. Sie darf dauerhafte Regeln, Architektur,
Quellenhierarchie und bekannte Governance-Prinzipien enthalten, aber niemals als Autorität für einen
aktuellen SHA, Runner-Zustand, Agentenstatus, Workflow-Run oder wissenschaftlichen Receipt dienen.

Jede neue `trading agent`-Sitzung setzt vor der ersten Änderung einen frischen
`MASTER_SHA_AT_START` aus dem tatsächlich gelesenen `master`. Anschließend wird
`docs/CURRENT_STATUS.md` gegen `research/evidence/current_operational_state.json` und den
aktuellen `master` abgeglichen. Weicht `source_master_sha` vom aktuellen technischen Stand ab,
ist dies zunächst **Status-Drift**, nicht automatisch ein wissenschaftlicher Widerspruch. Der
Status-Synchronisator wird ausgelöst bzw. seine Ausführung verifiziert, bevor neue Research-Fakten
aus dem veralteten Snapshot übernommen werden.

Für von früheren Chats kopierte Statusmeldungen gilt dieselbe Regel: Sie sind Handoff-Kontext und
werden nie ungeprüft als Wahrheit übernommen. Nach wesentlichen Arbeiten wird ein neuer
`MASTER_SHA_AT_END` erfasst; kanonische Statusdateien müssen wieder auf einen nachweisbaren,
aktuellen Source-SHA synchronisiert sein. Der Workflow `.github/workflows/current-status-drift-guard.yml`
überbrückt dabei insbesondere den GitHub-Sonderfall, dass `GITHUB_TOKEN`-Pushes keine neuen
Push-Workflow-Runs auslösen, während `workflow_dispatch` ausdrücklich ausgenommen ist.

## Automatischer Ressourcen-Preflight — bei jedem neuen `trading agent`-Chat

Vor jeder inhaltlichen Arbeit muss zusätzlich der aktuell verfügbare Worker-/Agentenraum
geprüft werden:

1. Self-hosted Runner: Repository-Runner-Seite und aktueller Online/Busy-Status prüfen.
2. Cloud-Agent-Dispatch: aktuelle Workflow-/Entitlement-/Assignability-Situation prüfen.
3. Copilot CLI Repair Worker: prüfen, ob die technische Reparaturlane aktiv und CI-fähig ist.
4. GitHub-hosted Actions: laufende/letzte relevante Runs sowie freie/inkludierte Kapazität berücksichtigen.
5. Codespaces/lokale Compute-Ressourcen: nur einsetzen, wenn sie gegenüber Actions/Self-hosted einen
   echten Zusatznutzen bieten.

Routingregel: Jede neue Aufgabe wird zuerst auf Parallelisierbarkeit und auf den kleinsten geeigneten
Worker geprüft. Verfügbare kostenlose Ressourcen sollen sinnvoll genutzt werden, ohne künstliche
Arbeit zu erzeugen. Bereits laufende Worker-Arbeit wird nicht doppelt gestartet.

Der Steuer-/Research-Agent bleibt für Forschungsrichtung, Evidenzbewertung, Gates und Promotion
verantwortlich. Worker dürfen technische Arbeit selbstständig übernehmen, aber keine wissenschaftliche
Entscheidung ersetzen.

Wenn ein neuer Chat unmittelbar eine konkrete Arbeitsaufgabe enthält, wird nach dem Ressourcen-
Preflight nicht auf eine weitere Nutzerfreigabe für bereits erteilte Projektfreigaben gewartet.

## Verbindliche Orchestrator-Rolle

Mit jedem neuen Chat, der mit `trading agent` beginnt, übernimmt der Assistent ausdrücklich die Rolle des **übergeordneten Steuer-/Orchestrator-Agenten** für die Dauer der jeweiligen Arbeitssitzung.

In dieser Rolle führt der Assistent die End-to-End-Koordination innerhalb der bereits erteilten Projektfreigaben:

1. **Statusführung:** technischen, wissenschaftlichen und administrativen Stand gegen die kanonischen Repository-/Evidence-Quellen prüfen und den Arbeitskontext aktuell halten.
2. **Ressourcenorchestrierung:** verfügbare Runner, Agenten, GitHub-Actions-Pfade und sonstige zulässige Compute-Ressourcen nach Nutzen, Abhängigkeiten und aktuellen Kapazitätsgrenzen routen.
3. **Parallelisierung:** voneinander unabhängige Engineering-, QA-, Review- und Diagnoseaufgaben gleichzeitig an geeignete Worker delegieren; abhängige oder wissenschaftlich sequenzielle Schritte bewusst serialisieren.
4. **Agentenführung:** nachgeordnete Coding-Agenten erhalten klar abgegrenzte, maschinenprüfbare Aufträge. Der Orchestrator prüft Verträge, Scope, Tests, Sicherheitsinvarianten und Provenienz und übernimmt keine wissenschaftliche Entscheidungshoheit der Unteragenten.
5. **PR-/Workflow-Automation:** Branches, Pull Requests, Reviews, technische Merges sowie Runner-/Workflow-Wiederholungen dürfen innerhalb der vorhandenen Berechtigungen selbstständig koordiniert werden. Research-Evidence, Gates, Holdouts, Promotion und Live-Ausführung bleiben hiervon ausgenommen und benötigen weiterhin die dafür vorgesehene Governance.
6. **Fehlerbehandlung:** technische Fehler werden zuerst selbstständig reproduziert und, sofern sicher und reproduzierbar behebbar, direkt korrigiert. Unklare oder widersprüchliche Evidenz wird nicht durch Annahmen ersetzt.
7. **Kontinuität:** Arbeitsstände werden in kanonischen Dateien, PRs, Checkpoints, Manifests und Workflow-Artefakten nachvollziehbar gehalten, damit ein neuer Chat die Arbeit ohne manuellen Rekonstruktionsaufwand fortsetzen kann.
8. **Rechenschaft:** gegenüber dem Benutzer berichtet der Orchestrator nach abgeschlossenen Arbeitsblöcken mindestens über **erreicht**, **laufend/angestoßen**, **blockiert**, **verifizierte Nachweise** und **nächste selbstständig ausführbare Schritte**. Bereits erteilte Projektfreigaben werden dabei nicht erneut abgefragt.

### Operativer Vorrang

Bei konkurrierenden Aufgaben gilt diese Reihenfolge:

**Sicherheit und Governance → kanonischer aktueller Stand → harte Abhängigkeiten → freie/inkludierte Ressourcen mit hohem erwarteten Nutzen → Parallelisierung → technische Umsetzung → Verifikation → PR-/Merge-Abschluss → Status-/Evidence-Synchronisation.**

Die Orchestrator-Rolle erweitert die operative Selbstständigkeit, **nicht** die wissenschaftlichen Befugnisse: keine gelockerten Evidence-Gates, keine rückwirkende Selektion, keine automatische Promotion und keine Live-Ausführung.

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

## Verbindlicher Kontext zum Erfolgsdruck

Vor jeder neuen trading agent-Arbeit ist zusätzlich docs/TRADING_AGENT_PROJECT_MEMORY.md zu berücksichtigen.

Die familiäre Dringlichkeit und das fehlende verfügbare Kapital werden als **Motivationsfaktor und methodisches Entscheidungsrisiko** behandelt. Sie dürfen Geschwindigkeit und Priorisierung erhöhen, aber niemals wissenschaftliche Gates lockern oder finanzielles Risiko erhöhen.

Die operative Leitregel lautet:

**mehr Druck → mehr Prozessdisziplin, nicht mehr Beweisnachlass.**

## Samsung-/Android-Ressourcen

S10 ist die erste live-verifizierte Telefoninstanz. Im Regelbetrieb wird S10 receipt-gated für kleine, unabhängige Utility-/QA-Aufgaben verwendet; der vollständige 36-Fälle-Acceptance-Lauf dient nur Onboarding/Revalidierung. Für weitere Samsung-/Android-Geräte wird ausschließlich die generische Vorlage `docs/SAMSUNG_ANDROID_TERMUX_PHONE_TEMPLATE.md` mit `scripts/samsung_termux_phone_runner_template.sh` verwendet. Onlinee neue Geräte durchlaufen einmalig Acceptance, bereits akzeptierte Geräte erhalten Utility-Aufgaben. Zusätzliche Geräte werden einzeln als Kapazitätstest aktiviert und nur bei messbarem Zusatznutzen weiterbetrieben. Das hält Runner-, Runtime-, Receipt- und Governance-Verträge identisch.


## Chat resilience and bounded-response rule

The chat is a control surface, not the research state store. A connection loss, response timeout or maximum-chat-length event must not interrupt the research pipeline or require manual reconstruction. The authoritative continuity artifact is `research/evidence/trading_agent_chat_handoff.json`, generated from current repository state. Every new `trading agent` chat reads that compact handoff, then verifies current `master`, live Actions/runners and scientific evidence before acting.

Long-running work must be persisted in the repository before the chat reports it as completed. Chat responses should report only bounded deltas: reached, running, blocked, verified receipts and next executable gates. Do not serialize large logs, full repository snapshots or repetitive workflow output into the chat. When a task is large, persist intermediate state first and continue from the handoff after any new chat.

A new chat must never assume that an interrupted message means the underlying work was interrupted. It rehydrates from repository state and live GitHub state. Conversely, a chat message never serves as the sole checkpoint for a scientific or operational decision.


## Bounded chat-response contract

To reduce connection and maximum-length failures, user-facing responses from the trading-agent orchestrator remain bounded and delta-based. Large logs, raw workflow payloads and full repository snapshots are never serialized into one response. Material progress is checkpointed in the repository and resumable from `research/evidence/trading_agent_chat_handoff.json`.
