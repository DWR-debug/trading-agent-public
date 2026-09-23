# Mechanismus-Konvergenz-Control — 2026-09-22

## Ausgangslage

Bis zu diesem Checkpoint wurden zwei voneinander getrennte Mechanismen positiv
repliziert:

1. Cross-Asset Trend Following über acht liquide ETF-Proxy-Assets
2. 12-1 Cross-Sectional Momentum auf zwei getrennten Aktienuniversen

Die beiden Mechanismen wurden jeweils ohne Parameteroptimierung getestet.

## Neue Hypothese

Die einzige neue Hypothese dieses Controls lautet:

Eine feste 50/50-Kapitalgewichtung aus

- SMA 50/200 inverse-volatility Trend-Sleeve
- 12-1 Cross-Sectional-Momentum Top-2 Long-only Sleeve

kann eine stabilere Risiko-/Return-Struktur erzeugen als jeder Sleeve allein.

Es gibt keine Optimierung der Gewichtung.

## Daten

Trend-Sleeve:
- Cross-Asset-Universum
- 8 Assets
- unabhängiges Archiv aus dem Cross-Asset-Trend-Control

Cross-Sectional-Sleeve:
- Liquid-High-Volatility-Universum
- 5 Assets
- unabhängiges Archiv aus der CS-Momentum-Replikation

Für die Konvergenz werden nur gemeinsame Return-Timestamps des tatsächlichen
überlappenden Zeitraums verwendet.

## Methodik

- jedes Sleeve verwendet seine bereits etablierte Point-in-Time-Semantik
- Close(t) Entscheidung -> Open(t+1) -> Open(t+2)
- bestehende Kosten werden je Sleeve berücksichtigt
- Gesamtportfolio = 50 Prozent Trend + 50 Prozent Cross-Sectional Momentum
- Base und 2x-Kostenstress
- 80/20 Research/Holdout auf dem gemeinsamen Zeitraum
- fünf feste Rolling-Fenster
- keine Selection
- keine Parameteroptimierung
- keine Gate-Änderung
- keine Produktionsänderung

## Interpretation

Ein positiver Konvergenzbefund würde lediglich zeigen, dass die beiden
Mechanismen auf Portfolioebene komplementär sein können.

Er wäre kein Beweis für eine produktionsreife Strategie.

Ein negativer Befund wäre ebenso wertvoll, weil er davor schützt, zwei einzeln
plausible Mechanismen nur aufgrund ihrer isolierten Ergebnisse blind zu
kombinieren.

## Sicherheitszustand

Paper-Only aktiv.
Live-Trading deaktiviert.
Keine Orders.
Keine automatische Strategieauswahl.
