# Micro Trading: Unabhängige Holding-Horizon-Replikation — 15m

## Zweck

PR #35 zeigte auf DOGE/LTC/LINK/AVAX, dass längere feste Haltedauern den
Turnover stark reduzieren und die Reversal-Spur auf H16 bei einem niedrigen
Kostenstress von 0,1x des Projekt-Basissatzes noch positiv sein kann.

Dieser Lauf prüft dieselbe komplette Hypothesenfamilie unverändert auf einem
neuen, vollständig symbol-disjunkten Universum. Damit wird ausdrücklich nicht
H16 nachträglich als Gewinner behandelt.

## Unverändertes Protokoll

Neue Symbole:

- DOTUSDT
- ATOMUSDT
- UNIUSDT
- NEARUSDT

Daten:

- Binance Public Klines
- 15m
- 100.000 Candles je Asset
- 80% Research / 20% Holdout
- 5 feste Research-Rolling-Fenster

Hypothesen:

- Continuation: positiver Vorbar -> Long, negativer Vorbar -> Short
- Reversal: positiver Vorbar -> Short, negativer Vorbar -> Long

Haltedauern:

- H1 = 15 Minuten
- H4 = 60 Minuten
- H16 = 240 Minuten

Exposure:

- 1x
- 2x
- 3x

Kosten:

- 0x
- 0,1x
- 0,25x
- 0,5x
- 1x

des bestehenden Projekt-Basissatzes von 0,15% je Turnover-Einheit.

## Interpretation

Der Kontrolllauf ist nur dann als bestätigende Evidenz relevant, wenn ein
Muster über das gesamte vorab festgelegte Raster hinweg und über mehrere
Research-Rolling-Fenster sichtbar bleibt.

Es wird ausdrücklich keine Auswahl des besten Horizonts, der besten Richtung
oder des besten Hebels anhand dieses Holdouts vorgenommen.

Ein positiver Befund würde zunächst nur einen noch realistischeren
Execution-Control rechtfertigen. Short bleibt ein Preisreturn-Proxy; Funding,
Borrow, Liquidation und Latenz werden nicht modelliert.

## Sicherheit

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- keine Orders
- keine Produktionsintegration
