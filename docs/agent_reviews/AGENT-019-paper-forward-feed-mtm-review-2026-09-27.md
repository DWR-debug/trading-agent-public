# AGENT-019 – Unabhängiger technischer Audit von Closed-Candle-Feed und MTM-Ledger

**Issue:** #353  
**Taskvertrag:** `TRADING_AGENT_TASK_V1`, `task_id=AGENT-019`  
**Reviewdatum:** 2026-09-27  
**Reviewtyp:** technische, report-only Prüfung; keine Research-, Gate- oder Promotionsbewertung  
**Geprüfter Stand:** PR #352, Merge-Commit `a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba`; kanonischer Betriebsstand laut `docs/CURRENT_STATUS.md`: `bd262214e20578167bfc16ddbbc0ff494c94e119`

## Ergebnis

Die geprüften Komponenten sind für einen paper-only Shadow/Forward-Pfad grundsätzlich
sauber getrennt. Binance-Candles werden anhand von `open_time + interval <= now`
gefiltert, historische Candles werden beim Update byte-/wertgleich verglichen,
Persistenzdateien werden atomar geschrieben und beim Wiederaufnehmen vollständig
gegen neu berechnete Fingerprints und Portfolio-/Ledgerwerte geprüft. Der Ledger
unterscheidet Cash, realisiertes P&L, unrealisiertes P&L, Gebühren, Marktwert,
MTM-Equity und MTM-Drawdown. Die vier Sicherheitsinvarianten werden beim Start,
Fetch und Update fail-closed geprüft.

**Gesamturteil: technisch belastbar mit zwei mittleren Provenienz-/Kostenrisiken.**
Die Risiken ändern keine historische Evidence, kein Research-Gate und keinen
Live-Pfad. Vor einer Verwendung als streng reproduzierbarer Kosten- oder
Datenprovenienz-Nachweis sollten sie in einer separaten Engineering-Aufgabe
adressiert werden.

## Befunde

### F-01 – Mittleres Risiko: Feed-Receipt und persistierter Ledger sind nicht
verknüpft

**Nachweis:** `automation.paper_forward_market_feed.update_from_binance` erzeugt
ein `FeedReceipt` mit Endpoint, Abrufzeit und Fingerprint der in diesem Fetch
zurückgegebenen geschlossenen Candles. Das Receipt wird nur optional unter
`receipt_path` geschrieben. Der persistierte Shadow-State enthält dagegen nur
den kumulierten `input_fingerprint` und keine Receipt-ID, keinen Fetch-Fingerprint
und keine Receipt-Provenienz.

**Auswirkung:** Ein vorhandenes Receipt beweist nicht, dass genau dieser Fetch
in den gespeicherten Ledger eingegangen ist; umgekehrt kann ein Ledger ohne
Receipt erzeugt werden. Der State selbst bleibt tamper-evident, aber die
Zuordnung zwischen öffentlicher Datenabfrage und Ledger-Update ist nicht
vollständig nachvollziehbar. `fetched_at_utc` macht ein vollständiges Receipt
zudem absichtlich nicht byte-reproduzierbar.

**Empfehlung:** Receipt-Fingerprint bzw. eine unveränderliche, normalisierte
Fetch-Provenienz im State speichern und beim Update verifizieren. Zeitstempel
und volatile Transportmetadaten getrennt vom deterministischen Candle-Hash
behandeln. Keine Änderung an historischen Evidence-Dateien; dies wäre nur eine
neue technische Provenienzschicht.

### F-02 – Mittleres Risiko: Der Forward-Snapshot erzwingt keinen zentralen
Kostenvertrag

**Nachweis:** `_validate_candidate` akzeptiert `fee_rate` und `slippage_rate`
als beliebige endliche, nichtnegative Werte. `_snapshot` verwendet diese Werte
direkt für Entry-/Exit-Gebühren und Slippage. Die vorhandene
`ResearchExecutionCostContract`/`ExecutionCostModel`-Infrastruktur wird vom
Paper-Forward-Shadow nicht auf Kompatibilität geprüft; insbesondere werden
Spread und Short-Borrow-Kosten dort nicht modelliert.

**Auswirkung:** Ein eingefrorener Candidate kann mit Kostenannahmen laufen, die
vom kanonischen Research-Kostenvertrag abweichen, ohne dass der Forward-Pfad
dies als Fehler meldet. Die Berechnung ist innerhalb eines Candidates
deterministisch, aber nicht automatisch vergleichbar mit einem Research-Lauf.
Die vorhandene Gebühr-/Slippage-Rechnung selbst ist intern konsistent:
Entry-Gebühren werden sofort vom Cash abgezogen, Exit-Gebühren und Brutto-P&L
beim Schließen berücksichtigt, und `fees_paid_eur` wird kumuliert.

**Empfehlung:** Für den ausdrücklich autorisierten Kostenvertrag eine
fail-closed Kompatibilitätsprüfung und eine versionierte Kosten-Provenienz im
Candidate verlangen. Falls Forward bewusst einen anderen Vertrag nutzt, muss
das explizit als technische Simulation dokumentiert werden; keine rückwirkende
Änderung von Research-Parametern oder Evidence.

### F-03 – Niedrige Grenze: Closed-Candle-Garantie gilt für Binance-Adapter,
nicht für den allgemeinen Session-Einstieg

**Nachweis:** `fetch_closed_candles` filtert korrekt über
`is_candle_closed(..., now=...)`; `load_binance_history` filtert ebenfalls
geschlossene Candles. `start_session` und `update_session` validieren dagegen
Ordnung, Kontinuität, Werte und historische Unveränderlichkeit, prüfen aber
nicht, ob ein direkt übergebener letzter Timestamp bereits geschlossen ist.

