import pytest

from automation.research_evidence import build_evidence_summary


GATE_SCOPES = {
    "data_quality": "dataset_input",
    "backtest": "baseline_sanity",
    "walk_forward": "selected_candidate_oos",
    "rolling_walk_forward": "rolling_selected_candidate_oos",
    "robustness": "selected_candidate_robustness",
    "overfit": "selected_candidate_train_vs_oos",
    "holdout": "selected_candidate_holdout",
}

GATE_NAMES = tuple(GATE_SCOPES)


def _report(
    run_fingerprint: str,
    *,
    profile: str,
    status: str = "BLOCKED",
    gate_results: dict[str, bool] | None = None,
) -> dict:
    if gate_results is None:
        gate_results = {
            name: (status == "PASSED")
            for name in GATE_NAMES
        }

    report = {
        "status": status,
        "run_manifest": {
            "run_fingerprint": run_fingerprint,
        },
        "datasets": [
            {
                "symbol": "TEST",
                "interval": "1h",
                "research_gates": {
                    "status": status,
                    "passed": status == "PASSED",
                    "gates": [
                        {
                            "name": name,
                            "scope": GATE_SCOPES[name],
                            "passed": gate_results[name],
                            "details": {},
                        }
                        for name in GATE_NAMES
                    ],
                },
                "statistical_diagnostics": {
                    "multiple_testing": {
                        "selection_profile": profile,
                    },
                    "permutation": {
                        "positive_tail_probability": 0.031,
                    },
                },
            }
        ],
    }

    from automation.research_workflow import result_fingerprint

    report["result_fingerprint"] = result_fingerprint(report)
    return report


def test_evidence_summary_is_deterministic_for_same_reports():
    reports = (
        _report("run-a", profile="score_max"),
        _report("run-b", profile="boundary_averse"),
    )

    first = build_evidence_summary(reports)
    second = build_evidence_summary(reports)

    assert first == second
    assert len(first["evidence_fingerprint"]) == 64


def test_evidence_summary_tracks_family_scope_and_counts():
    reports = (
        _report("run-a", profile="score_max", status="PASSED"),
        _report("run-b", profile="boundary_averse"),
    )

    summary = build_evidence_summary(reports)

    assert summary["report_count"] == 2
    assert summary["unique_run_count"] == 2
    assert summary["selection_profiles"] == [
        "boundary_averse",
        "score_max",
    ]
    assert summary["dataset_result_count"] == 2
    assert summary["passed_dataset_count"] == 1
    assert summary["blocked_dataset_count"] == 1
    assert summary["evidence_scope"] == "multi_report"
    assert summary["multiple_testing"]["unique_selection_profile_count"] == 2


def test_evidence_summary_aggregates_gate_outcomes():
    reports = (
        _report(
            "run-a",
            profile="score_max",
            gate_results={
                "data_quality": True,
                "backtest": True,
                "walk_forward": False,
                "rolling_walk_forward": False,
                "robustness": True,
                "overfit": False,
                "holdout": True,
            },
        ),
        _report(
            "run-b",
            profile="boundary_averse",
            gate_results={
                "data_quality": True,
                "backtest": False,
                "walk_forward": True,
                "rolling_walk_forward": False,
                "robustness": False,
                "overfit": False,
                "holdout": True,
            },
        ),
    )

    summary = build_evidence_summary(reports)

    gates = {
        item["gate"]: item
        for item in summary["gate_summary"]
    }
    assert gates["data_quality"]["evaluation_count"] == 2
    assert gates["data_quality"]["passed_count"] == 2
    assert gates["data_quality"]["failed_count"] == 0
    assert gates["data_quality"]["pass_rate"] == 1.0

    assert gates["backtest"]["evaluation_count"] == 2
    assert gates["backtest"]["passed_count"] == 1
    assert gates["backtest"]["failed_count"] == 1
    assert gates["backtest"]["pass_rate"] == 0.5

    profile_gates = {
        (item["selection_profile"], item["gate"]): item
        for item in summary["profile_gate_summary"]
    }
    assert profile_gates[("score_max", "backtest")]["passed_count"] == 1
    assert profile_gates[("boundary_averse", "backtest")]["passed_count"] == 0


