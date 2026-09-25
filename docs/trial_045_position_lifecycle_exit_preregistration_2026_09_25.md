# Präregistrierung — Trial T-2026-09-25-045
## Position-Lifecycle / ATR-Trailing-Exit

### Forschungsfrage
Kann eine einzige feste Lifecycle-Regel die bestehende 50/50-Architektur robust
verbessern, ohne die Rendite-, Risiko-, Rolling-, Transfer- und Holdout-Verträge
gegenüber dem unveränderten Fixed Control zu verschlechtern?

### Exakte Intervention
Nur der Position-Lifecycle der Trend-Sleeve wird verändert. Das bestehende
SMA-50/200-Signal, die 12-1-Cross-Sectional-Sleeve, die inverse Volatilitätsgewichtung,
das 10%-Portfolio-Volatilitätsbudget, Gebühren, Slippage und Point-in-Time-Vertrag
bleiben unverändert.

Für eine Trendposition wird ein Trailing-Exit bei

**höchster Schlusskurs seit Einstieg − 3 × ATR(20)**

ausgelöst. ATR(20) ist der einfache Mittelwert der True Ranges der letzten 20
Sessions und verwendet jeweils den vorherigen Schlusskurs. Die Entscheidung fällt
am Schlusskurs; die Umsetzung folgt dem bestehenden verzögerten Point-in-Time-
Ausführungsvertrag.

Nach einem Stop bleibt das Asset bis zum nächsten monatlichen Baseline-Rebalance
flat. Liegt dort weiterhin eine positive Baseline-Allokation vor, erfolgt eine
neue Position mit Reset des Trailing-Highs. Die übrigen Trendgewichte werden nach
einem Exit nicht hochskaliert.

### Validierungsuniversum
Trend: WFC, DUK, AXP, BLK, DHR, INTU, MAR, COP
Cross-Sectional: SO, NEE, AMGN, BSX, CMCSA

- 13 vollständig symbol-disjunkte Assets
- 3.520 angeforderte Roh-Candles je Asset
- Ziel: 3.500 gemeinsame Candles
- 2.798 Research / 700 blinder Holdout
- 5 feste Rolling-Fenster

### Governance
Es gibt genau **einen** Challenger. Keine Suche über ATR-Fenster, ATR-Multiplikator,
Rebalance-Zeitpunkt, Exit-Schwellen, Gewichtscaps oder Parameter. Der Holdout wird
nicht zur Auswahl verwendet.

Ablauf:
Coverage-Preflight -> eingefrorener Coverage-Snapshot -> formale Research-Auswertung
-> blinder Holdout -> 1,5x-/2x-Kostenstress -> Evidence-Gates -> Archivierung.

PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; orders_enabled=False;
automatic_promotion=False.
