# Trial 024 — Monthly Low-Volatility Cross-Sectional Control — 2026-09-24

## Trial-ID

T-2026-09-24-024

## Forschungsfrage

Prüft wird eine einzige, feste, long-only Cross-Sectional-Hypothese: Aktien mit
der niedrigsten realisierten historischen Volatilität erzielen im Folgemonat
eine robuste kostenbereinigte Rendite und einen positiven Low-Vol-vs-High-Vol-Edge.

Die Literatur beschreibt eine dokumentierte Low-Volatility-/Defensive-Equity-Evidenz.
Gleichzeitig weisen Arbeiten auf Grenzen durch Bewertung, Liquidität und
Transaktionskosten hin. Der Control verwendet deshalb ein vollständig disjunktes
liquides U.S.-Aktienuniversum, eine fixe 252-Sessionen-Messung und explizite
Kostenstress-Szenarien. citeturn365865search0turn365865search2turn365865search9

## Daten

Festes, vollständig symbol-disjunktes U.S.-Aktienuniversum:

INTC, QCOM, AVGO, HON, LMT, RTX, CSX, NSC

- 3.500 Candles je Asset
- 3.498 Point-in-Time-Returnperioden
- Research: 2.798
- Holdout: 700
- Timestamp-Intersection-Alignment erforderlich
- bei zu kurzer gemeinsamer Historie: fail-closed
- Yahoo historical daily data

## Präregistrierte Regel

1. An jedem Kalendermonatsübergang wird für jedes Asset die Standardabweichung
   der unmittelbar vor dem aktuellen Monat liegenden 252 abgeschlossenen
   Close-to-Close-Tagesreturns berechnet.
2. Die Messung endet mit dem letzten abgeschlossenen Handelstag des Vormonats.
   Kein Return des aktuellen Monats darf in die Auswahl eingehen.
3. Im aktuellen Monat werden die vier Assets mit der niedrigsten Volatilität
   mit jeweils 25% Long-Gewicht gehalten.
4. Die vier Assets mit der höchsten Volatilität bilden ausschließlich den
   deskriptiven High-Vol-Control für den Low-Vol-minus-High-Vol-Edge.
5. Gross Exposure: 1,0x; nur Long; keine Hebelung.
6. Umschichtung: beim Kalendermonatswechsel.
7. Realisierung: Entscheidung am Timestamp t; nächstes vollständiges
   Close-to-Close-Intervall t+1 bis t+2.
8. Kosten: 10 bps Fee + 5 bps Slippage = 15 bps One-Way.
9. Kostenstress: 1,5x und 2,0x.
10. Keine Parameter-, Threshold-, Auswahlbreiten- oder Asset-Suche.

Der 252-Sessionen-Lookback und die Vier-von-Acht-Auswahl sind vorab fest.

## Entscheidungs-Gates

Alle folgenden Gates müssen gleichzeitig erfüllt sein:

- Research Return > 0
- Research Drawdown <= 10%
- Research Profit Factor >= 1,10
- mindestens 50% profitable Research-Rolling-Fenster
- OOS/Research Return Ratio >= 0,25
- Holdout Return > 0
- Holdout Drawdown <= 10%
- Holdout Profit Factor >= 1,10
- Holdout Return bei 1,5x Kosten >= 0
- Holdout Return bei 2,0x Kosten >= 0
- Low-Vol-minus-High-Vol Edge > 0 im Research
- Low-Vol-minus-High-Vol Edge > 0 im Holdout

Es gibt keinen nachträglichen Gate-Modifikator.

## Governance und Safety

- research_only = true
- strategy_variants = 1
- selection_after_results = false
- parameter_search = false
- threshold_search = false
- holdout_selection = false
- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- orders_enabled = False

Ein positives Ergebnis führt nicht automatisch zu Produktion. Promotion ist ein
separater Governance-Schritt nach unabhängiger Evidenz und unveränderten Gates.

## Literatur

- Novy-Marx (2014), Understanding Defensive Equity, NBER Working Paper 20591.
- Li, Sullivan & García-Feijóo (2016), The Low-Volatility Anomaly.
- Li, Sullivan & García-Feijóo (2014), The Limits to Arbitrage and the
  Low-Volatility Anomaly.
