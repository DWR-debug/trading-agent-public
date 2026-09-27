# AGENT-007 — Review des EUR-2.000-Kandidatenpfads

**Datum:** 2026-09-27  
**Ergebnis:** Technische Härtung umgesetzt und auf aktuellen Master portiert.

## Umfang

Geprüft wurden:
- `automation/paper_candidate_2000_gate.py`
- `tests/test_paper_candidate_2000_gate.py`
- `docs/PAPER_2000_CANDIDATE_PROTOCOL.md`
- der Workflow `.github/workflows/paper-2000-candidate.yml` read-only

Die Härtung betrifft ausschließlich Governance-, Safety- und Pfadgrenzen. Es wurden keine
Research-Gates, Strategieparameter, Asset-Universen, Holdout-Regeln oder Promotion-Regeln
geändert.

## Technische Befunde

- Kandidatenmanifest bleibt eingefroren und eindeutig; `frozen=True`, `auto_select=False`
  und `comparison_mode=False` werden fail-closed geprüft.
- Manifest-, Evidence- und Return-Stream-Pfade müssen repository-relativ sein. Absolute Pfade,
  `..` und Symlink-Auflösung außerhalb des Checkouts werden abgewiesen. Das Manifest selbst
  muss unter `research/paper_candidates_2000/` liegen.
- Evidence muss den bestehenden Eligibility-Vertrag erfüllen und `holdout_used_for_selection`
  bleibt zwingend `false`. Paper-only Safety wird aus dem Evidence ebenfalls fail-closed
  geprüft.
- Die EUR 2.000 bleiben ausschließlich hypothetisches Referenzkapital; das 500-EUR-Canary bleibt
  davon getrennt.
- Der formale Workflow wurde nicht verändert.

## Verifikation

Die zugrunde liegende Agenten-Implementierung meldete nach der Härtung **9 fokussierte Tests
erfolgreich**. Die aktuellen Änderungen wurden anschließend auf den aktuellen Master portiert;
der Umfang bleibt auf Gate, Regressionen und Dokumentation begrenzt.

Kein Performance-Run, keine Holdout-Auswahl, kein Tuning, keine Promotion und keine
Live-Ausführung.

Safety:
`PAPER_ONLY=True`
`LIVE_TRADING_ENABLED=False`
`orders_enabled=False`
`automatic_promotion=False`
