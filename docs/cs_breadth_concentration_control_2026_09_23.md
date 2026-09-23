# CS Breadth-/Concentration-Control — 2026-09-23

## Zweck

Dieser Control untersucht die Konzentrationsabhängigkeit der bereits fixierten Cross-Sectional-Mechanik, ohne eine neue Produktionsvariante auszuwählen.

Die Rangbildung bleibt unverändert:

- 12-1 Momentum
- 252 Sessions Formation
- 21 Sessions Skip
- 21 Sessions Rebalance

Nur die Anzahl gleichzeitig gehaltener Gewinner wird in einer vorab festgelegten diagnostischen Leiter betrachtet:

- Top-1
- Top-2
- Top-3
- Top-4
- Top-5

Top-5 entspricht bei einem fünfteiligen Universum einem Equal-Weight-Korb. Die Leiter ist vollständig vor Ergebnisbetrachtung festgelegt.

## Messgrößen

Für jedes der beiden bereits abgeschlossenen unabhängigen CS-Universen werden im Research gemessen:

- kumulierte Rendite
- Equal-Weight-Referenz
- Top-N minus Equal-Weight Selektionsdifferenz
- Maximum Drawdown
- Positive-Day-Quote
- Anteil der Tage mit Outperformance gegenüber Equal Weight
- mittlere tägliche cross-sectionale Dispersion
- 21-Session Forward-Selection-Spread
- Anteil negativer Forward-Spreads
- Rolling-Performance über fünf feste Research-Fenster

## Regeln

Dieser Control ist diagnostisch.

Es wird kein Top-N als Produktionsvariante ausgewählt. Die Daten dürfen keine Änderung an Parametern, Signalen, Asset-Universen, Sleeve-Gewichten oder Gates auslösen. Ein nachgelagerter Interventionsentwurf wäre eine separate Forschungsfrage und müsste vorab festgelegt und auf einem neuen, vollständig disjunkten Datensatz validiert werden.

## Datenintegrität

Verwendet werden ausschließlich die bereits archivierten, unabhängigen CS-Artifacts:

- erste Replikation: Run 35840185031
- zweite Validation: Artifact 10740188093

Holdout-Daten werden für die Breadth-Diagnose nicht verwendet.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Produktionsänderung
