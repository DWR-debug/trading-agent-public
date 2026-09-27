# Q028 — T052 Cross-Universe vs. Cross-Sleeve Decomposition

Stand: 2026-09-27

## Zweck

Q028 untersucht rein deskriptiv, ob die T052-Gate-Failure-Signaturen innerhalb
eines festen Universums zwischen den beiden Sleeves gemeinsam auftreten und
welche Failure-Gates über beide festen Universen hinweg gemeinsam bleiben.

Quelle ist ausschließlich der unveränderte T052-Resultatdatensatz:
Workflow 36338219883, Artifact 10938097809, Fingerprint
a0a1dc33ce281e7addcf9cf924881b6a30797c1a744d4160fbff91d3384b1b09.

## Vorläufiges Ergebnis

T049:
- Beide Sleeves teilen acht Failure-Gates.
- Nur der SMA-Sleeve hat zusätzlich das Failure-Gate total_return_sensitivity_holdout_nonnegative.

T050:
- Beide Sleeves teilen sechs Failure-Gates.
- Es gibt kein zusätzliches sleeve-spezifisches Failure-Gate.

Über beide Universen und beide Sleeves gemeinsam bleiben fünf Failure-Gates:
- research_drawdown_lte_10pct
- rolling_average_drawdown_lte_10pct
- oos_to_is_return_ratio_gte_0_25
- holdout_profit_factor_gte_1_10
- holdout_drawdown_lte_10pct

Universumspezifisch treten im T049-Muster zusätzlich holdout_return_positive,
stress_1_5x_holdout_nonnegative und stress_2x_holdout_nonnegative auf; im
T050-Muster tritt zusätzlich research_profit_factor_gte_1_10 auf.

Diese Muster sind deskriptiv. Sie beweisen keinen kausalen Universums-, Markt-
oder Regimeeffekt.

## Forschungsfolge

Die Evidenz spricht dafür, die nächsten diagnostischen Arbeiten zunächst auf
gemeinsame Risiko-/Stabilitätsmechanismen und auf mögliche Unterschiede
zwischen den beiden festen Universen zu konzentrieren, statt einen Sleeve
nachträglich auszuwählen oder T052 zu retunen.

Der nächste zulässige Schritt ist eine mechanistische Diagnose mit festem
Quellresultat zu Drawdown-Phasen, Research-to-Holdout-Verschiebung und
Kosten-/Sensitivity-Beiträgen.

## Governance

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
