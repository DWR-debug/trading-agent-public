# Risk-Layer Downside-Volatility — Pre-Registration 2026-09-24

## Motivation

Die vier unabhängigen Folgerenditen-Diagnosen zeigen, dass der bestehende
Total-Volatility-Risk-Layer nicht mit niedrigeren späteren Returns verbunden
ist. Dieser Befund wurde über 1, 5, 20 und 60 Tage nicht auf eine reine
Kurzfristigkeit begrenzt.

Externe Forschung von Wang & Yan (2021) untersucht deshalb Downside-Volatility
als alternative Risikometrik und berichtet stärkeres Return-Timing gegenüber
Total-Volatility. Sie definieren Downside-Volatility aus negativen Renditen
unter einer Nullschwelle.

Quelle: Wang & Yan (2021), Downside risk and the performance of volatility-
managed portfolios, Journal of Banking & Finance 131, 106198,
doi:10.1016/j.jbankfin.2021.106198.

## Präregistrierte Einzelintervention

Control:
- bestehende 63-Session-Stichprobenvolatilität

Intervention:
- gleiche 63-Session-Historie
- Downside-Volatility = sqrt(mean(r² * I[r<0])) * sqrt(252)
- feste Nullschwelle r<0
- identisches 10%-Jahresziel
- ausschließlich De-Risking, niemals Leverage

Die Intervention ist damit eine Risikometrikänderung, keine Änderung der
Signale oder der Portfolio-Gewichte.

## Unverändert

- Fixed Candidate
- SMA 50/200 Trend-Sleeve
- 12-1 Cross-Sectional-Momentum-Sleeve
- feste 50/50-Aggregation
- PIT-Semantik
- Kostenmodell
- fünf feste Research-Rolling-Fenster
- bestehende Research-Gates
- vier vollständig symbol-disjunkte Validierungsfamilien

## Ausgeschlossen

- keine Downside-Schwellenwertsuche
- keine Fenster-Suche
- keine alternative Downside-Definition
- keine Asset-Auswahl
- keine Gate-Änderung
- kein Holdout-Selection
- keine Produktionsmutation
- keine Orders

## Entscheidungsregel

Wie bei den vorherigen Risk-Layer-Interventionen ist Erfolg nur gegeben, wenn
in mindestens 3 von 4 Datensätzen:

1. Rapid-Delayed-or-Never-Rate sinkt,
2. Rapid-Onset-Active-Rate steigt,
3. Research-Drawdown nicht schlechter wird,
4. Research-Rolling-PF nicht schlechter wird.

Bei Erfüllung aller Bedingungen darf eine fünfte unabhängige Validierung mit
exakt derselben Downside-Volatility-Definition folgen.

Bei unvollständigem Timing-/Robustheitsnachweis erfolgt keine weitere
Downside-Tuning-Serie und keine Produktionseinführung.

## Datenbasis

- vier immutable Validierungsartefakte
- 2.798 Research-Returns je Familie
- 20 Research-Rolling-Fenster insgesamt
- Holdout weder berichtet noch zur Entscheidung verwendet

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False