def test_evidence_summary_rejects_tampered_report():
    report = _report("run-a", profile="score_max")
    report["status"] = "PASSED"

    with pytest.raises(ValueError, match="Fingerprint"):
        build_evidence_summary((report,))


def test_evidence_fingerprint_changes_when_sources_change():
    first = build_evidence_summary(
        (_report("run-a", profile="score_max"),)
    )
    second = build_evidence_summary(
        (_report("run-b", profile="score_max"),)
    )

    assert first["evidence_fingerprint"] != second["evidence_fingerprint"]


def test_empty_evidence_family_is_rejected():
    with pytest.raises(ValueError, match="[Mm]indestens ein"):
        build_evidence_summary(())


def test_selection_profile_metadata_requires_gate_list():
    report = _report("run-a", profile="score_max")
    del report["datasets"][0]["research_gates"]["gates"]

    from automation.research_workflow import result_fingerprint

    report["result_fingerprint"] = result_fingerprint(report)

    with pytest.raises(ValueError, match="Gate-Liste"):
        build_evidence_summary((report,))


def test_evidence_summary_preserves_gate_scopes():
    summary = build_evidence_summary(
        (_report("run-a", profile="score_max"),)
    )

    assert {
        item["gate"]: item["scope"]
        for item in summary["gate_summary"]
    } == GATE_SCOPES


def test_evidence_summary_rejects_missing_gate_scope():
    report = _report("run-a", profile="score_max")
    del report["datasets"][0]["research_gates"]["gates"][0]["scope"]

    from automation.research_workflow import result_fingerprint

    report["result_fingerprint"] = result_fingerprint(report)

    with pytest.raises(ValueError, match="Evidenz-Scope"):
        build_evidence_summary((report,))


def test_evidence_summary_builds_non_exclusive_failure_diagnostics():
    report = _report(
        "run-a",
        profile="score_max",
        gate_results={
            "data_quality": True,
            "backtest": False,
            "walk_forward": False,
            "rolling_walk_forward": False,
            "robustness": False,
            "overfit": False,
            "holdout": False,
        },
    )

    details_by_gate = {
        "backtest": {
            "metrics_valid": True,
            "trade_count": 10,
            "minimum_trades": 2,
            "final_capital_eur": 500.0,
            "max_drawdown_percent": 15.0,
            "maximum_drawdown_percent": 10.0,
        },
        "walk_forward": {
            "metrics_valid": True,
            "oos_trade_count": 10,
            "minimum_oos_trades": 10,
            "oos_net_profit_eur": -2.0,
            "profit_factor": 0.9,
            "minimum_profit_factor": 1.1,
            "oos_max_drawdown_percent": 12.0,
            "maximum_drawdown_percent": 10.0,
        },
        "rolling_walk_forward": {
            "window_count": 5,
            "total_trade_count": 20,
            "minimum_total_trades": 30,
            "total_net_profit_eur": -3.0,
            "overall_profit_factor": 0.8,
            "minimum_profit_factor": 1.1,
            "profitable_window_ratio": 0.2,
            "minimum_profitable_window_ratio": 0.5,
            "zero_trade_window_ratio": 0.0,
            "maximum_zero_trade_window_ratio": 0.25,
            "average_drawdown_percent": 2.0,
            "maximum_drawdown_percent": 10.0,
        },
        "robustness": {
            "variant_count": 6,
            "profitable_variant_count": 1,
            "profitable_variant_ratio": 1 / 6,
            "minimum_profitable_variant_ratio": 0.5,
            "stress_cost_multiplier": 1.5,
            "stressed_net_profit_eur": -1.0,
        },
        "overfit": {
            "train_return_percent": 100.0,
            "oos_return_percent": 5.0,
            "oos_to_is_return_ratio": 0.05,
            "minimum_oos_to_is_return_ratio": 0.25,
        },
        "holdout": {
            "trade_count": 8,
            "minimum_holdout_trades": 10,
            "net_profit_eur": -1.0,
            "profit_factor": 0.9,
            "minimum_profit_factor": 1.1,
            "max_drawdown_percent": 2.0,
            "maximum_drawdown_percent": 10.0,
        },
    }

    for gate in report["datasets"][0]["research_gates"]["gates"]:
        if gate["name"] in details_by_gate:
            gate["details"] = details_by_gate[gate["name"]]

    from automation.research_workflow import result_fingerprint

    report["result_fingerprint"] = result_fingerprint(report)
    summary = build_evidence_summary((report,))

    diagnostics = {
        item["gate"]: item
        for item in summary["failure_diagnostics"]
    }

    assert diagnostics["backtest"]["failure_count"] == 1
    assert diagnostics["backtest"]["criteria"] == [
        {
            "criterion": "drawdown_exceeded",
            "count": 1,
            "failure_rate": 1.0,
        }
    ]

    rolling = {
        item["criterion"]: item["count"]
        for item in diagnostics["rolling_walk_forward"]["criteria"]
    }
    assert rolling["insufficient_total_trades"] == 1
    assert rolling["non_positive_total_profit"] == 1
    assert rolling["profit_factor_below_minimum"] == 1
    assert rolling["profitable_window_ratio_below_minimum"] == 1

    assert summary["datasets"][0]["failed_criteria"]["overfit"] == [
        "oos_to_is_ratio_below_minimum"
    ]


