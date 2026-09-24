# Einkommens-Research

## Forschungszweck

Der Agent soll perspektivisch nicht nur eine positive Equity-Kurve erzeugen,
sondern daraus einen nachhaltigen und kontrollierbaren Auszahlungsstrom
ermöglichen.

Das initiale geschützte Grundkapital beträgt **500 EUR**.

## Konservatives Simulationsmodell

Die aktuelle Research-Simulation verwendet einen High-Water-Mark-Ansatz:

1. Das geschützte Grundkapital darf nicht ausgeschüttet werden.
2. Gewinne unterhalb des bisherigen High-Water-Mark werden nicht ausgeschüttet.
3. Eine Auszahlung kann nur bei einem neuen Kapitalhoch entstehen.
4. Die Auszahlung kann als Anteil des neuen Überschusses parametrisiert werden.
5. Ein zusätzlicher Reservebetrag kann oberhalb des Grundkapitals geschützt werden.
6. Die Auszahlungsperiode ist explizit konfigurierbar.
7. Eine Verlustphase kann deshalb die nächste Auszahlung auf null setzen.

Dieses Modell ist ein Forschungsbaustein, noch keine Produktionsregel.

## Was künftig gemessen werden muss

Für jede vollständig validierte Strategie bzw. Strategie-Kombination werden
später mindestens untersucht:

- Gesamtbetrag der Ausschüttungen,
- Median und unteres Quantil der Ausschüttungen,
- Anteil der Perioden ohne Ausschüttung,
- längste Auszahlungspause,
- verbleibendes Arbeitskapital,
- Kapitalbodenverletzungen,
- Maximum Drawdown nach Ausschüttungen,
- Verhalten in historischen Stressphasen,
- Sensitivität gegenüber Kosten und Slippage,
- Verhalten bei zusätzlicher Kapitalzufuhr,
- Nachhaltigkeit über verschiedene historische Startpunkte.

Besonders wichtig ist die Betrachtung **nach** Ausschüttungen. Ein System, das
vor Ausschüttungen robust aussieht, kann durch regelmäßige Entnahmen einen
anderen Kapitalpfad erhalten.

## Noch nicht festgelegte Produktionsgrößen

Die folgenden Größen werden erst nach einer belastbaren Multi-Strategie-OOS-
Evidenz präregistriert:

- gewünschte monatliche Mindestentnahme,
- maximal akzeptabler Drawdown im Einkommensbetrieb,
- Mindest-Kapitalpuffer,
- Auszahlungsintervall,
- Anteil des Gewinns, der ausgeschüttet werden darf,
- Regeln für zusätzliche Einzahlungen und spätere Kapitalaufstockung.

Keine dieser Größen wird rückwirkend anhand bereits beobachteter Gewinne
angepasst.

## Sicherheitsstatus

Die Simulation ist rein offline und kann weder Broker-Orders noch Live-Trading
auslösen.
