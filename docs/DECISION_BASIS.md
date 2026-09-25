# Decision Basis — Trading Agent

Stand: 2026-09-25

Diese Datei ist die laufende, chatübergreifende Entscheidungsgrundlage. Nach jedem
abgeschlossenen Research- oder Engineering-Schritt wird sie mit dem verifizierten
neuen Stand aktualisiert. Deskriptive Evidenz, Aussagegrenzen und nächste Aktion
bleiben strikt getrennt.

## Aktueller Stand

### Was ist verifiziert?

- Technische Referenz ist ausschließlich der öffentliche `master` von
  `DWR-debug/trading-agent-public`; Wide-Search Round 002 (H08 volatility-state transition) wurde inzwischen vollständig ausgeführt. Der feste Research-Only-Lauf hatte 316 Ereignisse und wurde mit **PRUNE_NO_RISK_REGIME_SUPPORT** klassifiziert. Der Holdout blieb unberührt; daraus folgt keine Performance-Autorisierung.

H06 sector-neutral residual momentum ist jetzt die aktive orthogonale Coverage-Stufe.

## Nächste Aktion

Zuerst wird die H06-Coverage-/PIT-Evidenz verifiziert. Eine positive Coverage führt nicht automatisch zu einem Performance-Trial; dafür bleibt eine getrennte Präregistrierung und der unveränderte Evidenz-Gate-Pfad erforderlich. Round 002 fokussiert eine ex ante fixierte **volatility-state transition**-Diagnose
als Brücke zwischen Exploration und dem identifizierten Hauptproblem des Projekts:
robuste Risiko-/Regime-Evidenz. Bewertet wird ausschließlich der Research-Split.
Eine positive Exploration wird nicht automatisch zu einem formalem Trial.

Parallel werden ALFRED/CFTC nicht anhand von Performanceergebnissen weiterverfolgt,
sondern erst bei verbesserter PIT-/Datenzugänglichkeit wieder freigegeben.

### Welche Schutzgrenzen bleiben unverändert?

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
