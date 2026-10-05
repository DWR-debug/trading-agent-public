> **Kapazitätsstatut:** `docs/TRADING_AGENT_PROJECT_STATUTES.md` ist verbindlich. Kostenfreie Ressourcen werden maximal sinnvoll eingesetzt; künstliche Arbeit, künstliche Laufzeitverlängerung und Duplikation sind verboten.

# GitHub Free Resource Operating Model — Trading Agent

Stand: 2026-09-26

## Zweck

Dieses Dokument ist die verbindliche monatliche Ressourcenstrategie für das Projekt.
Grundsatz: Nicht Ressourcenverbrauch maximieren, sondern Forschungsdurchsatz pro kostenloser Ressource maximieren.
Paid agent/API budget bleibt 0 USD. Keine automatische Aktivierung kostenpflichtiger Nutzung.

## Verifizierte aktuelle GitHub-Ressourcen

Der vom Benutzer am 2026-09-26 bereitgestellte Account-Stand enthält:

| Ressource | Inklusive Menge | Projektstrategie |
|---|---:|---|
| GitHub Actions | 2.000 min | Public-Repo-Standardrunner bevorzugen; nicht künstlich verbrauchen |
| Actions/Packages Storage | 0,5 GB | Nur kleine Evidence-Artefakte |
| Git LFS | 10 GB Storage + 10 GB Bandwidth | Nur bewusst versionierte, große und wiederverwendete Datensätze |
| Packages | 1 GB Transfer + 0,5 GB Storage | Standardmäßig nicht benötigen |
| Codespaces | 120 Core-hours | Interaktives Engineering, Daten-QA, Reproduktion |
| Codespaces Storage | 15 GB-month | Möglichst wenige aktive Codespaces, alte löschen |

Die Kontingente werden nicht durch künstliche Arbeit ausgeschöpft. Ziel ist verwertbarer Forschungs- und Engineering-Fortschritt.

## Actions

GitHub dokumentiert Standard-GitHub-hosted-Runner in öffentlichen Repositories als kostenlos. Für DWR-debug/trading-agent-public ist daher der öffentliche Standardrunner der bevorzugte Pfad für CI, Coverage, Preflight und deterministische Research-Workflows.

Die 2.000 inkludierten Actions-Minuten sind für diesen öffentlichen Projektpfad nicht der primäre Engpass. Wir optimieren trotzdem auf kurze, reproduzierbare Jobs und vermeiden doppelte oder sinnlose Läufe.

## Codespaces

120 Core-hours entsprechen bei 1 Core 120 Stunden Laufzeit, bei 2 Cores 60 Stunden und bei 4 Cores 30 Stunden.

Default: 1–2 Cores, kurze Sessions, nach Gebrauch stoppen und nicht benötigte Codespaces löschen.

Monatliche Soft-Allokation:
- 50 Core-hours interaktives Engineering/Debugging
- 25 Core-hours Daten-/Provenance-QA
- 25 Core-hours Research-Tooling und lokale Reproduktion
- 10 Core-hours Agent-/Workflow-Integration
- 10 Core-hours Notfallreserve

## Self-hosted Research Worker

Der Self-hosted Worker mit dem Label `trading-agent-research` ergänzt die kostenlosen GitHub-hosted Runner. Er übernimmt ausschließlich owner-gesteuerte QA-, Reproduktions- und vorbereitende Rechenlast. Er führt keinen untrusted Fork-/PR-Code aus, besitzt keine Trading-Secrets und darf keine Promotion oder Live-Ausführung auslösen.

Formale Research-Evidence bleibt auf kanonisch reproduzierbaren Pfaden. Für Q067 darf der ausdrücklich vertrauenswürdige owner-eigene Self-hosted Windows-Runner als formaler Ausführungspfad verwendet werden, wenn Snapshot, Commit, Safety, Preregistration, PIT/Prerequisites und Evidence-Gates vollständig maschinengeprüft sind. Untrusted Forks und beliebige Shell-Aufgaben bleiben ausgeschlossen.

Einrichtungsdokument: `docs/SELF_HOSTED_RESEARCH_RUNNER.md`.

## Copilot Cloud Agent — konkrete Eignung