**Auswirkung:** Der öffentliche Binance-Pfad verarbeitet keine ungeschlossene
Candle. Ein lokaler oder anderer Aufrufer kann jedoch den generischen Shadow-
Einstieg mit einer noch offenen Candle verwenden. Das ist eine klare
API-Vertragsgrenze, kein Bypass des Binance-Adapters.

**Empfehlung:** Entweder den generischen Einstieg ausdrücklich als bereits
normalisierte Candle-Schnittstelle dokumentieren oder für den Forward-Modus
eine separate Closed-Candle-Prüfung mit injizierbarer Uhr ergänzen. Die
historische Offline-/Testbarkeit darf dabei nicht durch eine implizite
Echtzeituhr verschlechtert werden.

## Geprüfte Kontrollen

| Kontrollziel | Bewertung | Begründung |
|---|---|---|
| Filterung ungeschlossener Binance-Candles | **Bestanden** | Binance-Kline-Timestamps sind Open-Zeitpunkte; `open + interval <= now` filtert die aktuelle Candle aus. Der Zeitpunkt wird vor dem Request erfasst, was konservativ ist. |
| Historische Inputs unveränderlich | **Bestanden** | Bereits gespeicherte Candles werden wertgleich verglichen; Änderungen, Lücken, Duplikate und nicht-kontiguierliche Anhänge werden abgelehnt. |
| Candidate-/Input-/Signal-Fingerprints | **Bestanden mit F-01** | State-Fingerprints werden beim Resume neu berechnet und geprüft. Die externe Fetch-Receipt ist aber nicht an den State gebunden. |
| Gebühren und Slippage | **Bestanden mit F-02** | Entry und Exit werden separat berechnet und kumuliert; ein zentraler Kostenvertrag wird im Forward-Pfad nicht erzwungen. |
| Offene Position am Snapshot | **Bestanden** | Position, Seite, Menge, Entry-Preis/-Zeit, Exposition und unrealisiertes P&L werden im letzten Ledger-Eintrag und Portfolio gespeichert. |
| Realized vs. unrealized P&L | **Bestanden** | Geschlossene Trades erhöhen `realized_pnl_eur`; offene Positionen bleiben unrealisiert und werden nicht als Trade gezählt. |
| MTM-Equity und Drawdown | **Bestanden mit definierter Semantik** | Equity ist Cash plus Mark-to-Market-P&L; realisierte und MTM-Drawdowns werden getrennt als Peak-basierte Prozentwerte geführt. |
| Reproduzierbarkeit | **Bestanden mit F-01/F-02** | Gleicher Candidate-/Candle-Input erzeugt gleiche Run-, Input- und Signal-Fingerprints; externe Fetch-Zuordnung und Kostenvertrag sind nicht vollständig festgeschrieben. |
| Fehlerzustände | **Bestanden** | Leere/ungültige Daten, IO-/JSON-Fehler, Safety-Abweichungen, Tampering und Kontinuitätsfehler führen zu expliziten Exceptions; keine Erfolg-Fallbacks gefunden. |
| PAPER_ONLY-Grenzen | **Bestanden** | `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False` und `AUTOMATIC_PROMOTION=False` werden fail-closed geprüft; der Feed nutzt nur den öffentlichen Market-Data-Endpunkt. |

## Positive technische Beobachtungen

- Der geschlossene Binance-Pfad führt keine Order- oder Broker-Funktion auf.
- Die Session-Datei wird per temporärer Datei und `os.replace` atomar geschrieben.
- Beim Resume wird nicht nur ein einzelner Hash, sondern der gesamte erwartete
  Snapshot einschließlich Ledger und Portfolio rekonstruiert.
- Ein offener Short bleibt am Snapshot offen; sein unrealisiertes P&L wird nicht
  fälschlich als realisiert oder als abgeschlossener Trade gezählt.
- Der MTM-Drawdown misst die Equity-Kurve, nicht nur abgeschlossene Trades.
- Die Tests decken offene Positionen, persistente Ledger, Tampering, historische
  Änderungen, Datenlücken und alle vier Safety-Invarianten ab.

## Sicherheits- und Scope-Abschluss

Diese Review verändert ausschließlich diese Review-Datei. Es wurden keine
Code-, Workflow-, Evidence-, Autorisierungs-, Gate-, Holdout-, Parameter-,
Asset-, Promotions- oder Live-Trading-Dateien geändert. Es wurde keine
deterministische Research-Berechnung und keine wissenschaftliche Auswahl
durchgeführt.

Die unveränderten Sicherheitsinvarianten sind:

```text
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
```

## Verifikation und Handoff

Die Prüfung erfolgte statisch anhand der kanonischen Statusdateien, der
PR-#352-Komponenten `automation/paper_forward_market_feed.py`,
`automation/paper_forward_shadow.py`, `automation/paper_forward_loop.py`,
der Binance-/Zeit- und Kostenmodule sowie der fokussierten Paper-Forward-,
Binance- und Kosten-Tests. Da der Taskvertrag strikt report-only ist und
keine Code- oder Teständerungen erlaubt, wurde kein deterministischer
Research-Lauf ausgeführt und kein Code verändert.

**Offene Punkte für einen separaten Engineering-Task:** F-01 Receipt-State-
Verknüpfung und F-02 fail-closed Kostenvertragsbindung; F-03 ist eine
bewusste API-Vertragsentscheidung. Diese Review enthält keine Promotion- oder
Research-Empfehlung.
