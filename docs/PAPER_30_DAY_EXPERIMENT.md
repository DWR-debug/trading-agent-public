# Paper-only 30-Tage-Experiment-Harness

Der Harness bildet den nächsten technischen Schritt Richtung autonomes
30-Tage-Experiment ab, ohne die aktuelle Paper-only-Sicherheitsgrenze zu ändern.

## Vertrag

Ein Lauf akzeptiert genau **eine** bereits Evidence-eligible Strategie:

- Evidence-Status muss `VALIDATED_PASS` sein.
- Alle deklarierten Gates müssen bestanden sein.
- Holdout darf nicht zur Selektion verwendet worden sein.
- Paper-only muss aktiv sein.
- Live-Trading und Orders müssen deaktiviert sein.
- Der Return-Stream muss exakt 30 Tagesbeobachtungen enthalten.
- Die Tagesreturns müssen bereits netto des deklarierten Kostenvertrags sein.
- Kein Kandidatenvergleich und keine automatische Auswahl findet statt.

Das Default-Startkapital ist 10 EUR, bleibt aber ein frei gesetzter Simulationsparameter.

## Checkpoint / Resume

Nach jedem Tag wird ein atomarer Checkpoint gespeichert. Der Checkpoint bindet:

Dataset-/Evidence-Kontext, Strategy-ID, Trial-ID, 30-Tage-Returnstream und Startkapital.

Bei `--resume` wird diese Identität erneut geprüft. Eine abweichende Return-Serie,
Evidence oder Kapitalbasis führt fail-closed zum Abbruch.

## Ergebnis

Der Abschlussbericht speichert mindestens:

- Final Equity nach 30 Tagen
- kumulierte Rendite
- Maximum Drawdown
- Minimum Equity
- Tagesbeobachtungen
- Return-Stream-Fingerprint
- Input-Fingerprint
- Evidence-/Safety-Status

## Grenzen

Der Harness ist eine **Offline-/Paper-Simulationskomponente**. Er ist noch kein
Marktdaten-Streamer und besitzt keine Broker- oder Live-Order-Anbindung.

Für einen späteren Echtgeldpfad müssen zusätzlich Venue, Mindestorders,
Gebühren, Slippage, Liquidität, Datenzugriff und eine explizite Live-Freigabe
geprüft werden. Diese Komponente kann eine solche Freigabe nicht selbst erzeugen.

## Sicherheitsstatus

`PAPER_ONLY=True`

`LIVE_TRADING_ENABLED=False`

`orders_enabled=False`
