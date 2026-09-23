from automation.selection_to_oos_control import _core_window, _verify_core_equivalence


def test_core_equivalence_ignores_only_new_metadata():
    base_window = {
        "window_index": 1,
        "train_size": 20,
        "test_size": 10,
        "step_size": 10,
        "train_start_index": 0,
        "train_end_index": 20,
        "test_start_index": 20,
        "test_end_index": 30,
        "test_start": "2026-01-01T00:00:00",
        "test_end": "2026-01-01T00:09:00",
        "candidate": {"risk_per_trade": 0.01},
        "candidate_fingerprint": "abc",
        "net_profit_eur": 1.0,
        "return_percent": 0.2,
        "win_rate_percent": 50.0,
        "profit_factor": 1.2,
        "max_drawdown_percent": 1.0,
        "sharpe_ratio": 0.4,
        "trade_count": 3,
        "average_trade_eur": 1.0,
        "selection": {"raw_score_rank": 4},
        "training": {"trade_count": 20},
    }

    run_template = {
        "geometry": "small_1125_225",
        "train_size": 20,
        "test_size": 10,
        "step_size": 10,
        "window_count": 1,
        "summary": {"window_count": 1, "total_trade_count": 3},
        "gate": {"name": "rolling_walk_forward", "passed": False, "details": {}},
    }
    source = {
        "datasets": [
            {
                "symbol": "SPY",
                "profiles": [
                    {
                        "selection_profile": "score_max",
                        "small": {**run_template, "windows": [base_window]},
                        "large": {
                            **run_template,
                            "geometry": "large_2250_450",
                            "windows": [],
                        },
                    }
                ],
            }
        ]
    }
    enriched_window = dict(base_window)
    enriched_window["selection"] = {
        "profile_rank": 1,
        "candidate_count": 1280,
        "score": 4.0,
        "raw_score_rank": 4,
        "runner_up_score_gap": 0.2,
        "selected_vs_best_raw_score_gap": -1.0,
    }
    enriched_window["training"] = {
        "net_profit_eur": 8.0,
        "return_percent": 1.6,
        "win_rate_percent": 55.0,
        "profit_factor": 1.4,
        "max_drawdown_percent": 2.0,
        "sharpe_ratio": 0.8,
        "trade_count": 20,
        "average_trade_eur": 0.4,
    }
    enriched = {
        "datasets": [
            {
                "symbol": "SPY",
                "profiles": [
                    {
                        "selection_profile": "score_max",
                        "small": {
                            **run_template,
                            "windows": [enriched_window],
                        },
                        "large": {
                            **run_template,
                            "geometry": "large_2250_450",
                            "windows": [],
                        },
                    }
                ],
            }
        ]
    }

    _verify_core_equivalence(source, enriched)
    assert _core_window(enriched_window)["candidate_fingerprint"] == "abc"


def test_core_equivalence_rejects_changed_oos_result():
    base = {
        "window_index": 1,
        "train_size": 20,
        "test_size": 10,
        "step_size": 10,
        "train_start_index": 0,
        "train_end_index": 20,
        "test_start_index": 20,
        "test_end_index": 30,
        "test_start": "2026-01-01T00:00:00",
        "test_end": "2026-01-01T00:09:00",
        "candidate": {"risk_per_trade": 0.01},
        "candidate_fingerprint": "abc",
        "net_profit_eur": 1.0,
        "return_percent": 0.2,
        "win_rate_percent": 50.0,
        "profit_factor": 1.2,
        "max_drawdown_percent": 1.0,
        "sharpe_ratio": 0.4,
        "trade_count": 3,
        "average_trade_eur": 1.0,
    }
    changed = dict(base)
    changed["net_profit_eur"] = 2.0

    run_template = {
        "geometry": "small_1125_225",
        "train_size": 20,
        "test_size": 10,
        "step_size": 10,
        "window_count": 1,
        "summary": {"window_count": 1, "total_trade_count": 3},
        "gate": {"name": "rolling_walk_forward", "passed": False, "details": {}},
    }
    source = {
        "datasets": [
            {
                "symbol": "SPY",
                "profiles": [
                    {
                        "selection_profile": "score_max",
                        "small": {**run_template, "windows": [base]},
                        "large": {
                            **run_template,
                            "geometry": "large_2250_450",
                            "windows": [],
                        },
                    }
                ],
            }
        ]
    }
    enriched = {
        "datasets": [
            {
                "symbol": "SPY",
                "profiles": [
                    {
                        "selection_profile": "score_max",
                        "small": {**run_template, "windows": [changed]},
                        "large": {
                            **run_template,
                            "geometry": "large_2250_450",
                            "windows": [],
                        },
                    }
                ],
            }
        ]
    }

    try:
        _verify_core_equivalence(source, enriched)
    except RuntimeError:
        return

    raise AssertionError("Geänderter OOS-Befund wurde nicht erkannt.")


tests = [
    (
        "test_core_equivalence_ignores_only_new_metadata",
        test_core_equivalence_ignores_only_new_metadata,
    ),
    (
        "test_core_equivalence_rejects_changed_oos_result",
        test_core_equivalence_rejects_changed_oos_result,
    ),
]

passed = sum(
    1
    for name, test in tests
    if (test() is None)
)

print(f"{passed}/{len(tests)} Selection-to-OOS-Control-Tests bestanden.")
