# Market-State Recognition Contract

## Zweck

Der Agent soll später Marktbedingungen erkennen können und daraus die Auswahl
mehrerer validierter Strategien ableiten. Die Erkennung ist dabei eine eigene
Research-Hypothese und darf nicht mit einer einfachen Backtest-Heuristik als
gelöst betrachtet werden.

## Aktueller Zustand

Es existiert bewusst noch kein produktiver Regime-Klassifikator. Der sichere
`UnknownMarketStateObserver` meldet `UNKNOWN` und `validated=False`. Die
Entscheidungslogik fällt dadurch auf 100 % Cash zurück.

## Zukünftiger Vertrag

Ein validiertes State-Modell muss eine `MarketStateObservation` liefern mit:

- eindeutigem Zustands-Identifier,
- Confidence zwischen 0 und 1,
- `validated=True` erst nach eigenständiger Out-of-Sample-Evidenz,
- nachvollziehbaren Eingabemerkmalen,
- Begründung/Provenienz.

Die Confidence ist dabei eine Modellaussage und keine vom Coordinator
interpretierte Renditewahrscheinlichkeit.

## Research-Anforderung

Ein State-/Regime-Modell muss vor einer Nutzung zur dynamischen Strategieauswahl
gegen feste Kontrollen validiert werden. Dabei müssen neue, vollständig
symbol-disjunkte Daten und ein unberührter Holdout verwendet werden.

Der Test muss nicht nur die Klassifikation selbst, sondern den wirtschaftlichen
Mehrwert der darauf basierenden Allokation untersuchen:

**State-Modell + adaptive Allokation** versus **feste Strategie-Kombination**

unter identischen Kosten-, Risiko- und Kapitalregeln.

Bei Unsicherheit bleibt der Agent defensiv.