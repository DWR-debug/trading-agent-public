# Canonical Data Layer

Stand: 2026-09-26

## Zweck

Die Datenebene trennt Datenerfassung von Forschungslogik. Die gemeinsame OHLCV-Coverage- und Snapshot-Geometrie wird nur einmal implementiert.

Kanonischer Ablauf:

    Preregistration
      -> SnapshotSpec
      -> acquisition mit festem Headroom
      -> optionales Study-Window
      -> vollständige Cross-Symbol-Intersection
      -> exakt letzte N gemeinsame Zeitstempel
      -> ausgerichteter Frozen Snapshot
      -> Dataset-Fingerprints
      -> Snapshot-Fingerprint
      -> deterministischer Research Worker

## Vertragsregeln

1. Die Study-Window-Filterung erfolgt vor der Kalenderintersection.
2. Erst die vollständige Intersection bestimmt die verfügbaren gemeinsamen Zeitstempel.
3. Danach werden exakt target_common_candles gemeinsame Zeitstempel ausgewählt.
4. Alle Symbole erhalten exakt dieselbe Zeitachse und dieselbe Anzahl Candles.
5. Bei Coverage-Fehlern werden keine partiellen Snapshot-Artefakte geschrieben.
6. Der Snapshot-Fingerprint enthält nur unveränderliche Identitätsdaten und ist unabhängig vom Ausführungszeitpunkt.
7. Die Schicht berechnet keinerlei Returns, P&L, Performance-Metriken oder Kandidatenauswahl.
8. Holdout-Blindness bleibt Sache des Research-Runners; die Datenebene autorisiert keinen Performance-Lauf.
9. Symbol-Disjointness bleibt vorgelagerte Governance und wird nicht durch die Snapshot-Schicht verändert.
10. Quelle, Universe, Geometrie und Fingerprints bleiben im Manifest nachvollziehbar.

## Gelöste Fehlerklassen

Die zentrale Schicht verhindert systematisch:

- inkonsistente Einzelhistorien,
- zu kleine gemeinsame Kalender,
- unterschiedliche Symbol-Zeitachsen,
- Zuschneiden vor statt nach der Intersection,
- falsche Snapshot-Größe,
- fehlende Fingerprints,
- nutzbare Teilartefakte trotz Coverage-Fehler.

## Migration

automation/coverage_preflight.py soll diese Schicht als einzigen Yahoo-OHLCV-Snapshot-Builder verwenden.

Spezialisierte Quellen wie ALFRED und CFTC behalten ihre quellspezifische PIT-Logik. Yahoo-basierte Research-Lanes werden schrittweise auf denselben Builder umgestellt, bevor neue formale Performance-Läufe autorisiert werden.

## Agenten-Rolle

Der Engineering-Agent kann die Infrastruktur auf einem Feature-Branch implementieren und Regressionstests ergänzen.

Der Research-Reviewer prüft unabhängig:

- Kalender-/Study-Window-Geometrie,
- Disjointness,
- Holdout-Blindness,
- Fingerprint-/Artifact-Provenienz,
- fehlende Performance-Selektion.

Agentenoutput bleibt Design-/Review-Material und ist keine wissenschaftliche Evidence.

## Chat-Kontinuität

Bei einem neuen Projektchat sind zusätzlich zu den kanonischen Statusdateien diese Punkte zu verifizieren:

- docs/CANONICAL_DATA_LAYER.md
- data/canonical_snapshot.py
- aktueller Master-Commit
- letzter Data-Layer-Checkpoint
- offene Infrastruktur-PRs

Damit wird die Datenarchitektur nicht erneut aus Chat-Handoff-Text rekonstruiert.
