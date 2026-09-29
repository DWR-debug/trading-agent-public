from automation.q091_post_performance_diagnosis import diagnose


def test_q092_diagnosis_is_descriptive_only():
    result = {
        "trial_id": "T-2026-09-29-091",
        "status": "COMPLETED",
        "performance_evaluation": True,
        "holdout_evaluation": True,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "promotion": False,
        "report_fingerprint": "fp",
        "arms": {
            "A": {
                "base": {
                    "research": {"period_return": 0.2, "max_drawdown_percent": 12.0},
                    "holdout": {"period_return": -0.01, "max_drawdown_percent": 11.0, "profit_factor": 0.9},
                    "oos_to_is_return_ratio": -0.05,
                    "rolling_windows": [
                        {"period_return": 0.1},
                        {"period_return": -0.1},
                    ],
                    "rolling_profitable_window_ratio": 0.5,
                    "rolling_average_drawdown_percent": 12.0,
                    "rolling_profit_factor": 1.0,
                    "gates": {"g1": True, "g2": False},
                },
                "stress_1_5x_cost": {"holdout": {"period_return": -0.02}},
                "stress_2x_cost": {"holdout": {"period_return": -0.03}},
                "total_return_sensitivity": {"holdout": {"period_return": 0.0}},
                "turnover": {"mean": 0.1, "sum": 1.0},
                "gates_passed": 1,
                "gates_total": 2,
                "all_gates_passed": False,
            }
        },
    }
    out = diagnose(result)
    assert out["diagnosis_type"] == "post_performance_failure_diagnosis"
    assert out["scientific_status"] == "descriptive_only_no_selection_or_promotion"
    assert out["input_report_fingerprint"] == "fp"
    assert out["method"]["uses_only_persisted_q091_result"] is True
    assert out["method"]["uses_holdout_for_selection"] is False
    assert out["method"]["promotion_decision"] is False
    assert out["method"]["creates_new_performance_evidence"] is False
    assert out["arms"]["A"]["gate_failures"] == ["g2"]
