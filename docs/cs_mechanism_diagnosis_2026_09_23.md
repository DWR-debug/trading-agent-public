# Cross-Sectional-Mechanismusdiagnose — 2026-09-23

## Forschungsfrage

Die vorherige Failure-/Risk-Diagnose zeigt wiederholt, dass die Cross-Sectional-Sleeve in mehreren Research-Fenstern negativ ist. Dieser Control prüft daher die konkrete Mechanik der festen 12-1-Rangselektion, bevor irgendeine Intervention erwogen wird.

Die zentrale Unterscheidung lautet:

1. Selektionsproblem: Die gewählten Top-2 schneiden nach der Auswahl systematisch schlechter ab als ein einfacher Equal-Weight-Korb desselben fünfteiligen Universums.
2. Realisierungs-/Kostenproblem: Die Selektion ist vor Kosten weniger problematisch, während Turnover und Volatilitätssteuerung einen relevanten Teil der Portfoliobelastung erzeugen.
3. Regime-/Reversal-Muster: Die Formation-Rangfolge ist häufig positiv, aber der anschließende 21-Session-Forward-Spread der Gewinner gegen den Equal-Weight-Korb wird negativ.

## Feste Methodik

Die Diagnose verwendet ausschließlich das bereits archivierte Validation-Artifact 10740188093.

Unverändert bleiben:

- 12-1 Momentum
- 252-Session Formation
- 21-Session Skip
- 21-Session Rebalance
- Top-2 Long-only
- identisches fünf-Asset-Cross-Sectional-Universum
- identische Point-in-Time-/Open-to-Open-Semantik
- identische Volatilitätssteuerung und Kosten in der Portfolio-Rekonstruktion

Es werden keine neuen Assets gewählt und keine Parameter aus den Ergebnissen abgeleitet.

## Diagnosemetriken

Der Control misst auf Tages- und Rebalance-Ebene:

- kumulierte Rendite der gewählten Top-2
- kumulierte Rendite eines Equal-Weight-Korbs über dieselben fünf Assets
- daraus abgeleitete Selektionsdifferenz
- Anteil der Tage, an denen Top-2 den Equal-Weight-Korb übertreffen
- Anteil der Tage, an denen Top-2 die Bottom-2 übertreffen
- cross-sectionale Dispersion
- exakter Cross-Sectional-Turnover
- Rank-Turnover zwischen aufeinanderfolgenden Rebalances
- Formation-Score der Gewinner
- 21-Session Forward-Spread der gewählten Gewinner gegen Equal Weight
- 21-Session Forward-Spread der gewählten Gewinner gegen Bottom-2
- Verhältnis negativer Forward-Spreads
- Verhältnis positive Formation-Score zu negativem Forward-Spread
- Korrelation Formation-Score zu Forward-Spread
- Portfolio-Gross-vs.-Net-Cost-Drag
- Anteil des Gesamtturnovers, der rechnerisch aus der 50%-Cross-Sectional-Sleeve stammt

Die Turnover-/Kostenmetriken werden deskriptiv ausgewiesen. Es wird ausdrücklich keine eindeutige kausale Zuordnung des gesamten Portfolio-Cost-Drag zu einer Sleeve vorgenommen.

## Entscheidungslogik

Das Ergebnis ist ein Ursachenbefund und keine Intervention.

Erst wenn über unabhängige Validierungssätze hinweg ein konsistentes Mechanismusmuster repliziert wird, darf daraus eine separat vorab festgelegte Intervention als eigene Forschungsfrage entstehen.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Produktionsänderung
- keine Gate-Änderung
- keine Parameteroptimierung
