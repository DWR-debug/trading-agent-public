# Risk-Layer Forward-Horizon Profile — Pre-Registration 2026-09-24

## Forschungsfrage

Die unmittelbare Folgerenditen-Diagnose zeigte in 4/4 Validierungsfamilien
höhere unskalierte Renditen und höhere positive Raten nach aktivem De-Risking.
Diese Diagnose prüft, ob dieser Gegenbefund nur kurzfristig ist oder auch auf
längeren Horizonten anhält.

## Präregistriertes Design

Der bestehende 63-Session-/10%-Risk-Layer bleibt vollständig unverändert.
Für jede Research-Periode t wird nach dem Zustand bei t die kumulierte
**unskalierte** Netto-Rendite von t+1 bis t+h gemessen.

Feste Horizonte:

- 1 Research-Periode
- 5 Research-Perioden
- 20 Research-Perioden
- 60 Research-Perioden

Die Auswertung endet vor dem Research/Headout-Grenzpunkt. Kein Fenster darf
den Holdout überlappen.

Zustände:

- De-Risk: Scale(t) < 1
- Vollrisiko: Scale(t) = 1

Je Horizont werden Mittelwert, Median und positive Renditerate für beide
Zustände und deren Differenzen berichtet.

## Vorab definierte Interpretation

Für jeden Horizont gilt eine Beziehung als:

- günstig, wenn Mittelwert und positive Rate nach De-Risking jeweils <= dem
  Vollrisiko-Zustand liegen.
- ungünstig, wenn beide Größen nach De-Risking > dem Vollrisiko-Zustand liegen.
- gemischt/unklar in allen anderen Fällen.

Replikation wird nur beschrieben; es wird kein Parameter anhand der
Horizontergebnisse ausgewählt.

Interpretationsschwerpunkte:

- **kurzfristig advers**: ungünstige Beziehung in >=3/4 bei 1 Tag.
- **mittelfristig advers**: ungünstige Beziehung in >=3/4 bei 20 Tagen.
- **langfristig advers**: ungünstige Beziehung in >=3/4 bei 60 Tagen.
- **kurzfristige Mean-Reversion-Spur**: 1 Tag advers in >=3/4, während 20 oder
  60 Tage günstig in >=3/4 sind.

Diese Kategorien sind nur Diagnoseetiketten und keine Qualitätsrankings.

## Datenbasis

- vier vollständig symbol-disjunkte immutable Validierungsfamilien
- 2.798 Research-Returns je Familie
- nur innerhalb des Research-Bereichs ausgewertete Forward-Horizonte
- Holdout weder berichtet noch verwendet
- keine neue Datenakquisition
- keine Strategie-, Parameter-, Gewichts-, Gate- oder Produktionsänderung

## Externe Motivation

Moreira & Muir (2017) zeigen den potenziellen Nutzen von Volatility Timing,
während Cooper & Priestley (2019) explizit die Interaktion von Volatility Timing
mit Return-Mean-Reversion und Anlagehorizont untersuchen. Der vorliegende
Control übernimmt daraus ausschließlich die Fragestellung nach der
Horizontabhängigkeit; es werden keine fremden Parameter in die Strategie
übernommen.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung