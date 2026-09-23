# Micro Trading: Directional Short/Long + Leverage — 15m

## Warum dieser Track?

Der erste 15m-Sidecar hat BTCUSDT und ETHUSDT mit zwei einfachen Long/Flat-Hypothesen geprüft. Beide waren im Research und Holdout unter dem getesteten Kostensatz klar negativ.

Dieser zweite Track prüft deshalb die naheliegende offene Frage separat: Kann ein kurzfristiges Signal auch die **Richtung** wechseln und durch festen 1x/2x/3x-Exposure wirtschaftlich nutzbar werden?

Wichtig: Dieser Track wird nicht auf dem bereits verwendeten BTC/ETH-Holdout nachgetuned. Er verwendet eine vollständig symbol-disjunkte Binance-Spot-Stichprobe:
- SOLUSDT
- BNBUSDT
- XRPUSDT
- ADAUSDT

## Vorab feste Hypothesen

1. **Directional continuation**
   - positiver abgeschlossener 15m-Bar -> Long im nächsten Bar
   - negativer abgeschlossener 15m-Bar -> Short im nächsten Bar

2. **Directional reversal**
   - positiver abgeschlossener 15m-Bar -> Short im nächsten Bar
   - negativer abgeschlossener 15m-Bar -> Long im nächsten Bar

Je Hypothese werden ausschließlich die festen Exposure-Stufen **1x, 2x und 3x** berechnet. 3x ist die bestehende Projektobergrenze. Es gibt keine Parametersuche und keine Auswahl einer Hypothese nach dem Research.

## Ausführung

Signal:
abgeschlossener Bar -> nächster Open -> gleicher Bar-Close.

Das verhindert Lookahead aus dem getesteten Signal.

## Kostenkontrolle

Jede Kombination wird mit einer festen Kosten-Sensitivität von:
- 0.0x
- 0.5x
- 1.0x
- 2.0x
- 4.0x

des bestehenden Projekt-Basissatzes von 0,15% je Turnover-Einheit ausgewertet.

Die 0x-Kostenkontrolle ist wichtig: Sie trennt ein mögliches **Signalproblem** von einem reinen **Ausführungskostenproblem**.

## Was der Hebel hier bedeutet

Die Simulation multipliziert den 15m-Preisreturn mit einem festen Exposure von 1x/2x/3x. Das ist eine mathematische Richtungs-/Exposure-Probe, kein fertiges Margin- oder Futures-Ausführungsmodell.

Nicht modelliert werden:
- Funding
- Borrow-/Leihkosten
- Liquidationsmechanik
- Orderbuch-/Slippage-Modell
- Latenz

Ein positiver Befund wäre deshalb lediglich ein Anlass für einen weiteren, realitätsnäheren Replikationsschritt und kein Produktionskandidat.

## Sicherheitsgrenze

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- keine Orders
- keine Integration in die tägliche ETF-Strategie
- keine automatische Auswahl oder Aktivierung einer Micro-Strategie

## Literatur-Inspiration

Die Richtungshypothesen sind bewusst aus widersprüchlicher Intraday-Literatur abgeleitet und werden nicht als bewiesener Edge angenommen.

- Zarattini, Aziz & Barbon, *Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF*:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172
- Herberger, Horn & Oehler, *Are Intraday Reversal and Momentum Trading Strategies Feasible?*:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3719233
- Fetna, *Opening-Range Breakout Does Not Survive Trading Costs*:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7428398
- BIS Working Paper 1290, *The speed premium: high-frequency trading and the cost of capital*:
  https://www.bis.org/publications/working-paper-1290-speed-premium-high-frequency-trading-and-cost-capital

Der Track ist damit ein **Falsifikations- und Evidenzschritt**, nicht der Versuch, aus einem negativen Holdout nachträglich eine profitable Variante herauszuoptimieren.
