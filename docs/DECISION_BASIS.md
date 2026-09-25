# Decision Basis — Trading Agent

Stand: 2026-09-25

Diese Datei ist die laufende, chatübergreifende Entscheidungsgrundlage. Nach jedem
abgeschlossenen Research- oder Engineering-Schritt wird sie mit dem verifizierten
neuen Stand aktualisiert. Deskriptive Evidenz, Aussagegrenzen und nächste Aktion
bleiben strikt getrennt.

## Aktueller Stand

### Was ist verifiziert?

- Technische Referenz ist ausschließlich der öffentliche `master` von
  `DWR-debug/trading-agent-public`; Wide-Search Round 002 ist in
  `6b6124883f4af03037c4c720f70b6e4a3a4976d2` integriert.
- Q016 bleibt `DATA_INSUFFICIENT`; daraus wurde kein Performance-Trial autorisiert.
- Q017-G3 bleibt `DATA_INSUFFICIENT`: Workflow `36186285814`, Artifact
  `10887025099`, Result-Fingerprint
  `09e8ceb04b37e55dc3c8cdfe6e0c448b328a2dee0bab7c0b90ab0f8ac02fa850`.
- Wide-Search Round 001 wurde vollständig ausgeführt: Workflow `36187003417`,
  Artifact `10887060908`, Artifact-Digest
  `sha256:d97eb2a06ee5f5222c4817652642d57d5c5dda2bf2a4bd813c3bcb512c34ba7c`,
  Probe-Fingerprint
  `3c9aa578ca8de7657ebc480b0ec0c4cf26e5285a8d5169daaf940b6e24080f24`.
- Die Triage Round 001 klassifizierte 7 Familien als Coverage-Kandidaten, 1 als
  Control-Replikation, 1 als Coverage-Diagnose, 2 wegen Data-Contract und 1 wegen
  Family-Duplikation zum Pruning.
- Vier konkrete Yahoo-Probes wurden im Research-Split tatsächlich geprüft und
  alle vier aggressiv verworfen. Es wurde weder Holdout verwendet noch ein
  Performance-Trial autorisiert.
- H03 abnormal turnover/liquidity shock: 799 Beobachtungen; Mittelwert insgesamt
  etwa -0,107 %, erste Research-Hälfte etwa +0,034 %, zweite etwa -0,248 %.
  Die Vorzeichen wechselten, daher Pruning.
- H07 cross-asset lead/lag: 14.986 Beobachtungen; Gesamtmittel etwa +0,072 %.
  Beide Research-Hälften waren positiv, aber die erste Hälfte blieb unter dem
  ex ante fixierten Mindestmittel von 0,1 %, daher Pruning.
- H09 gap reversal: 969 Beobachtungen; erste Hälfte etwa +0,517 %, zweite etwa
  -0,357 %. Vorzeichenwechsel, daher Pruning.
- H10 volume-price imbalance: 2.579 Beobachtungen; erste Hälfte etwa +0,019 %,
  zweite etwa -0,077 %. Vorzeichenwechsel und Unterschreitung des Mindestmittels,
  daher Pruning.
- Die vier Pruning-Ergebnisse sind Explorationsbefunde, kein allgemeiner Beweis,
  dass diese Signalideen niemals funktionieren.
- Wide-Search Round 002 (H08 volatility-state transition) ist technisch integriert und per vollständiger CI geprüft; der wissenschaftliche Round-002-Output ist zum Synchronisationszeitpunkt noch nicht verifiziert.

### Was ist unbekannt?

- Ob H06 sector-neutral residual momentum einen belastbaren Datenvertrag ohne
  versteckte Nachschau-Selektion erhält.
- Ob H08 volatility-state transition einen stabilen Research-Split-Effekt zeigt,
  nachdem die Regel ex ante fixiert wurde.
- Ob ALFRED-Vintage-Daten mit reproduzierbarem, robustem Zugriff verfügbar gemacht
  werden können.
- Ob eine historische CFTC-Release-Timeline PIT-sicher rekonstruiert werden kann.
- Ob irgendein Überlebender die unveränderten formalen Risiko-/Robustheitsgates
  bestehen kann.

### Was hat sich geändert?

- Der Forschungsmodus ist jetzt operativ `wide search -> aggressive pruning ->
  narrow formal validation`.
- Round 001 hat vier günstige Yahoo-basierte Mechanismen entfernt, bevor teure
  formale Performanceanalyse begonnen wurde.
- Kein Round-001-Kandidat rechtfertigt derzeit eine formale Validierung.
- Kostenlose Compute-Ressourcen werden für die verbleibenden orthogonalen Familien
  priorisiert; bekannte Datenvertragsprobleme bleiben diagnostic-only.

## Nächste Aktion

Zuerst wird der wissenschaftliche Output von Round 002 aus der dedizierten Ausführung verifiziert. Erst danach wird entschieden, ob die H08-Diagnose die nächste Coverage-/PIT-Stufe erreicht. Round 002 fokussiert eine ex ante fixierte **volatility-state transition**-Diagnose
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
