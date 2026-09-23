# Ergebnisse: Risikonormalisierter Trend-Portfolio-Control — 2026-09-22

Offizieller Run: 35777234246

Report-Fingerprint:
b4fb7d84102768684ba8ca55eee7d95da7da723c4eb4896715807976c8ab986c

## TSM-Ensemble, inverse-ATR-normalisiert

Research:
- Rendite +55,47 %
- maximaler Drawdown 36,28 %
- Profit Factor 1,046

Holdout:
- Rendite +15,63 %
- maximaler Drawdown 18,53 %
- Profit Factor 1,102

Rolling:
- Fenster 1: -9,20 %, PF 0,925
- Fenster 2: -3,55 %, PF 0,986
- Fenster 3: +13,54 %, PF 1,096
- Fenster 4: +2,55 %, PF 1,030
- Fenster 5: +14,12 %, PF 1,114

3/5 Rolling-Fenster positiv.

## SMA 50/200 Long/Flat, inverse-ATR-normalisiert

Research:
- Rendite +217,19 %
- maximaler Drawdown 47,24 %
- Profit Factor 1,108

Holdout:
- Rendite +19,91 %
- maximaler Drawdown 22,40 %
- Profit Factor 1,128

Rolling:
- Fenster 1: +13,71 %, PF 1,151
- Fenster 2: +6,75 %, PF 1,071
- Fenster 3: +50,95 %, PF 1,234
- Fenster 4: -0,74 %, PF 1,010
- Fenster 5: +39,32 %, PF 1,260

4/5 Rolling-Fenster positiv.

## Fester TSM/SMA-Blend, inverse-ATR-normalisiert

Research:
- Rendite +27,89 %
- maximaler Drawdown 44,02 %
- Profit Factor 1,033

Holdout:
- Rendite +21,84 %
- maximaler Drawdown 16,36 %
- Profit Factor 1,129

Rolling:
- Fenster 1: -9,56 %, PF 0,923
- Fenster 2: -3,41 %, PF 0,989
- Fenster 3: -3,50 %, PF 1,002
- Fenster 4: -1,69 %, PF 1,011
- Fenster 5: +16,85 %, PF 1,124

1/5 Rolling-Fenster positiv.

## Kontrollvergleich zum gleichgewichteten Portfolio

Der gleichgewichtete SMA-50/200-Control hatte:
- Research +39,35 %
- Holdout +4,77 %
- Holdout-Drawdown 4,43 %
- 5/5 positive Rolling-Fenster

Die inverse-ATR-Normierung erhöht damit die aktive Kapitalnutzung deutlich,
aber der maximale Drawdown steigt im Research stark. Der Holdout-Renditezuwachs
des SMA-Modells auf +19,91 % ist deshalb nicht als kostenloser Renditevorteil
zu interpretieren.

Der inverse-ATR-Blend erreicht einen Holdout-Drawdown von 16,36 % gegenüber
2,86 % beim gleichgewichteten Blend, verliert aber Rolling-Stabilität.

## Forschungsstatus

Die inverse-ATR-Gewichtung ist als eigenständige Portfolioallokationshypothese
interessant, aber nicht bestätigt als universell robuste Lösung.

Die Ergebnisse rechtfertigen:
- weitere Kosten-/Turnover-Stressprüfung
- längere/zusätzliche unabhängige Datenbasis
- spätere vollständige WFO-/Rolling-WF-/Robustness-/Overfit-/Holdout-Prüfung

Sie rechtfertigen nicht:
- einen Produktionswechsel
- eine Änderung der bestehenden Gates
- eine freie Gewichtungsoptimierung
- eine Auswahl eines einzigen „besten“ Trendmodells

Paper-Only bleibt aktiv; Live-Trading und Orderausführung bleiben deaktiviert.
