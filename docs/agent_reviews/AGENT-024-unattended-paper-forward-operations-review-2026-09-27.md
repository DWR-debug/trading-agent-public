# Technische Review: unbeaufsichtigter Windows-Paper-Forward-Betrieb

**Issue:** #396  
**Taskvertrag:** `TRADING_AGENT_TASK_V1`, `task_id=AGENT-024`  
**Reviewdatum:** 2026-09-27  
**Reviewtyp:** report-only; kein Code-, Workflow-, Research-, Evidence-, Gate- oder
Promotions-Change  
**Geprüfter kanonischer Stand:** `master`, Status-Snapshot
`8778dcf7370769a2afd8ceeec7bee68139c41b6a`  
**Vorläufer:** AGENT-020 / `docs/agent_reviews/AGENT-020-paper-forward-loop-review-2026-09-27.md`

## Ergebnis

**Gesamturteil: Für unbeaufsichtigten Windows-Dauerbetrieb bleibt der
Paper-Forward-Pfad nur bedingt betriebssicher.** Die nach AGENT-020 integrierten
Schutzmaßnahmen trennen Initialisierung und Resume, verhindern parallele
Prozesse mit State-/Receipt-Locks, bewahren eine Initialisierungsmarke und
verknüpfen Feed-Fingerprints mit dem validierten State. Sie bewirken aber weder
eine selbstheilende Feed-Recovery noch einen gemeinsamen atomaren Commit von
State und Receipt. Das Windows-Runbook beschreibt weiterhin einen interaktiven
Python-Prozess und keinen getesteten Task-Scheduler-/Supervisor-Betrieb.

Die Review beschreibt technische Anforderungen und Betriebsgrenzen. Sie ist
keine Research-Evidence, keine Promotion-Empfehlung und keine Autorisierung
für Live-Ausführung.

## Geprüfte Kontrollen und Grenzen

- `automation/paper_forward_loop.py`
- `automation/paper_forward_market_feed.py`
- `automation/paper_forward_shadow.py`
- `docs/PAPER_FORWARD_WINDOWS_RUNBOOK.md`
- AGENT-020-Review und aktueller operativer Status

Der Forward-Pfad ruft ausschließlich abgeschlossene öffentliche Binance-Candles
ab. Der State wird bei jedem Update einzeln atomar per temporärer Datei und
`os.replace` geschrieben. Die vier Safety-Invarianten werden im Laufzeitpfad
fail-closed geprüft:

```text
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
```

In den geprüften Betriebsflächen gibt es keinen Broker-, Account-Credential-,
Order-, Promotion- oder Research-Evidence-Pfad. Ein Windows-Supervisor darf
diese Trennung nicht durch zusätzliche Integrationen verändern.

## Restbefund F-01 — begrenzte Feed-Recovery und sichere Gap-Recovery

**Bewertung: teilweise bestanden; sicherer Reject, aber keine autonome
Wiederherstellung.**

Der Binance-Loader besitzt eine begrenzte Retry-/Backoff-Strategie für
temporäre HTTP-, Netzwerk- und Timeout-Fehler. Diese Strategie ist eine
Fetch-Recovery, keine Loop-Recovery: Nach erschöpften Retries propagiert der
Fehler aus `update_from_binance` bis `run_loop`, sofern kein äußerer
Supervisor den Prozess neu startet. Ein solcher Neustart behebt auch keine
Lücke, wenn `fetch_limit` beziehungsweise das Abruffenster den Zeitraum seit
dem letzten State-Candle nicht vollständig abdeckt.

Die Gap-Prüfung in `update_session` ist richtig fail-closed: Nicht
kontiguierliche neue Candles werden abgelehnt; fehlende Zwischen-Candles
werden nicht erfunden, übersprungen oder als erfolgreicher Update-Zyklus
verbucht. Der aktuelle Code enthält aber keinen separaten, begrenzten
historischen Catch-up-Pfad. Ein Retry darf deshalb nur denselben zulässigen
Fetch wiederholen; er darf die Kontinuitätsprüfung nicht abschalten und den
State nicht auf einen neuen Bootstrap zurücksetzen.

Für eine spätere Engineering-Umsetzung sind mindestens folgende
Betriebsverträge erforderlich:

1. **Transienter Feed-Fehler:** begrenzte Versuche mit sichtbarem Backoff,
   Fehlerklasse, Versuchszähler und letzter erfolgreicher Candle-Zeit. Nach
   dem Limit bleibt der State unverändert und der Prozess beendet sich mit
   einem nicht erfolgreichen Status oder geht in einen klar markierten
   Recovery-Zustand; kein Erfolg-Fallback.
2. **Gap-Recovery:** ein expliziter, begrenzter Catch-up-Aufruf mit
   Startpunkt `last_market_timestamp + interval`, festem Maximalfenster und
   vollständiger Reihenfolge-/Werte-/Closed-Candle-/Historienprüfung. Jede
   Zwischen-Candle muss vorhanden sein, bevor genau ein gültiger State-Update
   erfolgt.
