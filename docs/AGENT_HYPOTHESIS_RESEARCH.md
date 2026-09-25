# Agenten-gestützte Hypothesenforschung

## Dauerhafte Regel

**Lokale Rechenleistung für Berechnung; kostenfreie Agentenressourcen für Hypothesen.**

Kostenfreie Agentenressourcen werden dort eingesetzt, wo unabhängige Synthese, Gegenhypothesen, Mechanismusbildung oder Forschungsdesign einen echten Erkenntnisgewinn gegenüber deterministischer lokaler Berechnung liefert.

### Geeignete Aufgaben

- orthogonale Hypothesen aus eingefrorener Evidenz ableiten;
- Gegenhypothesen und Falsifikationsbedingungen formulieren;
- Marktmechanismen und Literatur-/Domänenwissen synthetisieren;
- ungewöhnliche oder widersprüchliche Ergebnisse interpretieren;
- Präregistrierungen und Testdesigns kritisch reviewen;
- aus mehreren Vorschlägen eine kleine, begründete Research-Liste bilden.

### Nicht delegieren

Agentencredits werden nicht für deterministische Aufgaben verbraucht:
- Backtests und Parameter-Sweeps
- Walk-Forward / Rolling Walk-Forward
- Datenimport und Datenqualität
- Coverage-Preflights
- Metrikberechnung und Ergebnisaggregation
- CI/pytest
- Artefaktserialisierung und Reproduktionsläufe

### Data-Snooping-Schutz

Agentenoutput ist **Ideenmaterial, keine Evidenz**.

- Kein Holdout-basierter Hypothesensieg.
- Keine rückwirkende Trial-Optimierung.
- Keine nachträgliche Parameter-/Asset-Auswahl.
- Jede formale Performancehypothese erhält eine neue Präregistrierung.
- Die numerische Prüfung bleibt deterministisch und reproduzierbar.

### Effizienz des kostenlosen Kontingents

Das Kontingent wird bevorzugt in gebündelten, diversifizierten Aufgaben eingesetzt:

1. kompakte eingefrorene Evidence-Summaries statt Rohdaten;
2. mehrere unabhängige Denk-Linsen in einem Lauf;
3. ein fixes Antwortschema je Hypothese;
4. lokale Preflights vor jeder formalen Ausführung;
5. keine Wiederholung ohne neue Evidenz oder neue Fragestellung.

### Agentenauftrag 001

Grundlage: T041/T042/T044/T045 sowie Q011.

Auftrag: mehrere orthogonale Alpha-/Informationshypothesen entwickeln, die nicht bloß weitere Varianten der bereits getesteten Risiko-, Volatilitäts-, Trendkonsistenz- oder Lifecycle-Control-Familien sind.

Jede Hypothese muss liefern:
- ID
- Mechanismus und ökonomische Intuition
- messbare Vorhersage
- erforderliche Datenquelle
- Point-in-Time-Regel
- Confounder
- Falsifikationskriterium
- Orthogonalität zu den bisherigen Trials
- minimaler deterministischer Preflight
- erwarteter Nullbefund

Vor einer möglichen Performanceprüfung folgt zwingend: Präregistrierung -> Coverage-Preflight -> unveränderte Evidence-Gates -> blinder Holdout.

### Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- automatic_promotion=False
