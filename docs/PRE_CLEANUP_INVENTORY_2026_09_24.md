# Pre-Cleanup Inventory — 2026-09-24

## Zweck

Diese Bestandsaufnahme hält Objekte fest, die vor einer Bereinigung nicht versehentlich entfernt werden sollen.
Die Inventur ist read-only. Sie führt keine Löschungen durch.

## Formale, dauerhaft zu bewahrende Evidence

- research/evidence/trial_ledger.json
- research/checkpoints/
- docs/trial_*.md
- relevante Workflow-/Artifact-Fingerprints
- Reports und Manifeste, die für historische Reproduktion benötigt werden

Diese Dateien werden nicht aufgrund eines negativen Trials gelöscht.

## Kontext-/Governance-Ebene

- docs/PROJECT_CONTEXT.md
- docs/CHAT_CONTEXT_2026_09_24.md
- docs/PROJECT_CONTEXT_INGESTION.md
- docs/research_archaeology_2026_09_24.md
- research/evidence/project_context.json
- automation/project_integrity_check.py
- .github/workflows/project-integrity.yml

## Branch-Inventur

### Formal relevant / aktiv zu beobachten
- master
- research/trial-034-relative-value-etf-pairs-2026-09-24 — offener PR #147
- governance/project-context-archaeology-2026-09-24 — diese Governance-Arbeit

### Historisch / wahrscheinlich nach Abschluss archivierbar
- archive/trial-032-data-invalid-2026-09-24
- archive/trial-033-data-invalid-2026-09-24

Diese bleiben zunächst erhalten, bis geprüft ist, dass alle nötigen Informationen in Ledger, Reports, Checkpoints und nicht nur im Branch vorhanden sind.

### Scratch-/Preflight-Branches mit besonderer Prüfung
- preflight/trial-032-residual-momentum-2026-09-24
- preflight/trial-033-residual-momentum-2026-09-24
- preflight/trial-032-relative-value-2026-09-24
- preflight/trial-033-relative-value-2026-09-24
- preflight/trial-034-relative-value-2026-09-24

Insbesondere die Residual-Momentum-Zweige waren nicht die formale Trial-Linie und dürfen bei späterer Bereinigung nicht versehentlich als formale Trial-Evidenz interpretiert werden.

## Workflow-Inventur

Beim Öffnen eines Research-PRs werden zahlreiche ältere Research-/Diagnose-Workflows ebenfalls auf dem PR-Branch gestartet, obwohl sie fachlich nicht Teil der Änderung sind.

Das verursacht CI-Kosten, Warteschlangen und verwirrende Fehlermeldungen. Es ist ein CI-Governance-Problem und kein wissenschaftlicher Befund.

Zielzustand: Research-Workflows laufen nur, wenn ihr Trigger fachlich zum jeweiligen Trial gehört, ein relevanter Pfad geändert wurde oder ein allgemeiner Testlauf bewusst angefordert wurde.

## Dateninventur

Vor Löschen oder Neuaufbau von Market-Data-Dateien sind Dataset-Fingerprint, Symbol/Zeitraum, Candle-Anzahl, gemeinsamer Kalender, Manifest-Referenz, Artifact-Referenz und mögliche Wiederverwendung in unabhängigen Validierungen zu prüfen.

T032 und T033 zeigen, warum das wichtig ist: Coverage-Unterschiede können einen Trial bereits vor Performanceauswertung ungültig machen.

## Löschregeln

Eine Datei, ein Branch oder ein Artefakt darf erst als löschbar klassifiziert werden, wenn die dauerhafte Erkenntnis stabil dokumentiert ist, keine formale Provenienz davon abhängt, kein aktiver Workflow/Test darauf verweist und der historische Zustand weiterhin reproduzierbar bleibt.

## Ergebnis

**Noch keine technische Massenbereinigung.**

Zuerst: Kontext stabilisieren → Evidence-Abhängigkeiten erfassen → CI-Fan-out isolieren → Scratch-/Archive-Branches einzeln klassifizieren → erst danach gezielt entfernen.