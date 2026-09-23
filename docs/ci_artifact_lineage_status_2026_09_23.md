# CI Artifact-Lineage-Status — 2026-09-23

## Befund

Drei historische Diagnose-Workflows verwenden fest verdrahtete Quell-Run-IDs, die im öffentlichen Repository nicht mehr vorhanden sind:

- Selection Profile Consensus: Run 35757944587
- Training Selection Stability: Run 35757944587 und Run 35750723097
- Stratified Hypothesis Control: Run 35762937300

Direkte GitHub-API-Prüfungen für diese Runs liefern keinen vorhandenen Workflow-Run. Die daraus entstehenden PR-Fehler sind daher Artifact-Lineage-/CI-Probleme und keine Research-Ergebnisse.

## Maßnahme

Diese drei Workflows sind ab sofort nur noch über workflow_dispatch startbar.

Die Analyseimplementierungen und ihre Quell-Guard-Prüfungen bleiben unverändert. Sobald die zugehörigen Quellartefakte reproduzierbar neu erzeugt und unveränderlich referenziert sind, kann der automatische PR-Trigger in einer separaten CI-Änderung wieder aktiviert werden.

## Sicherheitsregeln

- keine Strategieänderung
- keine Parameteränderung
- keine Datenänderung
- Paper-Only bleibt unverändert
- automatische Research-PR-Gates sollen nur auf reproduzierbar erreichbaren Quellartefakten basieren