# Trial 025 — Marktresiduale Volatilität — 2026-09-24

## Trial-ID

T-2026-09-24-025

## Forschungsfrage

Prüft wird eine einzige, feste, monatliche Cross-Sectional-Hypothese:

Aktien mit der niedrigsten **marktresidualen historischen Volatilität** erzielen im Folgemonat eine robuste kostenbereinigte Rendite und einen positiven Low-Residual-Vol-vs-High-Residual-Vol-Edge.

Die Literatur motiviert die Prüfung mit der dokumentierten Beziehung zwischen hoher idiosynkratischer Volatilität und niedrigen durchschnittlichen Aktienrenditen. Ang, Hodrick, Xing und Zhang (2006) messen dies in einem Faktor-Kontext. Dieser Trial ist ausdrücklich **keine 1:1-Replikation** des dortigen Faktormodells, sondern ein bewusst einfacher, rein preisbasierter Marktresidual-Proxy für eine vorab definierte Robustheitsprüfung. citeturn981350search1

## Daten

Festes, vollständig symbol-disjunktes U.S.-Aktienuniversum:

COST, TMO, LIN, DE, EMR, SBUX, VZ, MA

- 3.500 Candles je Asset
- 3.498 Point-in-Time-Returnperioden
- Research: 2.798
- Holdout: 700
- Timestamp-Intersection-Alignment erforderlich
- bei zu kurzer gemeinsamer Historie: fail-closed
- historische Yahoo Daily-Daten

Die Symbole müssen gegenüber allen bereits registrierten Research-Universen vollständig disjunkt sein.

## Präregistrierte Regel

1. Für jeden Monat wird je Asset ausschließlich aus den unmittelbar vor dem aktuellen Monat abgeschlossenen 252 Daily-Close-to-Close-Returns eine marktresiduale Volatilität berechnet.
2. Der Markt-Faktor ist der gleichgewichtete Daily-Return der **anderen sieben Assets** (Leave-One-Out), sodass das betrachtete Asset nicht in seinen eigenen Referenzfaktor eingeht.
3. Auf dem 252-Sessionen-Fenster wird eine OLS-Regressionsgerade mit Intercept zwischen Asset-Return und Leave-One-Out-Marktreturn geschätzt.
4. Die Standardabweichung der 252 Regressionresiduen ist die einzige Ranking-Kennzahl.
5. Im aktuellen Monat werden die vier Assets mit der niedrigsten marktresidualen Volatilität mit jeweils 25% Long-Gewicht gehalten.
6. Die vier Assets mit der höchsten marktresidualen Volatilität dienen ausschließlich als deskriptiver High-Residual-Vol-Control für den Edge.
7. Gross Exposure: 1,0x; nur Long; keine Hebelung; kein Shorting.
8. Umschichtung: ausschließlich am Kalendermonatswechsel.
9. Kein Return des aktuellen Monats darf in die Auswahl eingehen.
10. Realisierung: Entscheidung am Timestamp t; nächstes vollständiges Close-to-Close-Intervall t+1 bis t+2.
11. Kosten: 10 bps Fee + 5 bps Slippage = 15 bps One-Way.
12. Kostenstress: 1,5x und 2,0x.
13. Keine Parameter-, Threshold-, Auswahlbreiten- oder Asset-Suche.

Der 252-Sessionen-Lookback und die Vier-von-Acht-Auswahl sind vorab fest.

## Entscheidungs-Gates

Alle folgenden Gates müssen gleichzeitig erfüllt sein:

- Research Return > 0
- Research Drawdown <= 10%
- Research Profit Factor >= 1,10
- mindestens 50% profitable Research-Rolling-Fenster
- OOS/Research Return Ratio >= 0,25
- Holdout Return > 0
- Holdout Drawdown <= 10%
- Holdout Profit Factor >= 1,10
- Holdout Return bei 1,5x Kosten >= 0
- Holdout Return bei 2,0x Kosten >= 0
- Low-Residual-Vol-minus-High-Residual-Vol Edge > 0 im Research
- Low-Residual-Vol-minus-High-Residual-Vol Edge > 0 im Holdout

Es gibt keinen nachträglichen Gate-Modifikator.

## Governance und Safety

- research_only = true
- strategy_variants = 1
- selection_after_results = false
- parameter_search = false
- threshold_search = false
- holdout_selection = false
- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- orders_enabled = False

Ein positives Ergebnis führt nicht automatisch zu Produktion. Promotion ist ein
separater Governance-Schritt nach unabhängiger Evidenz und unveränderten Gates.

## Literatur

- Ang, Hodrick, Xing & Zhang (2006), The Cross-Section of Volatility and Expected Returns, Journal of Finance 61(1), 259–299. citeturn981350search1
