from automation.s10_acceptance import evaluate


def good_result():
    rows = [
        {
            "error": None,
            "predicted_label": label,
            "probabilities": {
                "SUPPORTED": 1.0 if label == "SUPPORTED" else 0.0,
                "REFUTED": 1.0 if label == "REFUTED" else 0.0,
                "INSUFFICIENT": 1.0 if label == "INSUFFICIENT" else 0.0,
            },
        }
        for label in ("SUPPORTED", "REFUTED", "INSUFFICIENT") * 12
    ]
    return {
        "status": "BENCHMARK_COMPLETED",
        "corpus": {"cases": 36},
        "metrics": {"n_total": 36, "n_scored": 36, "malformed_or_no_decision": 0},
        "option_order_sensitivity": {"n": 6, "choice_changes": 0, "max_probability_delta": 0.0},
        "environment": {"source_commit": "abc123", "runner_name": "S10-TERMUX"},
        "endpoint": "http://127.0.0.1:8765",
        "worker_output_is_scientific_evidence": False,
        "governance": {
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "raw_predictions": rows,
    }


def test_s10_acceptance_requires_full_typed_benchmark():
    status, checks = evaluate(good_result())
    assert status == "S10_UTILITY_ACCEPTED"
    assert all(checks.values())


def test_s10_acceptance_rejects_malformed_case():
    result = good_result()
    result["raw_predictions"][5]["probabilities"] = {"SUPPORTED": 1.0}
    status, checks = evaluate(result)
    assert status == "S10_UTILITY_NOT_ACCEPTED"
    assert checks["all_36_typed_decisions_valid"] is False


def test_s10_acceptance_rejects_non_loopback_endpoint():
    result = good_result()
    result["endpoint"] = "https://example.invalid"
    status, checks = evaluate(result)
    assert status == "S10_UTILITY_NOT_ACCEPTED"
    assert checks["loopback_endpoint"] is False
