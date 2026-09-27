# Q024 — Treasury Auction-Result Publication Timestamp / PIT Feasibility

Stand: 2026-09-27

## Zweck

Q024 is the direct follow-up to Q023/H2. Q023 established reproducible official
Offering Announcement timestamps for all 89 fixed Q019 events, but those timestamps
describe the pre-auction offering document. The Q019 signal itself is the
`bid_to_cover_ratio`, which is an auction-result statistic. Q024 therefore asks:

> Kann der tatsächliche Zeitpunkt, zu dem das für Q019 verwendete
> `bid_to_cover_ratio` öffentlich verfügbar wurde, für die gesamte feste Q019-
> Ereignispopulation historisch reproduzierbar bestimmt werden?

Q024 erzeugt **keine Performance-Evidence**.

## Ex ante fixierter Datenvertrag

Ausgangsbasis bleibt ausschließlich die bereits fixierte Q019-Eventpopulation
(89 Treasury-10-Year-Treasury-Securities-Auction-Result-Zeilen im
Studienfenster 2011-01-01 bis 2025-09-24).

Für jedes Event müssen mindestens diese Felder erhalten bleiben:

- Q019 `record_date`
- Q019 `auction_date`
- Q019 `cusip`
- Q019 `bid_to_cover_ratio`
- gefundener offizieller Auction-Results-Identifikator
- offizielle Quelle
- reproduzierbarer Veröffentlichungstimestamp inklusive Zeitzone
- Provenance-/Content-Fingerprint
- Differenz zwischen dem offiziellen Result-Publication-Timestamp und Q019
  `record_date`

## Zulässige Primärquellen

1. Offizielle Treasury Auction Results RSS / Feed-Metadaten.
2. Offizielle Treasury Auction Results XML/result files, soweit historisch
   deterministisch abrufbar.
3. Offizielle Treasury Auction Results PDFs, aber nur als Identitäts-/Inhaltsbeleg;
   ein PDF-Datum allein ist **nicht** automatisch ein Intraday-Publication-Timestamp.

Die Treasury-Auction-Timeline dokumentiert, dass seit Januar 2003 die offizielle
Auction-Release-Time als aufgezeichnete Zustellung der Results-XML an den Federal
Reserve Information Technology (FRIT)-Server definiert wurde. Sie dokumentiert
außerdem die automatisierte Internet-Veröffentlichung der Ergebnis-PDFs seit 2004
und die spätere Standardisierung der schnellen Resultate-Veröffentlichung.
Diese historische Semantik soll in Q024 getrennt von einer tatsächlich
reproduzierbaren Ereigniszeit geprüft werden.

## Matching-Regel

Eine Quelle darf einem Q019-Event nur zugeordnet werden, wenn mindestens
`cusip` und `auction_date` eindeutig mit dem Q019-Datensatz übereinstimmen und
die Quelle tatsächlich das Q019-`bid_to_cover_ratio` oder dessen vollständige
Bestandteile enthält. Ein RSS-Link auf ein passendes PDF ersetzt diese
zweifache Event- und Signalidentifikation nicht.

## Timestamp-Regel

Ein Event erhält nur dann `RESULT_TIMESTAMP_VALIDATED`, wenn der
Veröffentlichungszeitpunkt reproduzierbar und explizit aus einer zulässigen
Primärquelle oder deren dokumentierter Release-Metadatenstruktur ableitbar ist.

Ein bloßes PDF-Datum `For Immediate Release <date>` gilt nicht als hinreichender
Intraday-Timestamp.

Kann der echte Result-Publication-Timestamp nicht reproduzierbar bestimmt werden,
wird das Event als `RESULT_TIMESTAMP_INSUFFICIENT` klassifiziert.

## PIT-Prüfung

Der gefundene Result-Publication-Timestamp muss vor dem tatsächlich nächsten
verwendbaren Handelstag des Q019-Contracts liegen bzw. dessen Intraday-Position
muss eindeutig bestimmbar sein.

Es wird nur die Verfügbarkeit der Information geprüft. Keine Forward Returns,
kein P&L, kein Backtest.

Der Runner schreibt je Event außerdem den ersten folgenden XNYS-Handelstag und
akzeptiert die PIT-Prüfung nur, wenn der explizite Result-Timestamp vor diesem
Tag liegt. Ein Timestamp ohne nachweisbaren Signalinhalt oder ohne bestandene
PIT-Prüfung zählt nicht als Q024-Pass.

## Falsifikation / DATA_INSUFFICIENT

Q024 ist `DATA_INSUFFICIENT`, wenn für den vorab fixierten Mindestanteil der 89
Q019-Events kein reproduzierbarer Result-Publication-Timestamp verfügbar ist oder
die Quelle keine eindeutige Verbindung zwischen Timestamp und dem
`bid_to_cover_ratio` erlaubt.

Empfehlung des Vertrags: vollständige 89/89-Reproduzierbarkeit als Pass-Kriterium.

## Governance

- keine Performance
- kein Holdout
- keine Parameter-, Asset-, Threshold-, Horizon- oder Variantensuche
- keine nachträgliche Auswahl
- keine Gate-Änderung
- keine Promotion
- keine Live-Ausführung

Sicherheit:

`PAPER_ONLY=True`
`LIVE_TRADING_ENABLED=False`
`orders_enabled=False`
`automatic_promotion=False`

## Ergebnisregel

**Q024 PASS bedeutet nur:** Der tatsächliche Informationszeitpunkt des Q019-
`bid_to_cover_ratio` ist reproduzierbar.

Erst danach darf ein separat präregistrierter H2-Performanceversuch auf einem
neuen symbol-disjunkten Universum vorbereitet werden.

Q024 darf nicht dazu verwendet werden, Q020 nachträglich umzuschreiben oder
eine profitable Timestamp-Variante auszuwählen.

## Quellenbasis

Treasury dokumentiert die Auction-Results-Timeline und unterscheidet ausdrücklich
zwischen dem Result-Release und späteren Zusatzinformationen. Offizielle
Auction-Results-PDFs enthalten den `Bid-to-Cover Ratio`-Wert, z.B. die
10-Year-Note-Ausgabe vom 06.08.2025 für CUSIP 91282CNT4.


## Historical XML archive handling

The runner also probes the official TreasuryDirect `/xml/` result archive for deterministic result-file identity. HTTP `Last-Modified` metadata is preserved as provenance only and is explicitly **not** treated as the official auction-release timestamp. Q024 timestamp validation remains dependent on an explicit/deterministically documented publication timestamp tied to the auction result signal.
