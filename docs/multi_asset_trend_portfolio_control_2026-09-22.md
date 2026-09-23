# Multi-Asset Trend Portfolio Control — 2026-09-22

## Ziel

Der Control prüft, ob die im Literatur-Lab beobachtete Stabilität mittel-/langfristiger
Trendfamilien auf Portfolioebene erhalten bleibt.

Verwendet werden:
- SPY, QQQ, IWM
- exakt archivierte 5.000 Daily-Candles je Asset
- 4.500 Research-Candles + 500 Holdout-Candles
- Close(t) Entscheidung -> Open(t+1) -> Open(t+2) Renditeintervall
- feste Gebühren 0,10 % und Slippage 0,05 %
- ATR-basierte Exposition aus dem Literatur-Labor
- keine Optimierung
- keine Selection-Profile
- keine Änderung von Gates oder Produktionsparametern

## Getestete Portfolio-Konstruktionen

1. gleichgewichtetes Buy-and-Hold
2. gleichgewichtetes TSM-Ensemble 63/126/252
3. gleichgewichtetes SMA 50/200 Long/Flat
4. feste 50/50-Kombination aus TSM-Ensemble und SMA 50/200

## Ergebnisse

### Buy-and-Hold Referenz

Research:
- Rendite +443,1 %
- maximaler Drawdown 55,51 %
- Profit Factor 1,108

Holdout:
- Rendite +38,22 %
- maximaler Drawdown 23,11 %
- Profit Factor 1,193

Rolling:
- 4/5 Fenster positiv
- Fenster 4 negativ

### TSM-Ensemble 63/126/252

Research:
- Rendite +26,25 %
- maximaler Drawdown 8,77 %
- Profit Factor 1,073

Holdout:
- Rendite +5,12 %
- maximaler Drawdown 2,42 %
- Profit Factor 1,131

Rolling-Fenster:
- Fenster 1: -0,45 %, PF 0,990
- Fenster 2: -0,37 %, PF 0,995
- Fenster 3: +4,48 %, PF 1,136
- Fenster 4: +2,62 %, PF 1,075
- Fenster 5: +4,07 %, PF 1,128

3/5 Rolling-Fenster sind damit positiv.

### SMA 50/200 Long/Flat

Research:
- Rendite +39,35 %
- maximaler Drawdown 7,82 %
- Profit Factor 1,120

Holdout:
- Rendite +4,77 %
- maximaler Drawdown 4,43 %
- Profit Factor 1,127

Rolling-Fenster:
- Fenster 1: +6,30 %, PF 1,250
- Fenster 2: +2,73 %, PF 1,083
- Fenster 3: +3,46 %, PF 1,089
- Fenster 4: +0,95 %, PF 1,045
- Fenster 5: +7,05 %, PF 1,223

5/5 Rolling-Fenster sind positiv.

### Feste 50/50-Kombination TSM + SMA

Research:
- Rendite +32,98 %
- maximaler Drawdown 6,81 %
- Profit Factor 1,101

Holdout:
- Rendite +4,98 %
- maximaler Drawdown 2,86 %
- Profit Factor 1,140

Rolling-Fenster:
- Fenster 1: +2,89 %, PF 1,113
- Fenster 2: +1,18 %, PF 1,037
- Fenster 3: +4,01 %, PF 1,117
- Fenster 4: +1,81 %, PF 1,069
- Fenster 5: +5,56 %, PF 1,188

5/5 Rolling-Fenster sind positiv.

## Interpretation

Der Control zeigt einen deutlichen Unterschied zur bisherigen
Single-Asset-/Kurzfrist-Architektur:

- Trendportfolios reduzieren den maximalen Drawdown stark gegenüber
  gleichgewichteten Buy-and-Hold.
- SMA 50/200 und der feste TSM/SMA-Blend sind in allen fünf Rolling-Fenstern
  positiv.
- Der Holdout bleibt bei allen drei aktiven Trendkonstruktionen positiv.
- Buy-and-Hold liefert auf diesem historischen Aktienarchiv dennoch die höhere
  Roh-Rendite. Der Control belegt daher primär eine bessere Risiko-/Stabilitäts-
  struktur, nicht eigenständiges Alpha gegenüber der passiven Benchmark.

Der Befund ist deshalb noch kein Produktionsnachweis und keine Aussage,
dass SMA 50/200 oder der Blend die endgültige Strategie sein sollen.

## Methodische Konsequenz

Die nächste Forschungsstufe sollte nicht erneut nach dem besten Einzelwert suchen.

Stattdessen soll die Trendarchitektur vollständig vom Produktionspfad getrennt
weiterentwickelt werden:

Signal
-> Position Lifecycle
-> Exit
-> Volatilitätsskalierung
-> Portfolioaggregation
-> Kosten-/Turnover-Control
-> Robustness/WFO/Rolling-WF/Holdout

Besonders wichtig ist dabei, die Portfolioallokation gegen den jetzigen
equal-capital Control separat zu untersuchen. Die Literatur zu Trend Following
arbeitet häufig mit marktübergreifender Diversifikation und Risikoskalierung;
deshalb ist ein Risiko-basiertes, aber nicht optimiertes Portfolio-Weighting
ein sinnvoller nächster Kontrollschritt.

## Sicherheits- und Nicht-Änderungsregeln

- Paper-Only bleibt aktiv.
- LIVE_TRADING_ENABLED = False.
- Keine Orders im Research.
- Keine Änderung am Produktions-Parameterraum.
- Keine Änderung der Research-Gates.
- Kein automatischer Strategiewechsel.
