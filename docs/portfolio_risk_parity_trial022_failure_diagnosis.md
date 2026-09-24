# Failure-Diagnose: Trial 022 Portfolio Risk-Parity — 2026-09-24

## Zweck

Diese Diagnose ist kein neuer Alpha-Control. Sie ändert weder Trial 022 noch
dessen Gates und führt keine neue Auswahl- oder Parameterentscheidung ein.

## Befund

Im Holdout:

- Dynamic Return: +100,52% vs. 50/50 +114,92%
- Dynamic Drawdown: 23,83% vs. 50/50 24,87%
- Dynamic PF: 1,273 vs. 50/50 1,289
- zusätzlicher Allokations-Turnover: 4,97 Einheiten
- gesamter Turnover: 17,18 vs. 12,89 bei 50/50
- durchschnittliche Dynamic-Gewichte: 59,46% Trend / 40,54% Cross-Sectional

Die dynamische Allokation reduziert den Holdout-Drawdown um rund 1,04 Prozentpunkte,
erreicht aber die Projektgrenze von 10% bei weitem nicht.

## Mechanische Kostenzerlegung

Bei 15 bps Basiskosten je Turnover-Einheit verursacht der zusätzliche
Allokations-Turnover im Holdout rund 0,64 Prozentpunkte zusätzlichen Kosten-Drag.

Der Return-Abstand zu 50/50 beträgt rund 14,40 Prozentpunkte. Der zusätzliche
Turnover erklärt mechanisch nur rund 0,64 Prozentpunkte; rund 13,75 Prozentpunkte
bleiben als Residuum aus der unterschiedlichen Sleeve-Exposition über die
Stichprobe.

Im Research beträgt der zusätzliche Kosten-Drag rund 2,81 Prozentpunkte bei einem
Return-Abstand von rund 17,83 Prozentpunkten.

Das Residuum ist keine kausale Attribution.

## Diagnose

Der Engpass ist nicht ausschließlich Rebalancing-Kosten. Die Risk-Parity-Regel
erreicht eine kleine Drawdown-Verbesserung im Holdout, löst aber den absoluten
Drawdown-Failure nicht und verschlechtert Return und PF gegenüber 50/50.

Daher erfolgt kein weiteres Suchen über Lookback, Caps, Normalisierung oder Gewichte.

## Nächster Schritt

Vor einem weiteren Portfolio-Experiment wird eine explizit vorab formulierte,
signalneutrale Drawdown-/Exposure-Frage benötigt. Das nächste Experiment soll
nicht die Risk-Parity-Gewichte optimieren, sondern prüfen, ob ein bereits
definierter De-Risking-Mechanismus den bestehenden absoluten Drawdown-Engpass
adressiert, ohne die zugrunde liegenden Sleeve-Signale zu verändern.

