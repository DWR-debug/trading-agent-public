# Trial T-2026-09-25-043 — Coverage-Ergebnis

## Status

**DATA_INVALID / NO_SCIENTIFIC_OUTCOME**

T043 wurde vor jeder Performanceauswertung korrekt durch das Coverage-Gate gestoppt.
Die 13 Symbole lieferten jeweils genau 3.500 gültige Candles, aber nur **3.499
gemeinsame Kalendertimestamps**. Damit war der präregistrierte Zielvertrag von
3.500 gemeinsamen Candles nicht erfüllt.

## Technischer Nachweis

- Coverage-Workflow: `36112272492`
- Artifact-ID: `10852968148`
- Coverage-Fingerprint: `c70113976cdac68d8fa44617668e01b91dc7af272c3b3b89026fd90747d0f983`
- 13/13 Symbole: 3.500 Candles
- gemeinsamer Kalender: 3.499
- Research-/Holdout-Auswertung: **nicht ausgeführt**
- Selection: **nicht ausgeführt**
- Paper-only: bestanden

## Interpretation

Dies ist **kein Performanceergebnis** und keine negative Aussage über die
T043-Signalhypothese. Der Datenvertrag hat korrekt verhindert, dass aus einer
nicht ausreichend ausgerichteten Datenbasis wissenschaftliche Evidenz erzeugt
wird.

Der Fehler entsteht durch die Rohabdeckung/Ausrichtung der separat gelieferten
3.500 Datensätze: einige Reihen beginnen einen Handelstag später. Eine nachträgliche
Reduktion des Zielkalenders oder Lockerung der Gates wird ausdrücklich nicht vorgenommen.

## Reparaturpfad

T043 wird als DATA_INVALID archiviert und nicht wiederverwendet. Der nächste Schritt
ist ein **neuer Repair-Successor T044** mit unveränderter Signalhypothese und
unverändertem Ziel von 3.500 gemeinsamen Candles, aber größerem angefordertem
Rohdatenfenster. Die zusätzliche Rohhistorie dient ausschließlich dazu, den
bereits festgelegten gemeinsamen Kalender technisch vollständig bilden zu können.

Keine Parameter-/Variantensuche, keine Holdout-Selektion, keine Gate-Änderung,
keine Produktionsintegration, keine Orders.

## Sicherheitsstatus

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`  
`automatic_promotion=False`
