# Volatilitätsbudget-Control für die feste 50/50-Konvergenz

## Ausgangslage

Die feste 50/50-Kombination aus

- Cross-Asset SMA 50/200 Trend
- 12-1 Cross-Sectional Momentum Top-2

lieferte im Konvergenz-Control einen Holdout-Ertrag von rund 52,6 Prozent,
Profit Factor 1,332 und maximalen Drawdown von rund 15,1 Prozent.

Damit ist das nächste Problem nicht primär das Signal, sondern die
Risikoexposition.

## Neue Hypothese

Es wird genau eine neue Hypothese getestet:

Die bereits replizierte 50/50-Konvergenz wird mit einem festen
10-Prozent-Jahresvolatilitätsziel versehen.

Das Risikobudget darf nur reduzieren:

- kein Leverage
- keine Erhöhung über die ursprüngliche Exposition
- 63 vorherige Handelstage für die Volatilitätsschätzung
- Skalierung erfolgt point-in-time

Die 10-Prozent-Zielgröße ist literaturinformiert und wird nicht an den
bestehenden 10-Prozent-Maxdrawdown-Gate angepasst.

## Kostenmodell

- 0,10 Prozent Gebühren
- 0,05 Prozent Slippage
- zusätzlicher 2x-Kostenstress

Die Volumenskalierung selbst wird konservativ als zusätzlicher Turnover
behandelt.

## Auswertung

Verglichen werden:

1. unskalierte feste 50/50-Konvergenz
2. dieselbe Konvergenz mit 10-Prozent-Volatilitätsbudget

Daten, Signale, Sleeve-Gewichte und Ausführungslogik bleiben ansonsten
unverändert.

## Interpretation

Ein positiver Befund würde nur zeigen, dass separates Risikobudget die bereits
vorhandene Signalqualität in eine besser kontrollierbare Equity-Kurve
überführen kann.

Er wäre kein Produktionsnachweis.

Ein negativer Befund würde gegen zusätzliche Risiko-Skalierung als nächsten
Schritt sprechen.

## Sicherheitszustand

Paper-Only.
Live-Trading deaktiviert.
Keine Orders.
Keine Änderung der Research-Gates.
Keine Änderung der Signale.
