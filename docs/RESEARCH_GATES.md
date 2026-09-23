# Research Gates

Ein Research-Durchlauf darf erst als PASSED gelten, wenn alle sechs Gates bestanden sind.

Die Gates sind konservative Mindesthürden für die weitere Forschung. Sie sind ausdrücklich kein Beweis für Profitabilität und keine Garantie für zukünftige Ergebnisse.

## 1. Datenqualität

Voraussetzungen:

- vollständige Candle-Validierung über den zentralen Data-Quality-Pfad
- mindestens 500 Candles
- keine ungültigen Timestamps, Duplikate, NaN/Infinity oder Sortierungsfehler

## 2. Backtest

Der Baseline-Backtest muss technisch und risikoseitig plausibel sein:

- mindestens 2 abgeschlossene Trades
- numerisch gültige Kennzahlen
- verbleibendes virtuelles Kapital größer als 0 EUR
- maximaler Drawdown höchstens 10 %

## 3. Walk-Forward

Der ausgewählte Kandidat muss auf dem Out-of-Sample-Fenster bestehen:

- mindestens 10 OOS-Trades
- OOS-Nettoergebnis > 0 EUR
- Profit Factor >= 1,10
- OOS-Max-Drawdown <= 10 %

## 4. Rolling Walk-Forward

Die wiederholten OOS-Fenster müssen gemeinsam ausreichend belastbar sein:

- mindestens 30 OOS-Trades
- Gesamtergebnis > 0 EUR
- Profit Factor >= 1,10
- mindestens 50 % profitable Fenster
- höchstens 25 % Fenster ohne Trades
- durchschnittlicher Drawdown <= 10 %

## 5. Robustheit

Die Parameter dürfen nicht nur an einem einzelnen Punkt funktionieren:

- mindestens vier verfügbare lokale Parameter-Varianten
- mindestens 50 % der getesteten Varianten müssen positiv sein
- zusätzlich muss der ausgewählte Kandidat bei 1,5x Gebühren und Slippage weiterhin ein nicht-negatives OOS-Ergebnis erzielen

Die Robustheitsprüfung verändert nur Strategieparameter bzw. die angenommenen Ausführungskosten. Sicherheitslimits für Risiko und Hebel werden nicht überschritten.

## 6. Overfit

Der ausgewählte Walk-Forward-Kandidat wird erneut auf seinem Trainingsfenster bewertet.

Er muss:

- im Training eine positive Rendite haben
- mindestens 25 % seiner Trainingsrendite im OOS-Test erhalten

Formal ist erforderlich:

OOS-Rendite / In-Sample-Rendite >= 0,25

Dieser Quotient ist eine konservative Heuristik gegen extreme In-Sample-/OOS-Lücken. Er ist keine mathematische Garantie gegen Overfitting.

## Verhalten bei Fehlern

Bei mindestens einem fehlgeschlagenen Gate lautet der Research-Status BLOCKED.

Der Research-Workflow darf dann keinen Writeback als validiertes Ergebnis durchführen.

Ein BLOCKED-Report wird trotzdem als Artifact gespeichert, damit die Ursache reproduzierbar dokumentiert bleibt.

Die permanente autonome Research-Schleife bleibt separat deaktiviert. Diese Gates sind eine Qualitätsbarriere, keine Freigabe für Echtgeldhandel.
