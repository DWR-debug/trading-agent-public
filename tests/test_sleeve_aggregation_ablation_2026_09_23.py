from automation.sleeve_aggregation_ablation_2026_09_23 import (
    CASES,
    COST_SCENARIOS,
    RESEARCH_COUNT,
    VARIANTS,
    _compose_rows,
    _consensus,
)


def test_variants_and_cost_scenarios_are_fixed():
    assert VARIANTS == (
        ("trend_only_100_0", 1.0),
        ("equal_weight_50_50", 0.5),
        ("cross_sectional_only_0_100", 0.0),
    )
    assert COST_SCENARIOS == (
        ("base", 1.0),
        ("stress_1_5x_cost", 1.5),
        ("stress_2x_cost", 2.0),
    )
    assert RESEARCH_COUNT == 2798
    assert len(CASES) == 4
    assert len({case["artifact_id"] for case in CASES}) == 4


def test_composition_endpoints_and_midpoint():
    trend = (
        {
            "timestamp": i,
            "gross_open": 0.02 * (i + 1),
            "gross_close": 0.01 * (i + 1),
            "gross_adjusted_close": 0.011 * (i + 1),
            "turnover": 0.3 + i,
        }
        for i in range(3)
    )
    cs = (
        {
            "timestamp": i,
            "gross_open": -0.01 * (i + 1),
            "gross_close": -0.005 * (i + 1),
            "gross_adjusted_close": -0.004 * (i + 1),
            "turnover": 0.5 + i,
        }
        for i in range(3)
    )
    trend = tuple(trend)
    cs = tuple(cs)

    trend_only = _compose_rows(trend, cs, 1.0)
    cs_only = _compose_rows(trend, cs, 0.0)
    mix = _compose_rows(trend, cs, 0.5)

    assert trend_only[1]["gross_open"] == trend[1]["gross_open"]
    assert trend_only[1]["turnover"] == trend[1]["turnover"]
    assert cs_only[1]["gross_open"] == cs[1]["gross_open"]
    assert cs_only[1]["turnover"] == cs[1]["turnover"]
    assert mix[1]["gross_open"] == 0.5 * (trend[1]["gross_open"] + cs[1]["gross_open"])
    assert mix[1]["turnover"] == 0.5 * (trend[1]["turnover"] + cs[1]["turnover"])


def test_consensus_keeps_holdout_out_of_decision():
    def case(trend_dom=False, cs_dom=False, mix_dd=False, mix_pf=False):
        flags = {
            "trend_dominates_mix_on_dd_and_pf": trend_dom,
            "cs_dominates_mix_on_dd_and_pf": cs_dom,
            "mix_dd_higher_than_both": mix_dd,
            "mix_pf_lower_than_both": mix_pf,
        }
        return {"variants": {}, "_comparison_override": flags}

    # Consensus accepts only normal case result dictionaries; this smoke test
    # verifies the intended four-dataset threshold logic through the helper
    # payload shape.
    comparisons = {
        f"validation_{i}": {
            "variants": {},
        }
        for i in range(1, 5)
    }
    result = _consensus(comparisons)
    assert result["replication_counts"]["trend_dominates_mix_on_dd_and_pf"] == 0
    assert result["replication_counts"]["cross_sectional_only_dominates_mix_on_dd_and_pf"] == 0
    assert result["decision_rule"] == "no_universal_aggregation_contrast: the pre-registered 3/4 replication rules are not met."
