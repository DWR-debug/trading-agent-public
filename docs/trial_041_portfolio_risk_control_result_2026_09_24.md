# Trial 041 — Portfolio Risk Control Ergebnis — 2026-09-24

## Formale Provenienz

- Workflow: `36064175211`
- Artifact: `10835847008`
- Artifact-SHA256: `ceefba93fc79ec95eb83d6def33ace1ec5068f6dbc0ddf98f8d651b49821198a`
- Report-Fingerprint: `300fd4224b2a9df9a5f2bdcc55381fd5b239049605c7744c77ec43a15c6fdf7a`
- eingefrorene Trend-Coverage: `ebc08e73d9fad83da343e2ed15289b4ed05d4774346fb409994989f166469bab`
- eingefrorene Cross-Sectional-Coverage: `091fdc69edec4541c39654fabf308d64bbb7b7b80a9861a2cbe5492cd8ba3bf8`
- 3.498 gemeinsame Returns; 2.798 Research / 700 blinder Holdout

## Ergebnis

**NO_SUPPORT / archived_rejected**.

Der präregistrierte Challenger bestand die technischen Prüfungen und wurde tatsächlich auf dem eingefrorenen Coverage-Snapshot gerechnet. Er verfehlte jedoch die harten Risiko-/Transfer-Gates und darf nicht promotet werden.

Base-Szenario Challenger:
- Research Return: +81,26 %
- Research Max Drawdown: 37,27 %
- Research Profit Factor: 1,102
- minimale Rolling-PF: 1,032
- OOS/IS-Return-Ratio: 0,047
- Holdout Return: +44,18 %
- Holdout Max Drawdown: 19,63 %
- Holdout Profit Factor: 1,214

Fixed-50/50-Control:
- Research Return: +101,74 %
- Research Max Drawdown: 35,29 %
- Research Profit Factor: 1,100
- Holdout Return: +43,08 %
- Holdout Max Drawdown: 23,08 %
- Holdout Profit Factor: 1,179

Deskriptiv verbessert der Challenger im Holdout Drawdown und Profit Factor und hält die Rendite leicht höher. Die Verbesserung reicht aber nicht bis zum festen 10-%-Drawdown-Gate; zugleich verschlechtert sich die Research-Rendite und der Research-Drawdown.

## Rolling-Fenster

| Fenster | Challenger Return | Challenger DD | Challenger PF | Control Return | Control DD | Control PF |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 15,98 % | 9,63 % | 1,208 | 15,87 % | 10,20 % | 1,189 |
| 2 | 10,55 % | 12,29 % | 1,095 | 11,73 % | 16,41 % | 1,087 |
| 3 | 5,38 % | 20,51 % | 1,051 | 11,40 % | 21,80 % | 1,082 |
| 4 | 30,47 % | 35,49 % | 1,155 | 37,66 % | 35,29 % | 1,157 |
| 5 | 2,83 % | 14,79 % | 1,032 | 1,61 % | 15,65 % | 1,021 |

Die Risikosteuerung wirkt damit nicht konsistent genug über die fünf Research-Fenster, um den bestehenden Evidence-Vertrag zu erfüllen.

## Konsequenz

- Keine Produktionsintegration.
- Keine Änderung bestehender Gates.
- Keine Suche nach anderem Lookback, Gewichtscap, Rebalance-Timing oder Schwellenwert auf Basis des Holdouts.
- Portfolio-Risk-Control Q003 wird als blockiert geschlossen.
- Der nächste Forschungsschwerpunkt wechselt auf eine orthogonale Volatilitäts-/Relative-Value-Frage.
