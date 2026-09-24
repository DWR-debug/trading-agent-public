# Failure-Diagnose: Trial 023 MAX-Effect — 2026-09-24

## Ergebnis

Trial 023 ist als NO_SUPPORT archiviert. Diese Diagnose verändert weder die
Präregistrierung noch die Gates und führt keine weitere MAX-Suche durch.

## Deskriptive Befunde

Der absolute Drawdown-Gateabstand beträgt:

- Research: 24,63% DD gegenüber 10% Gate → +14,63 Prozentpunkte über dem Gate
- Holdout: 16,26% DD gegenüber 10% Gate → +6,26 Prozentpunkte über dem Gate

Die OOS/Research-Return-Ratio beträgt 0,136 gegenüber dem Gate 0,25.

Die Charakteristik-Kante dreht im Holdout:

- Research Low-MAX minus High-MAX: +1,44 bps/Tag
- Holdout Low-MAX minus High-MAX: -0,41 bps/Tag
- Veränderung: rund -1,84 bps/Tag

Die Research-Rolling-Stabilität beträgt 4/5 profitable Fenster.
Der Basisturnover beträgt 154,0 Einheiten über 3.498 Returnperioden;
167 Kalendermonate hatten eine gültige Vorperioden-MAX-Selektion.

Die 1,5x- und 2x-Kostenstress-Szenarien bleiben im Holdout positiv.
Daraus folgt deskriptiv, dass der vollständige Gate-Failure nicht lediglich
als reiner Kostenerschöpfungseffekt beschrieben werden kann.

## Methodische Konsequenz

Der zentrale Failure ist mangelnde Out-of-Sample-Stabilität des festen
Charakteristiksignals plus ein weiterhin unzureichender Drawdown.

Der Holdout-Vorzeichenwechsel des MAX-Edges ist eine Eigenschaft dieses
Kontrolldatensatzes. Er wird weder als kausale Widerlegung der Literatur noch
als Beleg für eine alternative Regel interpretiert.

Es erfolgt:

- kein MAX-Lookback-Tuning
- keine Auswahlbreiten-Suche
- keine Threshold-Suche
- keine Asset-Suche
- keine Kostenanpassung
- keine Produktionsintegration

## Nächster methodischer Schritt

Eine neue Forschungsfamilie muss orthogonal zum MAX-Control sein. Die nächste
präregistrierte Hypothese sollte aus einer anderen Charakteristik stammen und
dieselben Daten-, PIT-, Kosten-, Safety- und Holdout-Governance-Gates unverändert
übernehmen.
