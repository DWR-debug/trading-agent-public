# CS Rank-Bucket-/Monotonie-Control — 2026-09-23

## Zweck

Dieser Control prüft, ob die feste 12-1-Rangfolge eine monotone Beziehung zwischen Formation-Rang und anschließender 21-Session-Performance erzeugt.

Alle fünf Ränge werden ausgewertet. Es wird kein Rang bevorzugt und kein Parameter aus den Ergebnissen ausgewählt.

## Fixe Methodik

- 12-1 Cross-Sectional Momentum
- 252 Sessions Formation
- 21 Sessions Skip
- 21 Sessions Rebalance
- fünf Assets je Universum
- Research-only
- Rang 1 bis Rang 5 vollständig berichtet

An jedem Rebalance wird für jeden Rang die nächste vollständige 21-Session-Open-to-Open-Performance berechnet.

## Kennzahlen

- Mittelwert und Median der Forward-Performance je Rang
- Positive-Forward-Quote je Rang
- Mittelwert der Differenz benachbarter Ränge
- Anteil der Rebalances mit nicht zunehmender Rang-Performance
- Anteil vollständig monotoner Rank-Pfade
- gepoolte Korrelation von Rangposition und Forward-Performance

Eine ideal monotone Rangwirkung würde mit steigender Rangnummer keine systematische Verbesserung der Forward-Performance zeigen. Das ist eine Diagnosebeschreibung, keine Produktionsentscheidung.

## Daten

Verwendet werden ausschließlich die bereits abgeschlossenen unabhängigen Research-Artifacts:

- erste CS-Replikation: Run 35840185031
- zweite CS-Validation: Artifact 10740188093

Holdout-Returns werden nicht verwendet.

## Sicherheits- und Forschungsregeln

- keine Parameteroptimierung
- keine Asset-Ersetzung
- keine Signaländerung
- keine Sleeve-Gewichtsänderung
- keine Gate-Änderung
- keine Produktionsänderung
- kein Rang wird als Kandidat ausgewählt
- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False