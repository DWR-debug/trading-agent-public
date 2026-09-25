# Decision Basis — Trading Agent

Stand: 2026-09-25

Diese Datei ist die laufende, chatübergreifende Entscheidungsgrundlage. Nach jedem
abgeschlossenen Research- oder Engineering-Schritt wird sie mit dem verifizierten
neuen Stand aktualisiert. Deskriptive Evidenz, Aussagegrenzen und nächste Aktion
bleiben strikt getrennt.

## Aktueller Stand

### Was ist verifiziert?

- Technische Referenz ist ausschließlich der öffentliche `master` von
  `DWR-debug/trading-agent-public`; Q017 G3 ist in Merge-Commit
  `be558399d2a3a7aa7e5ade58d4f9b4fa603495d9` enthalten.
- Q016 ist technisch abgeschlossen und wissenschaftlich `DATA_INSUFFICIENT`
  mit 0 Beobachtungen und 0 Event-Fenstern; kein Performance-Trial wurde daraus
  autorisiert.
- Q017-G3 wurde vollständig ausgeführt: Coverage-/PIT-Preflight,
  Workflow `36186285814`, Artifact `10887025099`, Result-Fingerprint
  `09e8ceb04b37e55dc3c8cdfe6e0c448b328a2dee0bab7c0b90ab0f8ac02fa850`.
- Q017-G3 ist wissenschaftlich `DATA_INSUFFICIENT`, nicht `NO_SUPPORT`:
  die Resultate enthalten keine Renditeauswertung und keine Holdout-Selektion.
- Macro/ALFRED war wegen Read-Timeout nicht PIT-ready.
- CFTC zeigte umfangreiche historische Report-Daten, aber die tatsächlichen
  historischen Release-Timestamps und Ausnahmen sind mit dem verfügbaren
  Datenvertrag nicht vollständig verifizierbar; daher bleibt die Familie
  PIT-unverifiziert.
- Der Yahoo-Preflight erreichte nur 2.571 gemeinsame Tagesbars; für die meisten
  Symbole lagen innerhalb des fixierten Fensters nur 3.269 Bars vor, während
  CIBR erst 2015 beginnt. Deshalb ist die 3.500-Candle-Geometrie auf diesem
  Universum nicht erfüllbar.
- Die vier performance-validen historischen Trials aus Q010 zeigen positive
  Holdout-Renditen, aber keinen vollständigen Evidence-Gate-Pass; die wiederkehrenden
  Engpässe liegen bei Research-Drawdown, control-relativer Nichtverschlechterung,
  OOS/IS-Stabilität und teilweise Holdout-Risiko.
- Für die breite Suchphase sind 12 Hypothesen ex ante festgelegt. Der Triage-Lauf
  klassifizierte 7 für Coverage, 1 als Control-Replikation, 1 als Coverage-Diagnose,
  2 wegen Data-Contract und 1 wegen Family-Duplikation zum Pruning.

### Was ist unbekannt?

- Ob ALFRED mit einem robusteren, key-freien Vintage-Zugriff reproduzierbar
  verfügbar gemacht werden kann.
- Ob eine belastbare historische CFTC-Release-Timeline rekonstruiert werden kann,
  ohne ex post Terminwissen zu verwenden.
- Welche der sieben für Coverage vorgesehenen orthogonalen Familien einen
  reproduzierbaren, ausreichend informativen Datenvertrag besitzen.
- Ob irgendeine Explorationshypothese nach dem Pruning die unveränderten formalen
  Robustheits-/Risikogates bestehen kann.

### Was hat sich geändert?

- Q017-G3 wechselte von `COVERAGE_PENDING` zu abgeschlossenem
  `DATA_INSUFFICIENT`.
- Die Forschungssteuerung wurde auf `wide search -> aggressive pruning ->
  narrow formal validation` umgestellt.
- Kostenlose Compute-Ressourcen werden primär für breite, günstige Discovery- und
  Coverage-Probes verwendet; formale Performanceauswertungen bleiben auf wenige
  überlebende Kandidaten beschränkt.
- Q017s Yahoo-Geometrieproblem wird nicht rückwirkend „repariert“ und nicht als
  negatives Alpha-Ergebnis interpretiert. Ein geänderter Datenvertrag würde eine
  separate technische/experimentelle Runde erfordern.
- Wiederkehrende risk-adjusted/risk-control Controls werden nicht weiter blind
  innerhalb derselben Family optimiert.

## Nächste Aktion

Die Wide-Search-Lane führt einen festen, holdout-blinden Research-Probe auf einem
eigenständigen historischen Universum durch. Das Rohdatenfenster wurde auf 4.200
Bars erhöht, damit die feste 3.500-Candle-Geometrie nicht an einem unnötig kleinen
Request-Puffer scheitert.

Die breite Phase darf Hypothesen anhand ex ante definierter Coverage-/Plausibilitäts-
und Research-Split-Regeln aggressiv verwerfen. Erst ein verbleibender Kandidat mit
belastbarem Datenvertrag erhält eine eigene Präregistrierung und den vollständigen
formalen Validierungspfad.

### Welche Schutzgrenzen bleiben unverändert?

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `orders_enabled=False`
- `automatic_promotion=False`
- Kein Holdout wird zur Exploration oder Auswahl verwendet.
- Keine Parameter-, Asset-, Feature-, Horizon- oder Threshold-Selektion nach
  Beobachtung eines Ergebnisses.
- Zeit-/Erfolgsdruck erhöht nur Priorisierung und Parallelisierung, niemals
  Evidenzstandard oder finanzielles Risiko.

## Update-Regel

Nach jedem neuen signifikanten Ergebnis werden mindestens diese Felder ersetzt:
**Was wissen wir? — Was wissen wir nicht? — Was ändert sich? — Nächste Aktion —
Welche Schutzgrenzen bleiben unverändert?**