3. **Nicht recoverbare Lücke:** State, Receipt und Marker bleiben unverändert;
   ein Operator erhält eine eindeutige Meldung mit Session-ID,
   letztem gültigem Timestamp und erforderlicher Recovery-Aktion.
4. **Wiederanlauf:** Supervisor-Restarts dürfen nur dieselbe vorhandene
   Session fortsetzen. Die vorhandene Initialisierungsmarke verhindert bereits
   einen stillen Neustart als neue Session; ein bewusst neuer Lauf muss einen
   neuen State-/Receipt-Pfad verwenden.

## Restbefund F-05 — Windows Supervisor, Task Scheduler und Restart

**Bewertung: nicht als unbeaufsichtigter Betrieb nachgewiesen.**

`PAPER_FORWARD_WINDOWS_RUNBOOK.md` trennt den GitHub-Actions-Runner korrekt vom
lokalen Paper-Forward-Prozess und dokumentiert PowerShell-Aufrufe. Es
definiert jedoch keinen installierten oder getesteten Windows
Task-Scheduler-Task, keinen Dienst, keine Restart-Policy und kein
Shutdown-/Recovery-Protokoll für `paper_forward_loop.py`. Ein
`windows-latest`-Smoke-Test ist ebenfalls kein dauerhafter lokaler
Supervisor.

Ein zulässiges Windows-Betriebsdesign müsste den Prozess als **einen**
dedizierten Task unter einem eigenen, minimal berechtigten lokalen Konto
starten, etwa bei Systemstart oder nach einem kontrollierten Login, mit
Arbeitsverzeichnis und absoluten Pfaden zu einer unveränderlichen
Candidate-Datei. Der Task darf ausschließlich den Python-Paper-Forward-
Prozess und seine lokalen Daten erreichen. Insbesondere dürfen keine
Broker-Credentials, Order-Endpunkte, Account-APIs, Promotion- oder
Research-Evidence-Schreibpfade konfiguriert werden.

Erforderliche Scheduler-/Supervisor-Eigenschaften:

- `StopExisting` beziehungsweise eine äquivalente Einzelinstanz-Garantie;
  die Anwendungssperre bleibt die maßgebliche letzte Kontrolle.
- Restart bei nicht erfolgreichem Prozessende mit begrenztem Backoff und
  Restart-Sturm-Schutz; ein wiederholt scheiternder Prozess muss sichtbar
  `RECOVERY_REQUIRED` bleiben.
- kein Neustart nach normalem, absichtlich kontrolliertem Shutdown ohne
  Betreiberaktion, sofern die Session als beendet markiert wurde.
- definierte Shutdown-Frist: laufender Fetch darf beendet werden, danach
  kein partieller State-Write; der zuletzt atomar gespeicherte State bleibt
  der Recovery-Punkt.
- Windows-Ereignisprotokoll oder append-only Betriebslog mit Start,
  Stop-Grund, Exit-Code, Restart-Zähler, Lock-Konflikten, Feed-Fehlern,
  letzter erfolgreicher Candle und State-/Receipt-Fingerprints.
- lokale Uhrzeit nur für Betriebsmetadaten; Markt-Candle-Timestamps bleiben
  UTC und bestimmen Kontinuität sowie Resume.

Der Scheduler ist damit nur Prozessaufsicht. Er ist kein Trading- oder
Research-Orchestrator und darf keine Entscheidung über Strategie,
Parameter, Asset-Universum, Gates oder Promotion treffen.

## Restbefund F-06 — Receipt-vs-State Commit-Provenienz

**Bewertung: Fingerprint-Zuordnung verbessert; gemeinsamer Commit weiterhin
nicht vorhanden.**

Der aktualisierte State speichert `feed_receipt_fingerprint`,
`feed_candle_fingerprint` und `feed_fetch_fingerprint`. Der Receipt enthält
seinerseits `state_input_fingerprint`. Dadurch kann ein Prüfer feststellen,
ob ein vorhandener Receipt zu dem erwarteten State-Input gehört. Die
State-Validierung rekonstruiert diese Fingerprints und lehnt Manipulationen
ab.

Die Persistenz bleibt dennoch zweistufig: `update_session` schreibt zuerst
den neuen State; erst danach wird die separate Receipt-Datei atomar
ausgetauscht. Fällt der Receipt-Write aus, ist der State bereits gültig
fortgeschrieben, während der Aufrufer einen Fehler erhält. Fällt der Prozess
zwischen den beiden Writes aus, können State und Receipt zeitweise
auseinanderliegen. Die Fingerprints machen diese Situation erkennbar, sie
machen die beiden Dateien nicht zu einer Transaktion.

Der Betriebsvertrag muss deshalb ausdrücklich zwischen zwei Zuständen
unterscheiden:

