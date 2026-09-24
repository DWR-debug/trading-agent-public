# Ergebnis: Ein-Sitzungs-CS-Cooldown – fünfte Validierung (2026-09-24)

## Status

Der präregistrierte Ein-Sitzungs-CS-Cooldown wird VERWORFEN.

Die Hypothese wurde auf einem fünften, vollständig symbol-disjunkten
Validierungssatz mit 3.500 gemeinsamen Candles sowie 2.798 Research- und
700 Holdout-Return-Perioden ausgeführt. Es gab keine Parameter-, Gewichts-,
Schwellenwert- oder Varianten-Suche. Holdout wurde ausschließlich als
Bestätigung verwendet.

## Präzise Ergebnisse

### Unveränderte Baseline

Research:
- Return: +30.0999%
- Maximum Drawdown: 18.4904%
- Rolling Profit Factor: 1.05584
- Rolling-Durchschnittsdrawdown: 14.0025%
- profitable Rolling-Fenster: 4/5
- OOS/IS-Return-Verhältnis: 0.98756

Holdout:
- Return: +29.7254%
- Maximum Drawdown: 12.8766%
- Profit Factor: 1.19478

### Ein-Sitzungs-Cooldown

Research:
- Return: -55.7179%
- Maximum Drawdown: 57.6982%
- Rolling Profit Factor: 0.84093
- Rolling-Durchschnittsdrawdown: 20.7506%
- profitable Rolling-Fenster: 0/5

Holdout:
- Return: -0.0970%
- Maximum Drawdown: 13.4705%
- Profit Factor: 1.00689

Damit waren alle vier vorab festgelegten Research-Richtungen negativ:
- Research-Maximum-Drawdown nicht besser: nein
- Rolling-Profit-Factor nicht besser: nein
- Rolling-Durchschnittsdrawdown nicht besser: nein
- Research-Rendite nicht besser: nein

Auch die drei separaten Holdout-Bestätigungen waren negativ:
- Holdout-Rendite nicht schlechter: nein
- Holdout-Drawdown nicht schlechter: nein
- Holdout-Profit-Factor nicht schlechter: nein

## Interpretation

Der Befund spricht klar gegen diese konkrete Sofortreaktion.

Wichtig ist die methodische Einordnung: Das Ergebnis widerlegt nicht den zuvor
replizierten CS-Winner-Reversal-Befund. Es zeigt vielmehr, dass die einfache
Handlungsregel "am Folgetag den gesamten CS-Sleeve aussetzen" aus diesem Befund
keine robuste praktische Verbesserung erzeugt.

Die schlechte fünfte Baseline bestätigt zugleich, dass das fünfte Universum
selbst anspruchsvoll ist; der Cooldown verschlechtert die bereits vorhandenen
Research-Probleme jedoch deutlich und verschlechtert zusätzlich die Holdout-
Eigenschaften.

## Reproduzierbarkeit

Validation artifact: 10798118481

Report fingerprint:
9cb5d0431efe4d0116d394acbc06ea19017689d9b84ae3383651e5c93024a4ab

Trend-manifest fingerprint:
43d744eebc6ab9e97d4a547407865f9bf7590310b9e1709efb166c98fc7f6e0e

CS-manifest fingerprint:
f1a9f3e8a1de244ed7d709941cb926b3a1566c4dcbce8654c0d5b4cb55929e23

Die Workflow-Checks für Testsuite, Paper-only-Sicherheit, vollständige
Disjunktheit, Präregistrierung und Ergebnisintegrität waren erfolgreich.

## Forschungsentscheidung

Der Pfad wird nach der Präregistrierung beendet:
- kein Tuning des Cooldowns auf demselben fünften Satz;
- keine nachträgliche Auswahl einer anderen Cooldown-Länge;
- keine Änderung bestehender Research-Gates;
- keine Produktionsintegration;
- keine Orders;
- PAPER_ONLY=True;
- LIVE_TRADING_ENABLED=False.

Der nächste sinnvolle Forschungsbaustein ist daher keine weitere Variante dieses
Cooldowns, sondern die Charakterisierung der zeitnahen Reversal-Folgebewegung
auf einer neuen, präregistrierten Basis. Erst daraus darf eine neue Architektur-
hypothese entstehen.
