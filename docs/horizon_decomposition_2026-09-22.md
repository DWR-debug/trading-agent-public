# Horizon-Dekomposition 2026-09-22

## Zweck

Dieser Kontrolllauf zerlegt den beobachteten Horizon-Effekt in einem kontrollierten 2x2-Design.

## Design

- kurze Research-Historie: 2.250 Candles, Slice [2250:4500]
- lange Research-Historie: 4.500 Candles, Slice [0:4500]
- kleiner Holdout: 250 Candles, Slice [4500:4750]
- großer Holdout: 500 Candles, Slice [4500:5000]

Beide Research-Bedingungen enden am identischen Index 4.500. Beide Holdout-Bedingungen beginnen am identischen Index 4.500.

Der 2.250-Candle-Trainingsarm ist bewusst nicht identisch mit dem historischen 2.500-Candle-Report. Er ist ein neuer Kontrollarm, damit Trainingshistorie und Holdout-Stichprobengröße getrennt untersucht werden können.

## Unverändert

Strategie, Parameterraum, Selection-Profile, Research-Gates, Gate-Schwellenwerte, Gebühren, Slippage und Paper-Only-Sicherheitszustand bleiben unverändert.

## Auswertung

Für jede Asset/Profile-Kombination werden zwei Research-Läufe durchgeführt, einer je Trainingslänge. Der daraus ausgewählte Kandidat wird anschließend auf beiden Holdout-Größen geprüft.

Die Holdout-Größe darf die Kandidatenauswahl nicht verändern. Diese Invarianz wird im Lauf automatisch geprüft.

Die Auswertung berichtet:

- Gate-Passraten je 2x2-Zelle
- Haupteffekt der Trainingshistorie
- Haupteffekt der Holdout-Größe
- Interaktion beider Faktoren
- konkrete Failure-Kriterien je Gate
- Änderungen des ausgewählten Kandidaten durch zusätzliche Trainingshistorie

Der Lauf ist diagnostisch und stellt keine Änderung des Forschungsprotokolls dar.
