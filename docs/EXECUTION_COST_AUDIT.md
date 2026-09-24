# Execution-Kosten-Semantik-Audit — 2026-09-24

## Ergebnis

Die Research-Controls verwenden als Projektstandard:

- Fee: 10 bps je Turnover-Einheit
- Slippage: 5 bps je Turnover-Einheit
- Summe: 15 bps One-Way
- vollständiger Round Trip: 30 bps ohne Spread

Das opt-in ExecutionCostModel entspricht diesem Standard.
Der aktuelle BacktestEngine verwendet dieselben Default-Werte und ist damit
research-kompatibel.

Der aktuelle PaperBroker verwendet historisch bedingt weiterhin 5 bps Fee +
5 bps Slippage als Legacy-Default. Dieser Default bleibt bewusst unverändert.
Zusätzlich gibt es jetzt einen expliziten Opt-in-Pfad `cost_contract=ResearchExecutionCostContract()`,
der den Broker für research-kompatible Paper-Simulation auf 10 bps Fee + 5 bps
Slippage konfiguriert.

## Schutzmaßnahme

Der execution.cost_contract-Baustein:

- definiert die Research-Kosten explizit,
- prüft Research-/Backtest-Konfigurationen fail-closed,
- erkennt die Legacy-PaperBroker-Abweichung explizit,
- verändert den PaperBroker nicht rückwirkend.

Eine spätere Verwendung des PaperBroker als quantitative Research-Referenz darf
erst nach expliziter Kostenangleichung erfolgen.

## Konsequenz

Es gibt keinen rückwirkenden Einfluss auf bisherige Research-Ergebnisse. Die
bisherigen Reports bleiben mit ihren jeweils dokumentierten Kostenannahmen
reproduzierbar.

Die Entscheidung über eine künftige zentrale Kostenkonfiguration für den
PaperBroker ist eine Engineering-Entscheidung und wird separat behandelt.
