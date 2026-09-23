# Micro Trading / Intraday Sidecar — 15m

## Zweck

Separater Paper-Only-Forschungszweig für kurzfristige Intraday-Signale.
Er verändert den validierten täglichen ETF-Kandidaten nicht.

## Vorab definierte Hypothesen

1. Continuation: Long im nächsten 15-Minuten-Bar, wenn der abgeschlossene
   vorherige Bar eine positive Close-to-Close-Rendite hatte.
2. Reversal: Long im nächsten 15-Minuten-Bar, wenn der abgeschlossene vorherige
   Bar eine negative Close-to-Close-Rendite hatte.
3. Benchmark: Gleichgewichtetes Buy-and-Hold über BTCUSDT und ETHUSDT.

Signalzeitpunkt und Ausführung sind Point-in-Time:
abgeschlossener Bar -> nächster Open -> gleicher Bar-Close.

Es gibt keine Optimierung und keine Auswahl zwischen den beiden Hypothesen.
Kosten werden bei 1x, 2x und 4x des vorhandenen Projekt-Basissatzes von 0,15%
je Turnover-Einheit gerechnet.

## Daten

- Binance Public Klines
- BTCUSDT und ETHUSDT
- 15-Minuten-Bars
- 100.000 Candles je Asset
- 80% Research / 20% Holdout
- 5 feste Rolling-Fenster im Research

Intraday-Datenqualität prüft exakte 15-Minuten-Abstände, geschlossene Candles,
OHLC-/Volumen-Konsistenz und Freshness.

## Literatur als Hypothesen-Inspiration

Die Literatur ist hier ausdrücklich keine Evidenz für eine profitable
Projektstrategie. Sie motiviert nur die parallele Prüfung widersprüchlicher
Mikro-/Intraday-Mechanismen.

- Zarattini, Aziz & Barbon, Beat the Market: An Effective Intraday Momentum
  Strategy for S&P500 ETF (2024; revidiert 2025):
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172
- Herberger, Horn & Oehler, Are Intraday Reversal and Momentum Trading
  Strategies Feasible?:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3719233
- Fetna, Opening-Range Breakout Does Not Survive Trading Costs (2026),
  preregistered futures study:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7428398
- BIS Working Paper 1290, The speed premium: high-frequency trading and the
  cost of capital:
  https://www.bis.org/publications/working-paper-1290-speed-premium-high-frequency-trading-and-cost-capital

Die Quellen zeigen bewusst ein gemischtes Bild: Intraday Momentum wird in
einigen Arbeiten als prüfbare Hypothese beschrieben, während andere Arbeiten
Reversal-Effekte oder das Scheitern einfacher Intraday-Regeln unter realistischen
Kosten berichten. Deshalb ist der Sidecar als Falsifikations-/Research-Track
und nicht als vermeintlicher Edge konstruiert.

## Sicherheitsgrenze

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- keine Orders
- keine Integration in die tägliche ETF-Produktions-/Research-Strategie
