# Präregistrierung: siebte Multi-Strategie-Komplementaritätsvalidierung

## Forschungsfrage

Zeigt die feste Kombination aus der bisher untersuchten langfristigen Trendfamilie
und der 12-1 Cross-Sectional-Momentum-Familie auf einem neuen, vollständig
symbol-disjunkten Datensatz komplementäre Risiko-/Stabilitätseigenschaften?

## Vorab definierte Konstruktionen

1. Trend-only: SMA 50/200 Long/Flat mit bestehender inverser Volatilitätsgewichtung.
2. Cross-sectional-only: 252 Handelstage Formation, 21 Handelstage Skip,
   monatliche Reallokation, Top-2, Long-only, gleichgewichtet.
3. Blend: feste 50/50-Kombination der beiden Familien.

Alle drei Varianten verwenden dasselbe 10%-Volatilitätsbudget über 63 Sessions,
dieselbe Point-in-Time-Ausführungssemantik und dieselben Kosten.

Keine Parameter-, Schwellenwert- oder Varianten-Suche.

## Siebter unabhängiger Datensatz

Trend: SLV, RSP, VYM, VIG, DVY, EPP, EWU, EWZ

Cross-sectional: AAPL, MSFT, AMZN, META, GOOGL

Alle Symbole müssen gegenüber allen bereits registrierten Universen vollständig
symbol-disjunkt sein.

Pro Asset sind exakt 3.500 gemeinsame Tages-Candles vorgeschrieben. Nach der
Point-in-Time-Konstruktion müssen exakt 3.498 Portfolio-Returns verbleiben.
Research/Holdout: 2798 / 700.

## Kosten

- Basis: 0,10 % Gebühr + 0,05 % Slippage.
- 1,5x und 2x als reine Stressszenarien.

## Auswertung

Der Lauf ist ein präregistrierter Komplementaritäts-Control, kein neues
Parameter-Optimierungsproblem.

Für jede Variante werden Research, Holdout und fünf Research-Rolling-Fenster
ausgewertet: Rendite, Maximum Drawdown, Profit Factor, durchschnittlicher
Rolling-Drawdown und Anteil positiver Fenster.

Zusätzlich werden exakt vordefinierte Paarvergleiche berichtet:

- Blend Research-DD nicht schlechter als beide Einzelvarianten;
- Blend Rolling-PF nicht schlechter als beide Einzelvarianten;
- Blend Holdout-DD nicht schlechter als beide Einzelvarianten;
- Blend Holdout-PF nicht schlechter als beide Einzelvarianten;
- positive Blend-Rendite in Research und Holdout.

Diese Paarvergleiche sind diagnostisch. Sie werden nicht benutzt, um innerhalb
dieses Datensatzes eine Variante auszuwählen.

## Sicherheitsvertrag

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Keine Produktionsänderung und keine Live-Ausführung.

Trial-ID: T-2026-09-24-011
