# Full-Validation-Failure-Consensus — 2026-09-23

Dieser Control vergleicht die beiden vollständig disjunkten vollständigen Candidate-Validierungen:

- zweite Validation: Artifact 10740188093
- dritte Validation: Artifact 10745697729

Beide verwenden den unveränderten Candidate und denselben Gate-Vertrag. Der Control wertet nur die bereits festgestellten Reports aus und wählt keine Variante.

## Wiederkehrender Failure-Fingerabdruck

Der prädefinierte gemeinsame Risiko-/Robustheits-Satz lautet:

- Research Maximum Drawdown
- Rolling Profit Factor
- durchschnittlicher Rolling Drawdown
- Holdout Maximum Drawdown

Der Control prüft, ob exakt dieser vierteilige Satz in beiden unabhängigen vollständigen Validierungen erneut durchfällt.

## Bewusst getrennt

Positive Holdout-Rendite und Holdout-Profit-Factor werden separat dokumentiert. Ein positives Holdout-Ergebnis wird nicht mit einer Produktionsfreigabe gleichgesetzt.

Die vorherigen CS-Mechanismus-Controls zeigen zusätzlich universumsabhängige Selektion und nicht-monotone Rangwirkung. Dieser Control verbindet diese Befunde nicht zu einer optimierten Strategie; er markiert nur den gemeinsamen Risiko-Failure über zwei vollständige Sätze.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Parameteränderung
- keine Gate-Änderung