# Trial 018 — Fixed Event Risk-Off Overlay

## Fixed hypothesis

Bei einem qualifizierenden internationalen Konfliktfenster wird ein
marktneutrales, symmetrisches Risiko-Overlay aktiviert:

- SPY: -50 %
- TLT: +25 %
- GLD: +25 %

Die Bruttoexposure ist 100 %, die Nettoexposure 0 %. Ohne Event-Fenster ist die
Exposure 0 %. Das Mapping wird nicht auf den Research-Daten optimiert.

## Timing

Events werden ausschließlich aus dem Zeitraum nach dem letzten Market Close und
vor dem Ziel-Market-Open verwendet. Die Simulation hält die Exposure vom Ziel
Market Open bis zum nächsten Market Open. Damit ist der simulierte Return
tatsächlich an die verfügbare Informationszeit gekoppelt.

## Validation

2025 Q1 ist Research, 2025 Q2 ist ein zeitlich nachgelagertes Holdout.
Zusätzlich werden 2x Kosten und eine feste Verzögerung von einem Handelstag
getestet.

Kein Ergebnis dieses Trials aktiviert Produktion oder verändert bestehende
Research-Gates.