def test_failure_diagnostics_are_reproducible_and_profile_specific():
    report = _report(
        "run-a",
        profile="risk_averse",
        gate_results={
            "data_quality": True,
            "backtest": False,
            "walk_forward": True,
            "rolling_walk_forward": True,
            "robustness": True,
            "overfit": False,
            "holdout": True,
        },
    )

    backtest = report["datasets"][0]["research_gates"]["gates"][1]
    backtest["details"] = {
        "metrics_valid": True,
        "trade_count": 10,
        "minimum_trades": 2,
        "final_capital_eur": 500.0,
        "max_drawdown_percent": 20.0,
        "maximum_drawdown_percent": 10.0,
    }
    overfit = report["datasets"][0]["research_gates"]["gates"][5]
    overfit["details"] = {
        "train_return_percent": 50.0,
        "oos_return_percent": -2.0,
        "oos_to_is_return_ratio": -0.04,
        "minimum_oos_to_is_return_ratio": 0.25,
    }

    from automation.research_workflow import result_fingerprint

    report["result_fingerprint"] = result_fingerprint(report)

    first = build_evidence_summary((report,))
    second = build_evidence_summary((report,))

    assert first["failure_diagnostics"] == second["failure_diagnostics"]
    profile = {
        (item["selection_profile"], item["gate"]): item
        for item in first["profile_failure_diagnostics"]
    }
    assert profile[("risk_averse", "backtest")]["failure_count"] == 1
    assert profile[("risk_averse", "overfit")]["criteria"][0]["count"] == 1


