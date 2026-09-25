# Decision Basis — Trading Agent

Stand: 2026-09-25

Diese Datei ist die laufende, chatübergreifende Entscheidungsgrundlage. Nach jedem
abgeschlossenen Research- oder Engineering-Schritt wird sie mit dem verifizierten
neuen Stand aktualisiert. Deskriptive Evidenz, Aussagegrenzen und nächste Aktion
bleiben strikt getrennt.

## Aktueller Stand

### Was ist verifiziert?

- Technische Referenz ist ausschließlich der öffentliche `master` von
  `DWR-debug/trading-agent-public`.
- AGENT-001 wurde gemergt; CI, Projektintegrität, State-Freshness und
  Research-Governance waren auf dem letzten geprüften PR-Stand grün.
- Q016 ist technisch abgeschlossen und wissenschaftlich `DATA_INSUFFICIENT`
  mit 0 Beobachtungen und 0 Event-Fenstern; kein Performance-Trial wurde daraus
  autorisiert.
- Die vier performance-validen historischen Trials, die Q010 untersucht hat,
  zeigen positive Holdout-Renditen, aber keinen vollständigen Evidence-Gate-Pass.
  Wiederkehrende Fehler liegen insbesondere bei Research-Drawdown,
  control-relativer Nichtverschlechterung und OOS/IS-Stabilität.
- Q017 ist als orthogonale Designrunde präregistriert. G3 prüft ausschließlich
  historische Datenabdeckung und Point-in-Time-Tauglichkeit für Macro Surprise,
  CFTC Positioning/Crowding und abnormalen Turnover/Liquiditätsschock.

### Was bedeutet das?

Die aktuelle Forschungsengstelle ist nicht das Auffinden irgendeines positiven
Backtests. Die zentrale offene Frage ist, ob ein mechanistisch neuer Signaltyp
auf frischen Daten mit belastbarer Provenienz überhaupt ausreichend beobachtbar
und anschließend unter den unveränderten Robustheits-/Risikogates testbar ist.

### Was bedeutet es ausdrücklich nicht?

- Positive Holdout-Renditen früherer Trials sind kein Promotionsnachweis.
- Q016 liefert keinen Performance-Effekt.
- Q017-G3 liefert keine Rendite-Evidence.
- Eine Coverage-Lücke ist kein negatives Alpha-Ergebnis.
- Keine Aussage erlaubt eine Prognose künftiger Rendite oder finanzieller Sicherheit.

## Aktuelle Aktion

Q017-G3 wird coverage-first ausgeführt. Erst nach vollständiger Prüfung wird
zwischen weiterführbarer und technisch blockierter Forschung unterschieden.
Es erfolgt keine Performanceauswahl aus Q017-G3.

## Entscheidungsregeln

1. Technische oder Datenfehler werden vor wissenschaftlicher Interpretation behoben
   oder als `DATA_INVALID` dokumentiert.
2. `DATA_INSUFFICIENT` ist ein gültiger Fortschritt, wenn eine Forschungsrichtung
   belastbar ausgeschlossen oder ihre Unsicherheit reduziert wird.
3. Keine Holdout-, Parameter-, Asset-, Feature-, Horizon- oder Threshold-Selektion
   nach Ergebnisbeobachtung.
4. PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, orders_enabled=False und
   automatic_promotion=False bleiben invariant.
5. Zeit-/Erfolgsdruck erhöht Priorisierung und kostenlose Parallelisierung, niemals
   Beweisnachlass oder finanzielles Risiko.

## Update-Regel

Nach jedem neuen signifikanten Ergebnis werden mindestens diese Felder ersetzt:
**Was wissen wir? — Was wissen wir nicht? — Was ändert sich? — Nächste Aktion —
Welche Schutzgrenzen bleiben unverändert?**