- **State committed / receipt pending:** der Paper-State ist gültig und darf
  nicht zurückgesetzt oder doppelt verarbeitet werden; der fehlende Receipt
  ist ein sichtbarer Provenienzfehler und muss nachgeholt oder als
  `RECEIPT_RECOVERY_REQUIRED` markiert werden.
- **State und Receipt matched:** State-`input_fingerprint`,
  Receipt-`state_input_fingerprint`, Receipt- und Fetch-Fingerprints stimmen
  überein; erst dann gilt die Fetch-Provenienz als vollständig.

Eine spätere Härtung sollte bevorzugt eine gemeinsame Transaktionseinheit
verwenden, zum Beispiel ein versioniertes Commit-Manifest mit State und
Receipt als Bestandteilen oder ein einzelnes atomar ersetztes Envelope.
Falls die zwei Dateien beibehalten werden, braucht es mindestens einen
Commit-Identifier, erwartete Dateifingerprints, eine Recovery-Markierung und
eine deterministische Reconciliation beim Start. Kein Reconciliation-Pfad
darf einen gültigen State rückwirkend verändern oder eine fehlende Candle
erfinden.

## Logs, Shutdown und Recovery-Backups

Für unbeaufsichtigten Betrieb sind folgende Anforderungen
betriebsnotwendig, nicht optionales Komfortverhalten:

| Bereich | Mindestanforderung |
|---|---|
| Identität | `run_id`, `candidate_id`, `candidate_fingerprint`, State-Pfad und Session-Marker |
| Fortschritt | letzter gültiger Markt-Timestamp, Candle-Anzahl, letzter erfolgreicher Update-Versuch |
| Feed | Endpoint-Klasse, Request-Limit, geschlossene Candle-Anzahl, Retry-/Backoff-Status und Fehlerklasse |
| Provenienz | State-`input_fingerprint`, Feed-/Fetch-/Receipt-Fingerprints und Commit-Status |
| Shutdown | Grund, Signal/Exit-Code, letzter atomarer Commit und ob Recovery erforderlich ist |
| Aufbewahrung | rotierende, begrenzte Logs; ein Fehler darf nicht still überschrieben werden |
| Backup | versionierte Kopie von State, Receipt und Marker in einem zugriffsbeschränkten Verzeichnis |
| Restore | atomar in einen neuen temporären Pfad, Integritätsprüfung, dann kontrollierter Austausch; kein Überschreiben des einzigen Backups |

Backups sind Wiederherstellungsartefakte, keine neue Session und keine
Research-Evidence. Ein Backup darf nur wiederhergestellt werden, wenn
`run_id`, Candidate-Fingerprint, State-Integrität und Receipt-/Commit-Status
zusammenpassen. Alte Backups sind unveränderlich zu behandeln und mit
Zeitstempel/Hash zu referenzieren. Der Backup-Pfad darf nicht mit dem
aktiven State-Pfad verwechselt werden.

## Prüfergebnis nach Zielkriterien

| Prüfkriterium | Ergebnis |
|---|---|
| Begrenzte Feed-Recovery ohne stilles Verschlucken | **Teilweise bestanden:** Loader-Retries vorhanden; Loop-Recovery und sichtbarer Recovery-Zustand fehlen. |
| Sichere Gap-Recovery | **Reject-Sicherheit bestanden, Recovery unvollständig:** Lücken werden abgelehnt; ein expliziter Catch-up-Pfad fehlt. |
| Windows Supervisor/Task Scheduler/Restart | **Nicht nachgewiesen:** Runbook ist interaktiv; kein getesteter unbeaufsichtigter Betriebsvertrag vorhanden. |
| Broker-/Order-/Promotion-Pfade | **Bestanden im geprüften Scope:** keine solchen Pfade; Safety-Invarianten bleiben fail-closed. |
| Receipt-vs-State-Provenienz | **Teilweise bestanden:** Fingerprints sind gebunden; der zweistufige Commit bleibt sichtbar nicht atomar. |
| Logs, Shutdown, Recovery-Backups | **Anforderungen definierbar, nicht vollständig implementiert:** diese Review legt den Mindestvertrag fest. |

## Scope-, Sicherheits- und Verifikationsabschluss

Diese Review ist das einzige vorgesehene Ergebnisartefakt für AGENT-024.
Es wurden keine Code-, Workflow-, Research-, Evidence-, Autorisierungs-,
Gate-, Holdout-, Parameter-, Asset-, Promotion- oder Live-Trading-Dateien
geändert. Es wurde keine deterministische Research-Berechnung und keine
wissenschaftliche Selektion durchgeführt.

Die Review ist eine statische technische Analyse des aktuellen Repository-
Stands und der AGENT-020-Restbefunde. Aussagen über einen konkreten
Windows-PC, dessen Task-Scheduler-Konfiguration, Stromversorgung,
Netzwerkverfügbarkeit oder Live-Runner-Kapazität sind damit nicht verifiziert.

Die unveränderten Sicherheitsinvarianten sind:

```text
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
```

