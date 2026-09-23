# Micro Trading: Holding-Horizon / Turnover Control — 15m

## Forschungsfrage

Der vorherige symbol-disjunkte Directional-Control zeigte eine vor-Kosten-positive
Reversal-Spur, die unter der verwendeten Kostenkontrolle bereits bei 0,5x des
Projekt-Basissatzes kollabierte. Der nächste vorab definierte Test untersucht daher
nicht weitere Signalparameter, sondern ausschließlich die Frage, ob eine längere,
feste Haltedauer den Turnover so weit reduziert, dass ein vorhandener Effekt
wirtschaftlich messbarer wird.

## Vorab festes Design

Universe, vollständig symbol-disjunkt zu den beiden vorherigen Micro-Controls:

- DOGEUSDT
- LTCUSDT
- LINKUSDT
- AVAXUSDT

Daten:

- Binance Public Klines
- 15-Minuten-Bars
- 100.000 Candles je Asset
- 80% Research / 20% Holdout
- 5 feste Research-Rolling-Fenster

Richtungs-Hypothesen:

1. Continuation: positiver Vorbar -> Long, negativer Vorbar -> Short.
2. Reversal: positiver Vorbar -> Short, negativer Vorbar -> Long.

Feste Holding-Horizonte:

- 1 Bar = 15 Minuten
- 4 Bars = 60 Minuten
- 16 Bars = 240 Minuten

Feste Exposure-Stufen:

- 1x
- 2x
- 3x (= bestehende Projektobergrenze)

Kosten-Stress:

- 0x
- 0,1x
- 0,25x
- 0,5x
- 1x

des bestehenden Basissatzes von 0,15% je Turnover-Einheit.

Die 0x-Stufe trennt Signalqualität von Kostenwirkung. Die festen niedrigeren
Kostenstufen zeigen zusätzlich, ob der Befund nur bei praktisch kostenfreiem
Trading existiert.

## Execution

Signal wird erst nach Abschluss des Vorbars gebildet.

Danach:

abgeschlossener Signalbar -> nächster Open -> feste H-Bar-Haltedauer ->
Ausgang am Close des letzten gehaltenen Bars.

Jeder vollständige Holding-Block enthält explizit Entry- und Exit-Turnover.
Bei einem längeren Horizont wird der Trade deshalb nicht zwischenzeitlich wegen
eines neuen Signals gedreht.

## Grenzen

Der Short-Teil ist weiterhin ein Preisreturn-Proxy auf Spot-Candles. Es ist kein
Futures-/Margin-Ausführungsmodell.

Nicht modelliert:

- Funding
- Borrow-/Leihkosten
- Liquidationsmechanik
- Orderbuch-/Slippage-Dynamik
- Latenz

Ein positiver Befund wäre daher nur ein Anlass für einen weiteren Execution-Control
und keine Produktionsfreigabe.

Es gibt keine Parametersuche und keine Auswahl zwischen Continuation und Reversal
nach Sicht auf das Research oder den Holdout.

## Literatur-Inspiration

Die Literatur dient ausschließlich zur Formulierung prüfbarer Hypothesen. Sie wird
nicht als Nachweis eines profitablen Projekt-Edges behandelt.

- Zarattini, Aziz & Barbon, *Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF*:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172
- Herberger, Horn & Oehler, *Are Intraday Reversal and Momentum Trading Strategies Feasible?*:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3719233
- Fetna, *Opening-Range Breakout Does Not Survive Trading Costs*:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7428398
- BIS Working Paper 1290, *The speed premium: high-frequency trading and the cost of capital*:
  https://www.bis.org/publications/working-paper-1290-speed-premium-high-frequency-trading-and-cost-capital

## Sicherheitsgrenze

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- keine Orders
- keine Integration in die tägliche ETF-Strategie
- kein automatisches Live-Trading