Der Cloud Agent kann Repository-Recherche, Implementierungspläne, Bugfixes, inkrementelle Features, Testverbesserungen, Dokumentation, Technical-Debt-Arbeit und Merge-Conflict-Auflösung übernehmen. Er arbeitet in einer eigenen GitHub-Actions-basierten Umgebung und kann Änderungen auf einem Branch sowie Pull Requests erzeugen.

Für unsere tägliche Arbeit besonders geeignet:
- CI-/Testfehler analysieren und beheben
- Regressionstests ergänzen
- klar abgegrenzte Refactorings
- Daten-/Workflow-Adapter implementieren
- Evidence-/Status-Dokumentation synchronisieren
- technische Schulden abbauen
- kleine, präregistrierte Research-Runner implementieren
- fehlgeschlagene Actions-Läufe technisch diagnostizieren
- PR-Diffs technisch prüfen

Nicht delegieren:
- finale Forschungsentscheidung
- Holdout-Auswahl
- rückwirkende Parameter-/Asset-/Threshold-/Horizon-Selektion
- Änderung der Research-Gates
- Interpretation attraktiver Backtests als Beweis
- Live-Trading oder Echtgeld-Promotion
- große Batch-Backtests, die nicht in eine kurze Agentensession passen

## Cloud-Agent-Grenzen

GitHub dokumentiert derzeit eine harte Maximaldauer von 59 Minuten pro Cloud-Agent-Session. Ein Task arbeitet auf einem Branch und erzeugt höchstens einen Pull Request. Mehrere Sessions können parallel laufen.

Projektstandard:
- Zielumfang je Session: 15–45 Minuten
- genau eine abgegrenzte Aufgabe je Session
- komplexe Arbeit in PR-fähige Teilaufgaben zerlegen
- standardmäßig höchstens 2 parallele Cloud-Agent-Sessions
- dritte Session nur bei klarer Unabhängigkeit und hohem erwarteten Nutzen

## Copilot Free versus Cloud Agent

Der aktuelle GitHub-Planstand weist Cloud Agent nicht als Bestandteil von Copilot Free aus. Cloud Agent ist auf bezahlten Copilot-Plänen enthalten.

Projektregel: Kein Kauf, kein Upgrade nur für dieses Projekt und keine Overages. Cloud Agent darf nur verwendet werden, wenn dein Account ihn bereits ohne Zusatzkosten freischaltet, etwa durch einen bereits vorhandenen kostenlosen Anspruch.

AI Credits werden monatlich zurückgesetzt und nicht übertragen. Bei 100 Prozent Verbrauch wird der Cloud Agent für den betreffenden Monat nicht weiter eingesetzt.

## AI-Credit-Soft-Allokation

Falls Cloud Agent ohne Zusatzkosten verfügbar ist:

| Bereich | Soft-Anteil |
|---|---:|
| Engineering / Bugfix / Test | 50 % |
| QA / Governance / Review | 25 % |
| Research-Design / Gegenhypothesen | 15 % |
| Reserve für Blocker | 10 % |

Ab 80 Prozent Verbrauch nur noch hochwirksame Aufgaben; ab 100 Prozent Stop für den Monat.

## Task-Routing

| Aufgabe | Primäres Werkzeug |
|---|---|
| Strategie-/Grundsatzentscheidung | Steuer-/Research-Agent + menschliche Entscheidung |
| Hypothesen/Alternativen | Steuer-Agent, optional Cloud Agent |
| Bounded Coding | Cloud Agent |
| Regression/QA | Cloud Agent + CI |
| Deterministische Coverage | GitHub Actions; bei dokumentierter Hosted-Runner-Störung vertrauenswürdiger Self-hosted Runner |
| Backtest/Validation | GitHub Actions / vertrauenswürdiger Self-hosted Runner |
| Interaktives Debugging | Codespaces |
| Evidence-Archivierung | Repository + Actions Artifacts |
| Holdout-/Promotion-Entscheidungen | formale Research-Governance |

## Monatszyklus

Letzte 3–5 Tage des Monats: Nutzung dokumentieren, Fehlerklassen identifizieren, alte Codespaces löschen, Evidence-Artefakte prüfen.

Tag 1 des neuen Monats: Quoten/Berechtigungen neu prüfen, Soft-Allokation zurücksetzen, neue Agentenaufgaben aus der aktuellen Research Queue priorisieren.

Während des Monats: zuerst Blocker und wiederkehrende Engineering-Arbeit delegieren; deterministische Forschung auf reproduzierbaren Workern; Reserve für CI/Governance-Probleme erhalten.