def test_evidence_summary_includes_candidate_diagnostics():
    report = _report("run-a", profile="score_max")

    dataset = report["datasets"][0]
    dataset["walk_forward"] = {}
    dataset["rolling_walk_forward"] = {}
    dataset["holdout"] = {}
    dataset["optimization_candidate_count"] = 1280
    dataset["optimization_reported_top_n"] = 5

    dataset["walk_forward"].update(
        {
            "selection_profile": "score_max",
            "train_candles": 600,
            "test_candles": 150,
            "selected_candidate": {
                "risk_per_trade": 0.01,
                "leverage": 1.0,
                "strategy": {
                    "momentum": {"lookback": 8},
                    "mean_reversion": {
                        "window": 10,
                        "threshold": 0.02,
                    },
                },
            },
            "test_net_profit_eur": 4.0,
            "test_return_percent": 0.8,
            "test_profit_factor": 1.2,
            "test_max_drawdown_percent": 4.0,
            "test_trade_count": 12,
        }
    )
    dataset["rolling_walk_forward"]["summary"] = {
        "window_count": 5,
        "total_trade_count": 40,
        "total_net_profit_eur": 3.0,
        "overall_profit_factor": 1.2,
        "profitable_window_ratio": 0.6,
        "zero_trade_window_ratio": 0.0,
        "average_drawdown_percent": 2.0,
    }
    dataset["holdout"].update(
        {
            "trade_count": 12,
            "net_profit_eur": 2.0,
            "return_percent": 0.4,
            "profit_factor": 1.2,
            "max_drawdown_percent": 2.0,
            "permutation_positive_tail_probability": 0.04,
        }
    )

    for gate in dataset["research_gates"]["gates"]:
        if gate["name"] == "robustness":
            gate["details"] = {
                "variant_count": 6,
                "profitable_variant_count": 4,
                "profitable_variant_ratio": 2 / 3,
                "minimum_profitable_variant_ratio": 0.5,
                "stress_cost_multiplier": 1.5,
                "stressed_net_profit_eur": 1.0,
            }
        elif gate["name"] == "overfit":
            gate["details"] = {
                "train_return_percent": 20.0,
                "oos_return_percent": 0.8,
                "oos_to_is_return_ratio": 0.04,
                "minimum_oos_to_is_return_ratio": 0.25,
            }

    from automation.research_workflow import result_fingerprint

    report["result_fingerprint"] = result_fingerprint(report)
    summary = build_evidence_summary((report,))

    candidate = summary["candidate_diagnostics"][0]
    assert candidate["selection_profile"] == "score_max"
    assert candidate["optimization_candidate_count"] == 1280
    assert candidate["optimization_reported_top_n"] == 5
    assert candidate["wfo_oos"]["profit_factor"] == 1.2
    assert candidate["rolling_wf"]["profitable_window_ratio"] == 0.6
    assert candidate["robustness"]["profitable_variant_ratio"] == 2 / 3
    assert candidate["overfit"]["oos_to_is_return_ratio"] == 0.04
    assert candidate["holdout"]["permutation_positive_tail_probability"] == 0.04
    assert len(candidate["candidate_fingerprint"]) == 64


def test_evidence_summary_archives_rolling_window_diagnostics():
    report = _report("run-a", profile="score_max")
    dataset = report["datasets"][0]
    selected = {
        "risk_per_trade": 0.01,
        "leverage": 1.0,
        "strategy": {
            "momentum": {"lookback": 8},
            "mean_reversion": {
                "window": 10,
                "threshold": 0.02,
            },
        },
    }
    dataset["walk_forward"] = {
        "selection_profile": "score_max",
        "selected_candidate": selected,
        "train_candles": 600,
        "test_candles": 150,
    }
    dataset["rolling_walk_forward"] = {
        "summary": {
            "window_count": 2,
        },
        "windows": [
            {
                "window_index": 1,
                "selected_candidate": selected,
                "test_net_profit_eur": 1.0,
                "test_return_percent": 0.2,
                "test_profit_factor": 1.2,
                "test_max_drawdown_percent": 2.0,
                "test_trade_count": 5,
            },
            {
                "window_index": 2,
                "selected_candidate": {
                    "risk_per_trade": 0.01,
                    "leverage": 1.0,
                    "strategy": {
                        "momentum": {"lookback": 13},
                        "mean_reversion": {
                            "window": 10,
                            "threshold": 0.02,
                        },
                    },
                },
                "test_net_profit_eur": -1.0,
                "test_return_percent": -0.2,
                "test_profit_factor": 0.8,
                "test_max_drawdown_percent": 1.0,
                "test_trade_count": 4,
            },
        ],
    }
    dataset["holdout"] = {}

    from automation.research_workflow import result_fingerprint

    report["result_fingerprint"] = result_fingerprint(report)
    summary = build_evidence_summary((report,))
    windows = summary["candidate_diagnostics"][0]["rolling_wf"]["windows"]

    assert len(windows) == 2
    assert windows[0]["window_index"] == 1
    assert windows[0]["same_as_wfo_candidate"] is True
    assert windows[1]["same_as_wfo_candidate"] is False
    assert windows[0]["test_net_profit_eur"] == 1.0
    assert len(windows[0]["selected_candidate_fingerprint"]) == 64
    assert summary["candidate_diagnostics"][0]["rolling_wf"]["unique_candidate_count"] == 2
