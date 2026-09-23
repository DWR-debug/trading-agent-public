import json

from automation.selection_profile_consensus_analysis import (
    _json_safe,
    _pairwise_agreement,
    _pearson,
)


def test_json_safe_handles_nonfinite_values():
    safe = _json_safe({"x": float("inf"), "y": float("-inf"), "z": float("nan")})
    assert safe == {"x": "inf", "y": "-inf", "z": None}
    json.dumps(safe, allow_nan=False)


def test_pearson_is_deterministic():
    assert _pearson([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == 1.0


def test_pairwise_agreement_counts():
    control = {
        "datasets": [
            {
                "symbol": "SPY",
                "profiles": [
                    {
                        "selection_profile": "boundary_averse",
                        "small": {"windows": [{
                            "window_index": 1,
                            "candidate_fingerprint": "A",
                        }]},
                        "large": {"windows": []},
                    },
                    {
                        "selection_profile": "risk_averse",
                        "small": {"windows": [{
                            "window_index": 1,
                            "candidate_fingerprint": "A",
                        }]},
                        "large": {"windows": []},
                    },
                    {
                        "selection_profile": "score_max",
                        "small": {"windows": [{
                            "window_index": 1,
                            "candidate_fingerprint": "B",
                        }]},
                        "large": {"windows": []},
                    },
                    {
                        "selection_profile": "trade_rich",
                        "small": {"windows": [{
                            "window_index": 1,
                            "candidate_fingerprint": "C",
                        }]},
                        "large": {"windows": []},
                    },
                ],
            }
        ]
    }

    pairs = _pairwise_agreement(control)
    pair_map = {
        (row["profile_a"], row["profile_b"]): row["candidate_agreement_rate"]
        for row in pairs
    }
    assert pair_map[("boundary_averse", "risk_averse")] == 1.0
    assert pair_map[("boundary_averse", "score_max")] == 0.0
    assert pair_map[("risk_averse", "trade_rich")] == 0.0
