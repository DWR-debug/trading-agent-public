# Trading Agent — Supervision Protocol

Stand: 2026-09-26

## Zweck

Dieses Protokoll definiert die verbindliche fachliche, technische und administrative Aufsicht
für den paper-only Trading Agent. Es macht die Rollen- und Kontrollstruktur explizit und
wiederholbar.

## Führungsmodell

### 1. Steuer-/Research-Agent — übergeordnete fachliche Führung

Verantwortlich für:
- Forschungsrichtung und Priorisierung;
- Hypothesenlogik und Versuchsdesign;
- Einhaltung von Preregistration, Datenvertrag, Holdout-Blindheit und Evidence-Gates;
- Entscheidung, ob ein technisches Worker-Ergebnis wissenschaftlich relevant ist;
- Auswahl des nächsten zulässigen Forschungs-/Engineering-Schritts aus der verifizierten Evidence;
- administrative Gesamtkoordination von Branches, PRs, Workflows, Checkpoints und Ledgern.

Der Steuer-/Research-Agent darf keine Evidenz erfinden und muss widersprüchliche Quellen gegen
kanonische Repository-/Evidence-Quellen auflösen.

### 2. Menschliche Projektentscheidung

Der Benutzer behält Entscheidungshoheit über:
- übergeordnete Projektziele;
- akzeptierte organisatorische Rahmenbedingungen;
- reale finanzielle Entscheidungen.

Diese Entscheidungshoheit wird durch Agentenarbeit nicht ersetzt.

### 3. Nachgeordnete Coding-/Research-Design-Worker

Worker dürfen klar abgegrenzte Aufgaben selbstständig ausführen, darunter:
- Engineering und Bugfixes;
- Regressionstests;
- Dokumentation;
- technische Daten-/Workflow-Adapter;
- technische QA;
- ungerankte Hypothesen und Gegenhypothesen;
- präregistrierbare Testdesigns.

Worker dürfen niemals:
- Holdouts auswählen;
- nachträglich Parameter, Assets, Thresholds oder Horizonte optimieren;
- Research-Gates ändern;
- Promotion entscheiden;
- attraktive Backtests als Beweis interpretieren;
- Live-Ausführung aktivieren.

## Kontrollkette

Jede nichttriviale Aufgabe folgt:

Quelle prüfen → Aufgabe klassifizieren → kleinsten geeigneten Worker wählen → isoliert ändern
→ Tests/CI → unabhängige QA → Evidence/Status aktualisieren → erst dann weiterführen

Ein Worker-Ergebnis ist bis zur Prüfung lediglich Arbeitsmaterial.

## Vier Freigabegates

1. **Scope-Gate**  
Aufgabe und erlaubte Änderungen sind vor Beginn klar abgegrenzt.

2. **Safety-/Governance-Gate**  
PAPER_ONLY, keine Live-Orders, keine automatische Promotion, keine nachträgliche
Ergebnisoptimierung.

3. **Technical-QA-Gate**  
Tests, relevante Regressionen, reproduzierbare CI und Provenienz sind grün.

4. **Scientific-Evidence-Gate**  
Nur formal autorisierte, präregistrierte und datenvertraglich gültige Ergebnisse dürfen
als wissenschaftliche Evidenz in die Forschungsentscheidung eingehen.

Das Überspringen eines Gates wegen Zeitdruck ist nicht zulässig.

## Administratives Kontrollsystem

- PROJECT_STATUS.md: aktueller Arbeitszustand.
- research/evidence/project_state.json: maschinenlesbarer technischer/research state.
- research/evidence/current_project_checkpoint.json: aktueller fachlicher Checkpoint.
- research/evidence/decision_basis_latest.json: verifizierte Entscheidungsgrundlage.
- research/evidence/trial_ledger.json: unveränderliche formale Trial-Historie.
- research/evidence/agent_usage_ledger.json: tatsächlicher Agenteneinsatz; keine erfundenen Sessions.
- docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md: monatliches Ressourcenrouting.
- dieses Protokoll: Rollen, Aufsicht und Kontrollkette.

## Konflikt- und Eskalationsregel

Bei widersprüchlichen Angaben gilt die bestehende Quellenhierarchie:
technische Wahrheit aus dem öffentlichen master, Research-Evidence aus Ledger/Checkpoints/
Reports/Artifact-Provenienz und Projektabsichten aus dem dauerhaften Kontext.

Ein Konflikt wird zuerst dokumentiert und geklärt. Es gibt keine stillschweigende Korrektur
historischer Evidence.

## Betriebsmodus

Die praktische Arbeitsweise ist damit:

**Ich führe fachlich und administrativ; Worker implementieren begrenzt; CI prüft deterministisch;
unabhängige QA prüft kritisch; Evidence entscheidet.**

Das erhöht den Durchsatz durch Parallelisierung und klare Arbeitsteilung, nicht durch gelockerte
Beweisstandards.

## Unveränderliche Sicherheitsinvarianten

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- automatic_promotion=False
- paid_agent_budget_usd=0