import json

from automation.selection_stability_control import (
    _candidate_key,
    _json_safe,
    _parameter_distance,
)


def test_parameter_distance_is_normalized():
    candidate_a = {
        "risk_per_trade": 0.0025,
        "leverage": 1.0,
        "strategy": {
            "momentum": {"lookback": 3},
            "mean_reversion": {"window": 5, "threshold": 0.01},
        },
    }
    candidate_b = dict(candidate_a)
    candidate_b["leverage"] = 3.0

    assert _candidate_key(candidate_a)[-1] == 1.0
    assert _parameter_distance(candidate_a, candidate_b) == 0.2
    assert _parameter_distance(candidate_a, candidate_a) == 0.0


def test_json_safe_handles_nonfinite_values():
    value = _json_safe({"x": float("inf"), "y": float("nan")})
    assert value == {"x": "inf", "y": None}
    json.dumps(value, allow_nan=False)
