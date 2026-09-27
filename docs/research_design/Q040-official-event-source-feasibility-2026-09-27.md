# Q040 — Official Event-Source PIT Feasibility

**Stand:** 2026-09-27  
**Trial:** T-2026-09-27-062  
**Status:** SOURCE/PIT FEASIBILITY ONLY

## Ziel

Q040 prüft fünf offizielle Datenquellen auf erreichbare Primärdaten und belastbare zeitliche Semantik. Ein vorhandenes Datum wird nicht automatisch als Point-in-Time-Nachweis behandelt.

Wir unterscheiden:

- Referenz-/Beobachtungsdatum
- Record-/Report-Date
- angekündigte Veröffentlichungszeit
- tatsächlichen Annahme-/Publikationszeitpunkt
- spätere Revisionen

## Feste Quellen

**SEC EDGAR:** Submission-Daten enthalten `acceptanceDateTime`. Dieser Zeitpunkt ist der Annahmezeitpunkt des Filings; er darf nicht ungeprüft mit dem ersten öffentlichen Sichtbarkeitszeitpunkt gleichgesetzt werden.

**BLS:** Der offizielle Release-Kalender liefert feste Release-Termine und Uhrzeiten. Für einen echten PIT-Einsatz muss zusätzlich nachgewiesen werden, wann die historischen Werte tatsächlich öffentlich verfügbar waren.

**BEA:** Der offizielle Release Schedule liefert Datum und Uhrzeit. Auch hier gilt: Schedule-Zeit ist nicht automatisch gleich historische Erstverfügbarkeit.

**CFTC:** Report Date und Release-Zeit sind unterschiedliche Konzepte. Ein Report-Date-Datensatz allein genügt nicht als Release-Timestamp.

**TreasuryDirect:** Historische Announcement/Result-Archive sind die Ausgangsquelle; die bereits verifizierte Q023/Q024-Evidence-Kette bleibt für Treasury-Publikationszeit maßgeblich.

## Ergebnislogik

Jeder Source-Pfad erhält einen technischen Access-Status und eine PIT-Feasibility-Klasse. HTTP 403/5xx, Timeout und Netzwerkfehler werden als Zugriffs-/Infrastrukturbeobachtung dokumentiert, nicht als wissenschaftliche Negativ-Evidence.

Q040 erzeugt keine Performance-Evidence, keine Holdout-Auswahl und keine Promotion.
