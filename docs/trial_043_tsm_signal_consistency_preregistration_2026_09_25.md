# Präregistrierung — Trial T-2026-09-25-043
## Trend-Signal-Variabilität: Unanimous TSM Consistency

### Forschungsfrage
Kann eine einzige feste Signal-Konsistenzregel die Trend-Sleeve des eingefrorenen
50/50-Kandidaten auf einem neuen vollständig symbol-disjunkten Universum verändern,
ohne die bestehenden Risiko-, Robustheits-, Transfer- und Holdout-Verträge zu verletzen?

### Exakte Intervention
Nur das Trend-Signal wird ersetzt. Die übrige Architektur bleibt unverändert:
50/50 Trend/CS, Point-in-Time-Ausführung, inverse Volatilitätsgewichtung,
63-Session-10%-Portfolio-Volatilitätsbudget, Gebühren, Slippage und Holdout-Vertrag.

Das Trend-Signal ist long only, wenn die bis zum Entscheidungstag verfügbaren
63-, 126- und 252-Session-TSM-Renditen alle positiv sind. Sobald mindestens ein
Horizont nicht positiv ist, bleibt der Asset im Trend-Sleeve flat.

Es gibt keine Suche über Lookbacks, Konsensschwellen, Gewichte, Rebalance-Phasen
oder Kosten. Genau diese eine Regel wird auf dem neuen Datensatz geprüft.

### Validierungsuniversum
Trend: WMT, JNJ, PG, KO, PEP, XOM, CVX, CSCO
Cross-Sectional: MCD, V, ORCL, MRK, PFE

- 3.500 Daily-Candles je Symbol
- 3.498 gemeinsame Point-in-Time-Return-Perioden
- 2.798 Research / 700 blinder Holdout
- vollständig symbol-disjunkt zu allen bereits registrierten Universen

### Gates
Die bestehenden Research-Gates bleiben unverändert. Zusätzlich gilt ein
präregistrierter Nicht-Verschlechterungsvertrag gegenüber dem festen 50/50-Control:
Research Return, Research DD/PF, Rolling PF/positive-window-ratio/average-DD,
OOS/IS sowie Holdout Return/PF/DD dürfen nicht schlechter werden.

### Governance und Sicherheit
Coverage-Preflight ist zwingend vor Performanceauswertung.
Holdout wird weder zur Asset- noch Parameter- oder Hypothesenauswahl verwendet.
Keine nachträgliche Variante, keine Gate-Lockerung, keine Produktionseinbindung.

PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; orders_enabled=False;
automatic_promotion=False.