## Metriken

- Agent-Sessions → verwertbare PRs
- PRs → grüne CI
- Zeit bis CI green
- Actions-Laufzeit pro Evidence-Pack
- Codespace-Core-hours pro gelöstem Engineering-Problem
- Storage pro Evidence-Pack

Zielgröße: Evidence-/Engineering-Fortschritt pro kostenloser Ressource.

## Neue-Chat-Regel

Wenn ein neuer Chat mit "trading agent" beginnt, wird dieses Dokument nach dem Chat-Einstiegspunkt gelesen und durch einen **Live-Ressourcen-Preflight** ergänzt, bevor der nächste Arbeitsschritt gewählt wird.

Verbindliche Reihenfolge:
TRADING_AGENT_CHAT_ENTRYPOINT.md → PROJECT_CONTEXT.md → GITHUB_FREE_RESOURCE_OPERATING_MODEL.md → PROJECT_STATUS.md → project_state.json → current_project_checkpoint.json → Evidence-Ledger → aktueller GitHub-Stand → Live-Ressourcen-/Runner-Snapshot.

Der Live-Snapshot prüft mindestens GitHub-hosted Actions, Self-hosted Research Worker, Copilot-CLI-Queue,
Copilot-CLI-CI-Repair, Copilot Cloud Agent/Entitlement sowie tatsächlich zugängliche kostenlose Compute-
Pfade. Für jede laufende oder verfügbare Ressource wird geprüft, ob die aktuelle Aufgabe parallelisiert
werden kann. **Verfügbar + unabhängig + zulässig + sinnvoll wird ohne zusätzliche Nutzerfreigabe eingesetzt.**
Die Prüfung wird nach dem Abschluss größerer Arbeitsblöcke wiederholt, damit neu frei gewordene kostenlose
Kapazität nicht ungenutzt bleibt.

Kontingente werden nicht durch künstliche Arbeit verbraucht. Parallelisierung dient ausschließlich dem
verwertbaren Forschungs- und Engineering-Durchsatz.

## Sicherheitsinvarianten

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- automatic_promotion=False
- paid_agent_budget_usd=0

## Quellen

https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent
https://docs.github.com/en/copilot/get-started/plans
https://docs.github.com/en/copilot/concepts/billing-and-usage/individuals/billing
https://docs.github.com/en/billing/concepts/product-billing/github-actions
https://docs.github.com/en/billing/concepts/product-billing/github-codespaces

## Bounded Copilot CLI CI Repair

