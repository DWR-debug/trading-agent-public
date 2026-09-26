# Q023 — Treasury Release-Timestamp / PIT Feasibility

Stand: 2026-09-26

## Zweck

Q023 ist eine **DESIGN_ONLY / SOURCE-FEASIBILITY** Untersuchung der H2-Frage aus
Q022:

> Repräsentiert `record_date` den tatsächlich handelbaren Informationszeitpunkt des
> Treasury-Auktionssignals hinreichend?

Es wird **keine Performance berechnet**, kein Holdout geöffnet und keine
Richtung/Parameter/Asset-/Horizon-Variante ausgewählt.

## Ex ante fixierter Datenvertrag

Die bestehende Q019-Treasury-Eventpopulation bleibt die einzige Ausgangsbasis.
Für jedes 10-Year-Note-Auktionsereignis wird eine offizielle Treasury Offering
Announcement Quelle gesucht und deterministisch protokolliert.

Zulässige Primärquellen:

1. TreasuryDirect Offering Announcement PDFs.
2. FiscalData veröffentlichte Treasury-Auction-Announcement PDFs.

Der Veröffentlichungszeitpunkt wird ausschließlich aus der im offiziellen Dokument
ausgewiesenen **Embargo-Zeit ("Embargoed Until")** und dem Dokumentdatum abgeleitet.
Kann dieser Zeitpunkt nicht reproduzierbar extrahiert werden, wird das Ereignis als
timestamp-insufficient markiert; es erfolgt keine Ergebnisrettung über andere Quellen.

## Prüfungen

Für jedes Ereignis werden mindestens erfasst:

- Q019 `record_date`
- offizielles Dokumentdatum
- offizieller "Embargoed Until"-Zeitpunkt inklusive Zeitzone
- deterministischer Announcement-Identifikator/URL
- Parsing-/Provenance-Fingerprint
- Differenz zwischen `record_date` und offizieller Veröffentlichungszeit
- ob vor dem ersten folgenden XNYS-Handelstag ein tatsächlich öffentlicher
  Informationszeitpunkt reproduzierbar festgestellt werden kann

## Falsifikation / DATA_INSUFFICIENT

Q023 gilt als `DATA_INSUFFICIENT`, wenn ein vorab definierter Mindestanteil der
Q019-Ereignisse keine reproduzierbare offizielle Timestamp-Quelle besitzt oder der
Timestamp nicht eindeutig ableitbar ist.

Ein erfolgreicher Q023-Befund ist **kein Alpha-Nachweis**. Er schafft lediglich die
Voraussetzung für eine spätere separate H2-Performance-Präregistrierung mit einem
neuen symbol-disjunkten Universum.

## Governance

- kein Performance-Run
- kein Holdout
- keine Parameter-/Asset-/Threshold-/Horizon-/Variantensuche
- keine Gate-Änderung
- keine Promotion
- keine Live-Ausführung

Sicherheit:

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`  
`automatic_promotion=False`

## Offizielle Quellen

TreasuryDirect veröffentlicht Offering Announcements mit explizitem
"Embargoed Until"-Zeitpunkt; Beispiele umfassen 10-Year Notes und Treasury
Auction Announcement PDFs. Die Q023-Implementierung muss die konkreten historischen
Dokumente pro Ereignis deterministisch auflösen und deren Fingerprints sichern.
