# AGENT-007: Review des EUR-2.000-Kandidatenpfads

**Datum:** 2026-09-27  
**Ergebnis:** Technische Härtung umgesetzt; der Workflow blieb unverändert und wurde ausschließlich gelesen.
**Ausgangsrevision:** `36c5e256bcb9708d3250fdf4706d8cb1a3b7a9e1` auf
`agent/AGENT-007-2000-CANDIDATE-copilot-cli`.

## Umfang und Befund

Geprüft wurden der Gate, seine fokussierten Tests, das Kandidatenprotokoll und der Workflow
`paper-2000-candidate.yml`. Es wurden keine Research-Berechnungen, Holdout-Auswertungen,
Kandidatenauswahlen, Parameter-/Asset-/Threshold-/Horizon-Suchen oder Promotionsentscheidungen
vorgenommen.

- **Kandidat / Mehrdeutigkeit:** Das Manifest verlangt weiterhin `frozen=True`,
  `auto_select=False` und `comparison_mode=False`. Der Workflow verarbeitet genau ein JSON-Manifest
  unter `research/paper_candidates_2000/`, bricht bei mehreren ab und überspringt die Ausführung,
  wenn keines vorhanden ist. Keine Vergleichs- oder Auswahl-Logik wurde ergänzt.
- **Eligibility / Holdout:** Der Evidence-Vertrag muss `VALIDATED_PASS` und alle Eligibility-Gates
  bestehen. Das Gate weist nun zusätzlich jeden Wert außer `holdout_used_for_selection is False`
  zurück.
- **Pfadgrenzen:** Manifest-, Evidence- und Return-Stream-Pfade müssen Repository-relativ sein.
  `..`, absolute Pfade und nach Auflösung aus dem Checkout führende Symlinks werden abgewiesen;
  das Manifest muss im vorgesehenen Kandidatenverzeichnis liegen. Die Tests decken Checkout-Flucht
  über Pfad und Symlink ab.
- **Kapital / Safety:** 2.000 EUR sind ausschließlich hypothetisches Referenzkapital; Protokoll
  und Gate-Ausgabe benennen diese Semantik. Der Workflow prüft weiterhin `PAPER_ONLY=True`,
  `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False` und `AUTOMATIC_PROMOTION=False`. Evidence
  mit verletztem Paper-only-/Order-Schutz wird ebenfalls fail-closed abgewiesen.
- **Research-Governance:** Keine Research-Gates, Strategieparameter, Asset-Universen,
  Holdout-Regeln oder Promotion-Regeln wurden geändert. Der Workflow wurde nicht verändert.

## Verifikation und Grenzen

`python -m pytest -q tests/test_paper_candidate_2000_gate.py` wurde nach der Härtung erfolgreich
ausgeführt. Der vorangestellte Regressionstest-Lauf schlug zunächst bei den neu hinzugefügten
Holdout-, Safety- und Pfadfällen fehl und reproduzierte damit die behandelten Lücken.
Ergebnis: **9 passed**. Es wurde kein Research-Artefakt erzeugt.

Der Live-GitHub-Ressourcencheck war nicht zugänglich: `gh auth status`/API lieferte
„Permission denied and could not request permission from user“. Daher konnten laufende Actions,
Self-hosted Runner und aktuelle Agenten-Queue nicht live bestätigt werden. Der aktuelle
Repository-Snapshot wurde als statische Quelle verwendet. Es wurde kein Workflow-Lauf gestartet,
kein Commit erstellt und kein Push oder Pull Request ausgeführt.
