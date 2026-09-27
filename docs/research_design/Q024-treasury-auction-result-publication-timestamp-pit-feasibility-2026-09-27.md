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
   deterministisch abrufbar. Der offizielle XML-Archivpfad verwendet
   `https://www.treasurydirect.gov/xml/R_YYYYMMDD_N.xml`.
3. Offizielle Treasury Auction Results PDFs, aber nur als Identitäts-/Inhaltsbeleg;
   ein PDF-Datum allein ist **nicht** automatisch ein Intraday-Publication-Timestamp.

Die Treasury-Auction-Timeline dokumentiert, dass seit Januar 2003 die offizielle
Auction-Release-Time als aufgezeichnete Zustellung der Results-XML an den Federal
Reserve Information Technology (FRIT)-Server definiert wurde. Sie dokumentiert
außerdem die automatisierte Internet-Veröffentlichung der Ergebnis-PDFs seit 2004
und die spätere Standardisierung der schnellen Resultate-Veröffentlichung.
Diese historische Semantik soll in Q024 getrennt von einer tatsächlich
reproduzierbaren Ereigniszeit geprüft werden.

## XML-Result-Dateien: Implementierungsvertrag

Die XML-Archiveinträge werden deterministisch anhand
`R_<auction_date>_<sequence>.xml` unter `/xml/` geprüft (feste Sequenzgrenze
1 bis 8; kein inhalts-/ergebnisabhängiges Ranking). Ein XML-Event wird nur
zugeordnet, wenn `AuctionAnnouncement/CUSIP` und `AuctionDate` mit Q019
übereinstimmen, `AuctionResults/BidToCoverRatio` numerisch dem Q019-Signal
entspricht und `ResultsPDFName` zur aufgerufenen XML-Datei passt. Mehrere oder
keine passenden Result-Dateien sind nicht eindeutig und bleiben unzureichend.
Der Output protokolliert für jede getestete URL 404, Quellfehler oder
Inhaltsfingerprint/Header plus Identitäts-Match/-Mismatch.

Der Timestamp wird aus `AuctionAnnouncement/AuctionDate` und
`AuctionResults/ReleaseTime` gebildet. `ReleaseTime` ist ein XML-Militärzeitfeld
ohne eingebetteten UTC-Offset; die Implementierung weist deshalb die
Treasury-Auktionszeitzone `America/New_York` explizit aus und protokolliert
lokale Zeit sowie UTC-Normalisierung. Ein fehlendes oder nicht parsebares
`ReleaseTime` ist kein validierter Timestamp. Die HTTP-Header `Last-Modified`,
`ETag` und `Content-MD5` bleiben Provenienzmetadaten: insbesondere wird
`Last-Modified` niemals als historischer Veröffentlichungszeitpunkt verwendet.

Gezielte Abrufprüfungen bestätigten die offizielle XML-Struktur sowohl für
`R_20110112_2.xml` als auch für `R_20250806_2.xml`; beide enthalten CUSIP,
AuctionDate, BidToCoverRatio, ReleaseTime und ResultsPDFName. Das sind
Format-/Quellenprüfungen, **keine** 89-Event-Coverage-Auswertung. Die
Antworten führten `Last-Modified` aus Mai 2026, daher belegt dieser Header
gerade nicht den historischen Auction-Result-Release. Der Runner erhält diese
Header nur als Herkunftsinformation. Die offiziellen Treasury-Schemas
`https://www.treasurydirect.gov/xsd/Auction_v1_0_0.xsd` und
`https://www.treasurydirect.gov/xsd/Auction_v7_0_0.xsd` beschreiben
`ReleaseTime` als `EmptyMilitaryTimeType` und `AuctionDate` als Datum; die
XML-Datei selbst enthält keinen UTC-Offset.

## Matching-Regel

Eine Quelle darf einem Q019-Event nur zugeordnet werden, wenn mindestens
`cusip` und `auction_date` eindeutig mit dem Q019-Datensatz übereinstimmen und
die Quelle tatsächlich das Q019-`bid_to_cover_ratio` oder dessen vollständige
Bestandteile enthält.

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

Da die Q019-Handelsaktion erst in der ersten XNYS-Session strikt nach
`record_date` liegt, kann die PIT-Ordnung ohne Rendite-/P&L-Berechnung
nachgewiesen werden, wenn der offizielle XML-Release auf `auction_date` liegt
und `auction_date < record_date`. Andernfalls bleibt das Event PIT-unzureichend.

Es wird nur die Verfügbarkeit der Information geprüft. Keine Forward Returns,
kein P&L, kein Backtest.

## Falsifikation / DATA_INSUFFICIENT

Q024 ist `DATA_INSUFFICIENT`, wenn für den vorab fixierten Mindestanteil der 89
Q019-Events kein reproduzierbarer Result-Publication-Timestamp verfügbar ist oder
die Quelle keine eindeutige Verbindung zwischen Timestamp und dem
`bid_to_cover_ratio` erlaubt.

Empfehlung des Vertrags: vollständige 89/89-Reproduzierbarkeit als Pass-Kriterium.

Der Runner erzwingt genau 89 eindeutige Q019-(CUSIP, auction_date)-Events.
Der festgelegte Timestamp-Pass setzt 89/89 validierte Release-Timestamps
voraus; andernfalls ist der Status `DATA_INSUFFICIENT`. Die PIT-Abdeckung wird
separat je Event ausgegeben und ändert die registrierte 89/89-Timestampregel
nicht.

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
