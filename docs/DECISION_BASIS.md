# Decision Basis — Trading Agent

Stand: 2026-09-26

Diese Datei ist die laufende, chatübergreifende Entscheidungsgrundlage. Nach jedem
abgeschlossenen Research- oder Engineering-Schritt wird sie mit dem verifizierten
neuen Stand aktualisiert. Deskriptive Evidenz, Aussagegrenzen und nächste Aktion
bleiben strikt getrennt.

## Aktueller Stand

### Was ist verifiziert?

- Technische Referenz ist ausschließlich der öffentliche `master` von
  `DWR-debug/trading-agent-public`.
- H08 wurde in Wide-Search Round 002 als Research-Only-Diagnose mit 316 Ereignissen
  ausgeführt und nach der festen Regel als `PRUNE_NO_RISK_REGIME_SUPPORT` klassifiziert.
- H06 sector-neutral residual momentum wurde auf einem vollständig disjunkten
  Universum als Mechanismus repliziert. Der aktuelle kanonische End-to-End-Lauf
  `36236202675` reproduzierte den bestehenden Ergebnis-Fingerprint
  `45546b7a2b69c39f961cab85f9ab091d165f5e9a711777fb23dd717f82fc9fbd`.
  H06 ist damit Mechanismus-Evidence, aber ausdrücklich keine Profitabilitäts-Evidence.
- PR #230 integrierte die H06-Replikation in den kanonischen Datenpfad und wurde als
  `c8b19db5ed1fa22da67abdba2f070914c0d1a70a` gemergt.
- Q017-G3 ist `DATA_INSUFFICIENT`. Es gab keine Performanceauswertung.
  Der Yahoo-Coverage-Pfad wurde inzwischen auf `data/canonical_snapshot.py`
  vereinheitlicht; PR #234 ist als `cfdb0ac7031cfdadcbfe16da50cbedeb4b285dd3` gemergt.
- Q018 ist als `DESIGN_ONLY` preregistriert und enthält drei bewusst ungerankte,
  mechanistisch unterschiedliche offizielle Event-Informationsquellen.

## Was wissen wir nicht?

- Ob einer der Q018-Kandidaten einen vollständigen, reproduzierbaren
  historischen Daten-/PIT-Vertrag erfüllt.
- Ob ein source-feasibility-passender Kandidat später die unveränderten
  Performance-Gates auf einem neuen disjunkten Universum erfüllen kann.
- Ob die historische Abdeckung und deterministische Parsbarkeit von SEC Form 4,
  FOMC-Entscheidungen und Treasury-10Y-Auktionsergebnissen aus kostenlosen
  offiziellen Quellen vollständig reproduzierbar ist.

## Was ändert sich?

Die Forschungsmaschine wechselt nach dem Abschluss von H06 von der Mechanismus-Replikation
zur **source-first feasibility** für orthogonale offizielle Eventdaten. Q017 wird nicht
durch Asset-, Parameter- oder Regeländerungen gerettet. Ein DATA_INSUFFICIENT-Ergebnis
bleibt ein gültiger Datenvertragsbefund.

## Nächste Aktion

Deterministischen Q018-Source-Feasibility-Preflight für alle drei fixierten Kandidaten
ausführen. Erfasst werden nur Coverage, Point-in-Time-Verfügbarkeit, Parsing,
Provenienz und Datenvollständigkeit. Kein Performance-Trial, keine Kandidatenrangfolge,
keine Holdout-Nutzung.

## Welche Schutzgrenzen bleiben unverändert?

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `ORDERS_ENABLED=False`
- `automatic_promotion=False`
- Kein Holdout wird zur Exploration oder Auswahl verwendet.
- Keine Parameter-, Asset-, Feature-, Horizon- oder Threshold-Selektion nach
  Beobachtung eines Ergebnisses.
- Zeit-/Erfolgsdruck verändert nur Priorisierung und Parallelisierung, niemals
  Evidenzstandard oder finanzielles Risiko.

## Update-Regel

Nach jedem neuen signifikanten Ergebnis werden mindestens diese Felder ersetzt:
**Was wissen wir? — Was wissen wir nicht? — Was ändert sich? — Nächste Aktion —
Welche Schutzgrenzen bleiben unverändert?**


## Q018 Source-Feasibility abgeschlossen — 2026-09-26

Q018 ist als Source-Feasibility-Gate abgeschlossen.

- Workflow: `36237329691`
- Artifact: `10904273903`
- Artifact-Digest: `sha256:f8bfe4e1065d3d8a8b82b08fe4f78f6bd3c006bedf71c8cadc4f512d8d308989`
- Result-Fingerprint: `82b07265b29a93547f2b1547227722005cf9d883baf3ee8b6dc50e029742152d`
- Gesamtstatus: `DATA_INSUFFICIENT`
- SEC Form 4: `DATA_INSUFFICIENT` — HTTP 403 aus GitHub Actions.
- FOMC: `DATA_INSUFFICIENT` — HTTP 403 aus GitHub Actions.
- Treasury 10-Year Auction Data: `COVERAGE_VALIDATED`.
- Keine Performanceauswertung, kein Holdout, keine Kandidatenrangfolge, kein Tuning.

Die SEC/Fed-Befunde sind Ausführungs-/Zugriffsprobleme des aktuellen kostenlosen Runners; sie sind keine Behauptung, dass die offiziellen Quellen selbst nicht existieren.

### Nächste Aktion

Q019 — Treasury Auction Signal Contract. Die einzige source-feasible Q018-Familie wird jetzt objektiv auf Signal-Parsing, Point-in-Time-Mapping und deterministische Ereignisabdeckung geprüft. Das ist kein Performance-Trial und keine nachträgliche Optimierung.


## Q019 abgeschlossen / Q020 gestartet — 2026-09-26

Q019 Treasury Auction Signal/PIT Contract ist **COMPLETED / COVERAGE_VALIDATED**. Der verifizierte Lauf `36238205065` lieferte 89 gemappte Ereignisse und 0 terminale Ereignisse; keine Performanceauswertung und keine Holdout-Nutzung.

Q020 ist **PREREGISTERED_COVERAGE_ONLY** und prüft nun die kanonische OHLCV-Coverage des bereits fixierten Q018-Universums. Bei Nichterfüllung von 3500 gemeinsamen Candles gilt `DATA_INSUFFICIENT`; Assets oder Sample-Geometrie dürfen nicht nachträglich geändert werden.