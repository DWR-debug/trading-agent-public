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

Formale Research-Evidence bleibt auf den kanonischen, reproduzierbaren GitHub-hosted Pfaden. Der Self-hosted Worker liefert Arbeitsartefakte, die bei wissenschaftlicher Verwendung anschließend kanonisch reproduziert werden.

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
| Deterministische Coverage | GitHub Actions |
| Backtest/Validation | GitHub Actions / lokaler Runner |
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

Wenn ein neuer Chat mit "trading agent" beginnt, wird dieses Dokument nach dem Chat-Einstiegspunkt gelesen, bevor der nächste Arbeitsschritt gewählt wird.

Verbindliche Reihenfolge:
TRADING_AGENT_CHAT_ENTRYPOINT.md → PROJECT_CONTEXT.md → GITHUB_FREE_RESOURCE_OPERATING_MODEL.md → PROJECT_STATUS.md → project_state.json → current_project_checkpoint.json → Evidence-Ledger → aktueller GitHub-Stand.

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