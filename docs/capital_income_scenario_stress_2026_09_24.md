# Capital Income Scenario Stress — 2026-09-24

## Ziel

Der Test untersucht die Belastbarkeit des Kapital-/Entnahmepfads getrennt von
einer konkreten Trading-Strategie. Die Renditepfade sind bewusst synthetische,
vollständig vorab definierte Szenario-Kontrollen; sie sind weder Forecasts noch
historische Strategieergebnisse.

## Feste Szenarien

- Flat: 252 × 0 %
- Steady Growth: 252 × +0,04 %
- Volatile Growth: abwechselnd +0,60 % / -0,55 %
- Early Drawdown: 42 × -0,50 %, danach 210 × +0,15 %
- Late Drawdown: 210 × +0,15 %, danach 42 × -0,50 %
- Whipsaw: abwechselnd +0,40 % / -0,40 %

## Feste Entnahmepolitiken

- Full Payout: 100 % Ausschüttung, keine Kapitalisierung, keine Reserve
- Balanced Capitalization: 50 % Ausschüttung, 25 % Kapitalisierung, Rest bleibt
  Working Capital
- Protected Income: 50 % Ausschüttung, 25 EUR Reserve, keine Kapitalisierung

Alle drei Varianten sind vorab festgelegt. Es gibt keine Optimierung, kein
Ranking und keine Auswahl nach dem Ergebnis.

## Auswertung

Je Szenario und Policy werden dokumentiert:

- Gesamtentnahme
- Endkapital
- kapitalisierte Gewinne
- Anzahl von Auszahlungen/Kapitalisierungen
- Mindestkapital
- Maximum Drawdown
- Unterschiede gegenüber umgekehrter Renditereihenfolge

Die Sequence-Sensitivity ist eine deterministische Diagnose. Die Szenarien
sollen insbesondere sichtbar machen, dass gleiche Renditebausteine je nach
Reihenfolge unterschiedliche entnehmbare Pfade erzeugen können.

## Interpretation

Ein gutes Szenarioergebnis ist kein Nachweis einer künftigen Trading-Rendite.
Der Wert des Tests liegt in der Transparenz der Kapitalentnahme-Mechanik und in
der Identifikation von Sequenz-, Reserve- und Ausschüttungsrisiken, bevor reale
Strategiereturns als Einkommenspfad verwendet werden.

## Sicherheit

Der Workflow bestätigt Paper-Only. Der Test enthält keine Broker-, Order- oder
Live-Trading-Integration.
