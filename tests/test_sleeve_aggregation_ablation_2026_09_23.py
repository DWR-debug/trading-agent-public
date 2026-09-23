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


def _metrics(dd, pf):
    return {
        "research_drawdown_percent": dd,
        "rolling_profit_factor": pf,
        "research_gate_pass_count": 0,
    }


def _case_result(trend_dd, trend_pf, mix_dd, mix_pf, cs_dd, cs_pf):
    return {
        "variants": {
            "trend_only_100_0": {"base": _metrics(trend_dd, trend_pf)},
            "equal_weight_50_50": {"base": _metrics(mix_dd, mix_pf)},
            "cross_sectional_only_0_100": {"base": _metrics(cs_dd, cs_pf)},
        }
    }


def test_consensus_uses_only_research_comparison_metrics():
    case_results = {
        "validation_1": _case_result(8.0, 1.12, 12.0, 1.05, 14.0, 1.04),
        "validation_2": _case_result(9.0, 1.11, 13.0, 1.02, 15.0, 1.03),
        "validation_3": _case_result(10.0, 1.10, 12.0, 1.08, 14.0, 1.04),
        "validation_4": _case_result(9.5, 1.09, 12.5, 1.06, 14.5, 1.03),
    }
    result = _consensus(case_results)
    counts = result["replication_counts"]
    assert counts["trend_dominates_mix_on_dd_and_pf"] == 4
    assert counts["cross_sectional_only_dominates_mix_on_dd_and_pf"] == 0
    assert counts["mix_dd_higher_than_both"] == 0
    assert counts["mix_pf_lower_than_both"] == 4
    assert result["decision_rule"].startswith("trend_only_research_contrast_replicated:")
