# Trial T-2026-09-24-031 — Risk-Adjusted Cross-Sectional Momentum

## Status

**NO_SUPPORT / archived_rejected**

Trial 031 wurde als einzelner, vorab präregistrierter Research-Control vollständig und reproduzierbar ausgeführt. Es gab keine Parameter-, Threshold- oder Varianten-Suche, keine Holdout-Selektion und keine Orders.

## Technischer Nachweis

- Merge-Commit: `52f51aff2e9aeb828f8d3c5c2889bd4960cef0f8`
- Trial-Branch-Commit: `ba5480ae789facc922015c4fe13a57c94f73703a`
- Research-Workflow: `36043071782`
- Artifact: `10826903506`
- Artifact-Digest: `sha256:9b42882a4ee9082c2b6194f4b671513b7da50685d850bac561aaa3df1bab551a`
- Report-Fingerprint: `f22e6cad28fbfbf73495f35da056b0bb8fe80c30ecd7d54deb09385452533cad`
- Coverage-Preflight: Workflow `36042442309`, Artifact `10827700335`
- Coverage: 13/13 Symbole, 3.500 Candles je Asset, 3.520 gemeinsamer Kalender im Preflight, 3.498 gemeinsame PIT-Returnperioden
- Research/Holdout: 2.798 / 700
- Vollständige symbolische Disjunktheit zum bisherigen Research-Universum
- Trial-031-spezifischer Prerequisite-Job: grün
- Trial-031-spezifischer Research-Job: grün
- Vollständige Testsuite im korrekten Trial-031-Stand: **671 passed**
- Sicherheitsvertrag: Paper-only, keine Live-Orders

## Intervention

Unverändert blieben:

- 50/50 Trend + Cross-Sectional
- SMA 50/200 inverse-volatility Trend-Sleeve
- Top-2 long-only Cross-Sectional-Sleeve
- aggregiertes 63-Session-/10%-Volatilitätsbudget
- Point-in-Time-Ausführung
- 10 bps Fee + 5 bps Slippage
- 1,5x-/2x-Kostenstress

Einzige Änderung:

**CS-Score = 252-Session kumulierte Rendite / Realized Volatility derselben 252-Session Formationperiode, 21 Sessions vor Rebalance abgeschlossen.**

Keine Short-Positionen und kein Hebel über 1x.

## Ergebnis

| Kennzahl | Fixed 50/50 | Risk-adjusted CS |
|---|---:|---:|
| Research Return | +1,65 % | -8,37 % |
| Research Max DD | 22,65 % | 26,77 % |
| Research PF | 1,011 | 0,994 |
| Holdout Return | +27,14 % | +24,47 % |
| Holdout Max DD | 15,59 % | 14,56 % |
| Holdout PF | 1,165 | 1,150 |
| Profitable Research Windows | 3/5 | 3/5 |
| Rolling PF | 1,011 | 0,994 |
| OOS/IS Return Ratio | 16,45 | 0,00 |

Kostenstress für den Risk-adjusted Challenger blieb positiv:

- 1,5x Kosten: Holdout +23,26 %
- 2,0x Kosten: Holdout +22,06 %

Auch die Total-Return-Sensitivität blieb im Holdout positiv (+30,43 %). Diese positiven Teilbefunde kompensieren jedoch nicht die verfehlten Research-, Drawdown-, PF- und Robustheits-Gates.

## Gate-Diagnose

Absolute Gates nicht erfüllt:

- Research-Return
- Research-Drawdown
- Research-PF
- Rolling-PF
- durchschnittlicher Rolling-Drawdown
- OOS/IS
- Holdout-Drawdown

Zusätzlich verfehlt der Challenger gegenüber dem Fixed Candidate die Nicht-Verschlechterungsbedingungen für Research-Return, Research-DD, Research-PF, Rolling-PF, Rolling-DD, OOS/IS, Holdout-Return und Holdout-PF. Nicht schlechter waren nur die profitable Rolling-Fensterquote und der Holdout-Drawdown.

## Konsequenz

Trial 031 wird **nicht** in die Produktionsstrategie übernommen.

Es folgt keine nachträgliche Suche über Volatilitätsnormalisierung, Lookback, Skip, Top-N oder andere risikoadjustierte Momentumparameter. Der Fixed Candidate bleibt unverändert **BLOCKED**; ein 30-Tage-Paper-Experiment mit ihm ist nicht freigeschaltet.

Der nächste Research-Schritt soll wieder orthogonal zur bislang ausgiebig geprüften Volatilitäts-/Risk-Layer-Familie sein und vorab auf einem neuen vollständig disjunkten Datensatz geprüft werden.