Für owner-eigene PRs gibt es einen separaten Copilot-CLI-Worker, der einen fehlgeschlagenen
CI-Lauf einmalig technisch reparieren kann. GitHub dokumentiert Copilot CLI für GitHub
Actions; für persönliche Repositorys kann die CLI über ein Repository-Secret
\`COPILOT_GITHUB_TOKEN\` mit einem Benutzer-Token authentifiziert werden.

Der Worker ist bewusst enger begrenzt als ein allgemeiner Coding-Agent: keine Fork-PRs,
keine Network-/URL-Tools, kein \`git push\` durch Copilot selbst und maximal 60 AI-Credits
sowie zwei Autopilot-Fortsetzungen. Der Workflow führt nach der Agentensitzung
\`git diff --check\` und die vollständige Testsuite aus und pusht nur bei grünem Test-Gate.

Ein automatisch erzeugter Commit \`FIX: autonomous CI repair\` verhindert einen
Reparatur-Endloszyklus. Ein zweiter Fehler wird an die übergeordnete Steuer-/Research-Ebene
eskaliert.

Die Reparatur darf keine Research-Evidence, Präregistrierungen, Authorisierungen, Gates,
Holdout-Logik, Strategieparameter, Promotion oder Live-Trading verändern.


## Multi-Model AI Worker Fabric — 2026-09-28

Zusätzlich zu PC, GitHub Actions, bounded Agents und Python wird ein separater
kostenfreier AI-Worker-Pool betrieben.

### Grundsatz

Die Ressourcenklassen werden parallelisiert, nicht unnötig serialisiert:

- Self-hosted PC: lokale QA, Reproduktion und freigegebene Research-Ausführung.
- GitHub-hosted Runner: CI, deterministische Research-Läufe und bounded Agent Queue.
- Python: kanonische numerische/statistische Berechnung und Evidence-Erzeugung.
- Externe AI-Worker: Hypothesen, Gegenhypothesen, Research-Design, Review und
  technische Analyse.

### Gemini

Gemini CLI ist als primärer externer Worker vorgesehen. Der offizielle CLI-Modus
unterstützt headless Prompt-Ausführung und JSON-Ausgabe; die Gemini Developer API
bietet eine Free Tier für ausgewählte Modelle.

Die Nutzung bleibt an den projektspezifischen Free-only-Preflight gebunden. Ein
vorhandener Schlüssel allein aktiviert keinen externen Worker.

### Claude

Claude CLI ist als sekundärer, opportunistischer Worker integriert. Es wird
ausschließlich bereits vorhandener, ausdrücklich kostenfrei bestätigter Zugriff
akzeptiert. Anthropic API-Nutzung wird nicht aus dem Paid-Zero-Budget automatisch
aktiviert.

### Router und Nachweis

Die Implementierung befindet sich in:
- automation/ai_worker_fabric.py
- .github/workflows/ai-worker-fabric.yml
- tests/test_ai_worker_fabric.py
- docs/AI_WORKER_FABRIC.md

Jeder Lauf schreibt einen strukturierten Worker-Receipt. Die Datei enthält
Provider, Task-Fingerprint, Preflight, Status und den unveränderlichen Hinweis,
dass Worker-Output keine wissenschaftliche Evidenz ist.

### Ressourcenverteilung

Die bestehende Copilot-/Agent-Queue bleibt unabhängig. Die AI-Worker-Lanes laufen
auf GitHub-hosted Runnern und blockieren den Self-hosted PC nicht.

Die bevorzugte Reihenfolge bei freier Kapazität lautet:

deterministische Arbeit zuerst, dann unabhängige QA/Review, dann freie externe AI-Exploration.

Bei Nichtverfügbarkeit eines Providers wird ohne Kosten-Fallback weitergearbeitet.

### Verbindliche Kostenregel

Paid agent/API budget = 0 USD.

Kein Workflow darf automatisch eine kostenpflichtige API, ein Upgrade, Overages oder
einen bezahlten Agenten aktivieren. Jeder externe Provider besitzt einen separaten
Free-Mode-Gate und fail-closed Verhalten.

## Copilot — geschützte Monatsreserve ab 2026-10-01

Für dieses Projekt beginnt die geschützte Copilot-Reserve am **2026-10-01T00:00:00Z**.
Der Orchestrator prüft ab diesem Zeitpunkt die tatsächliche Account-/Repository-
Verfügbarkeit, bevor eine Session verbraucht wird. Eine geplante Projektreserve
ist nicht gleichbedeutend mit einer verifizierten Copilot-Entitlement oder einem
kostenlosen Kontingent.

GitHub dokumentiert ein monatliches AI-Credit-Kontingent auch für Copilot Free;
die inkludierten Kontingente werden am ersten Tag jedes Monats um 00:00 UTC
zurückgesetzt. Komplexe agentische Aufgaben können deutlich mehr Verbrauch
verursachen als einfache Interaktionen.

Für dieses Projekt wird deshalb bewusst nicht das komplette Free-Kontingent
automatisch ausgenutzt.

Interne Schutzkappe:
- Startfenster: 2026-10-01T00:00:00Z
- 4 Session-Reservierungen pro Monat
- 30 AI credits maximale Agent-Session
- 1 parallele Copilot-Queue-Lane
- keine zusätzlichen Käufe und keine Overages

Diese Werte sind eine konservative Projektreserve und nicht die Behauptung,
dass Copilot Free exakt 48 AI credits pro Monat enthält.

Copilot wird nur für hochwirksame, klar abgegrenzte Engineering-/QA-/Review-
Aufgaben eingesetzt. Große explorative Aufgaben gehen stattdessen an
Gemini/Claude, Self-hosted oder deterministische Pfade, sofern diese kostenlos
verfügbar sind.
## Live re-validation — 2026-09-30

### Public GitHub-hosted runner capacity

`DWR-debug/trading-agent-public` ist öffentlich. GitHub dokumentiert für öffentliche Repositorys die Standard-GitHub-hosted Runner als kostenlos und unbegrenzt nutzbar; der separate GitHub-Free-Minutenwert von 2.000 betrifft den allgemeinen Plan-/Privat-Repo-Kontext und ist **nicht** der Engpass für Standard-Hosted-Jobs dieses öffentlichen Repositorys.

Für die aktuelle Plattform sind unter anderem verfügbar:

- `ubuntu-24.04` / `ubuntu-22.04` / `ubuntu-26.04`: 4 CPU, 16 GB RAM, x64.
- `ubuntu-24.04-arm` / `ubuntu-22.04-arm` / `ubuntu-26.04-arm`: 4 CPU, 16 GB RAM, ARM64.
- `windows-2025` / `windows-2022`: 4 CPU, 16 GB RAM, x64.
- Standard-Hosted-Jobs auf öffentlichen Repositories sind kostenlos; die normale Hosted-Job-Konkurrenz liegt im GitHub-Free-Plan bei bis zu 20 gleichzeitigen Jobs.

### Tatsächlicher Projektcheck

Am 2026-09-30 liefen auf dem aktuellen öffentlichen `master` erfolgreiche Hosted-Jobs:

- `CI` Run `36757300045`: `ubuntu-24.04` **SUCCESS** und `ubuntu-24.04-arm` **SUCCESS**.
- `T052 Exact Master CI Gate` Run `36757299960`: **SUCCESS**.
- `Free AI Worker Fabric` Run `36757408780`: Hosted-Matrix wurde tatsächlich gestartet; OpenRouter-Free/Unusual-Frontier **SUCCESS**, Gemini-Lanes providerseitig fehlgeschlagen, Claude-Lanes erfolgreich beendet. Das sind Providerzustände, kein Hosted-Runner-Ausfall.
- `Permanent Self-Hosted Research Loop` Run `36757444326`: `local_reproduction` und `autonomous_frontier_qa` **SUCCESS**.

Die frühere Zero-Job-/Queue-Anomalie ist damit **nicht als aktueller Hosted-Runner-Blocker bestätigt**. Neue Läufe werden weiterhin gegen den Live-Zustand geprüft, da GitHub Limits und Infrastrukturzustände sich ändern können.

### Verbindliches Routing

Hosted-Runner sind ab 2026-09-30 **Primärpfad**, nicht bloß Fallback:

1. Hosted x64: CI, Governance, deterministische Reproduktion und formale Gegenprüfungen.
2. Hosted ARM64: unabhängige Architektur-/Reproduzierbarkeitsprüfung und orthogonale Regression.
3. Self-hosted Windows: lokale Reproduktion, Frontier-Feasibility, trusted QA und lokale AI-Pfade.
4. Kostenfreie externe AI: Design, adversarial Review und Hypothesen; kein wissenschaftlicher Evidence-Status.

Die Parallelität soll echte Unabhängigkeit erhöhen; `concurrency`-Gruppen und Latest-Run-Wins werden nur dort verwendet, wo alte Läufe wissenschaftlich/operativ nicht mehr wertvoll sind.

## Self-hosted Failover — 2026-09-30

Self-hosted Windows ist kein Single Point of Failure. Der Workflow
.github/workflows/hosted-research-failover.yml prüft im 30-Minuten-Takt den Heartbeat
des permanenten Self-hosted Research Loop und startet bei stale/unverfügbarem Signal
automatisch bounded Hosted-Arbeit.

Failover-Schwellen:
- queued/pending Self-hosted-Lauf länger als 25 Minuten;
- letzter Self-hosted-Lauf älter als 45 Minuten;
- überhaupt kein Self-hosted-Heartbeat.

Bei Failover läuft ausschließlich die Governance-/Reproduktionsspur auf `ubuntu-24.04-arm`; die dauerhafte Frontier-QA ist separat auf `ubuntu-24.04` verankert und darf durch Failover nicht dupliziert werden.

Der Failover darf keine formale Performance-Evidence erzeugen, keine Research-Gates
ändern, keine Kandidaten-/Holdout-Selektion vornehmen und keine kostenpflichtige
Ressource aktivieren.

Der offene Chat ist für Aktivierung und Beendigung nicht erforderlich. Sobald der
Self-hosted Heartbeat wieder frisch ist, unterdrückt der Guard den Fallback.

Technische Umsetzung:
- automation/hosted_fallback_guard.py
- automation/hosted_fallback_worker.py
- tests/test_hosted_fallback_guard.py
- docs/RESOURCE_FAILOVER_MODEL.md