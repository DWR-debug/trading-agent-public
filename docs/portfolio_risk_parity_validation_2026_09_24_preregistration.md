# Präregistrierung: Portfolio Risk-Parity Control 2026-09-24

## Trial

Trial-ID: T-2026-09-24-022

## Forschungsfrage

Verbessert eine feste, lagged 63-Sessionen-Inverse-Volatilitäts-Allokation zwischen
den bereits etablierten Trend- und Cross-Sectional-Momentum-Sleeves die robuste
Portfolioqualität gegenüber der fixen 50/50-Referenz?

## Einzige Hypothese

Die zugrunde liegenden Signale und Sleeve-Konstruktionen bleiben unverändert:

- Cross-Asset SMA 50/200 inverse-volatility Trend-Sleeve
- 12-1 Cross-Sectional Momentum Top-2 Long-only Sleeve

Nur die Portfolioaggregation wird verändert.

Für jeden Research-Tag werden ausschließlich die letzten 63 bereits realisierten
Sleeve-Renditen verwendet. Die Sleeve-Gewichte werden proportional zum Kehrwert
ihrer realisierten Volatilität gesetzt und auf exakt 1,0x Gesamtgross-Exposure
normalisiert. Vor vollständiger 63-Session-Historie oder bei Nullvolatilität wird
fix auf 50/50 zurückgefallen.

Es gibt keine Optimierung, keine Gewichtssuche, keine Cap-Suche und keine
Holdout-Auswahl.

## Referenz und Daten

Die unveränderte 50/50-Aggregation wird auf demselben neuen, vollständig
symbol-disjunkten Datensatz als Referenz mitgeführt.

Trend-Universum:

IBM, GE, CAT, MMM, HD, LOW, UNP, NKE

Cross-Sectional-Universum:

BAC, JPM, GS, MS, C

Pro Asset werden exakt 3.500 Tages-Candles aus Yahoo Chart akquiriert und über
den bestehenden Point-in-Time-Datenpfad ausgerichtet.

Die Auswertung verwendet 3.498 Returns:

- Research: 2.798
- Holdout: 700

Holdout wird nicht zur Regel-, Gewichts- oder Asset-Entscheidung verwendet.

## Kosten

Bestehender Projekt-Kostenstandard:

- Gebühr: 0,10% je Turnover-Einheit
- Slippage: 0,05% je Turnover-Einheit

Zusätzlich feste Szenarien mit 1,5x und 2,0x diesen Kosten.

Die Portfolio-Rebalancing-Kosten der dynamischen Allokation werden zusätzlich über
die tatsächliche absolute Gewichtsänderung der beiden Sleeves erfasst.

## Vorab definierte Entscheidung

Die dynamische Allokation erhält nur dann Unterstützung, wenn alle absoluten
Projektgates erfüllt sind:

1. Research-Return > 0
2. Research-Drawdown <= 10%
3. Research-PF >= 1,10
4. mindestens 50% der fünf Research-Rolling-Fenster profitabel
5. OOS/Research >= 0,25
6. Holdout-Return > 0
7. Holdout-PF >= 1,10
8. Holdout-Drawdown <= 10%
9. 1,5x-Kostenstress Holdout >= 0
10. 2x-Kostenstress Holdout >= 0

Zusätzlich darf die dynamische Allokation gegenüber der fixen 50/50-Referenz
nicht schlechter sein bei:

- Research-Return
- Research-Drawdown
- Research-PF
- Holdout-Return
- Holdout-Drawdown
- Holdout-PF

Diese Bedingungen werden nach Sichtung des Holdouts nicht verändert.

## Literatur / methodische Inspiration

Clare, Seaton, Smith und Thomas, Journal of Behavioral and Experimental Finance
(2016), untersuchen Trend Following, Momentum und Portfolio-Konstruktion im
Multi-Asset-Kontext und diskutieren Risk Parity als Allokationsansatz.

Sullivan und Wey, Risk Parity and its Discontents (2025), berichten keine pauschale
Überlegenheit von Risk Parity gegenüber 60/40 in ihrem historischen Datensatz.

Dynamic Risk Parity Portfolio Optimization: A Comparative Study with Markowitz and
Static Risk Parity (2026) untersucht dynamische gegenüber statischen Risk-Parity-
Verfahren auf 2015-2025.

Die Literatur wird ausschließlich zur Hypothesenbildung verwendet. Die vorliegende
Analyse behauptet keine allgemeine Überlegenheit und prüft nur diesen einen festen
Portfolio-Kontrast.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
Keine Orders.
