import json
from pathlib import Path

from automation.q066_alpha_failure_diagnosis import (
    jaccard,
    classify_regime,
    hhi,
)


def test_q066_preregistration_is_diagnostic_only():
    p = json.loads(
        Path(
            "research/preregistrations/q066_alpha_failure_mechanism_diagnosis_2026_09_28.json"
        ).read_text(encoding="utf-8")
    )
    assert p["status"] == "PREREGISTERED_DIAGNOSTIC_ONLY"
    assert p["governance"]["new_performance_evaluation"] is False
    assert p["governance"]["selection"] is False
    assert p["governance"]["promotion_decision"] is False
    assert p["data_and_reproducibility"]["no_new_market_data"] is True


def test_jaccard_and_hhi_are_deterministic():
    assert jaccard({"A", "B"}, {"B", "C"}) == 1 / 3
    assert jaccard(set(), set()) == 1.0
    assert hhi([0.5, 0.5, 0.0]) == 0.5
    assert hhi([]) == 0.0


def test_regime_requires_prior_lookback():
    market = [0.001] * 400
    labels = classify_regime(market)
    assert labels[:273] == ["UNDEFINED_EARLY"] * 273
    assert labels[273] in {
        "UPTREND_LOWVOL",
        "UPTREND_HIGHVOL",
        "DOWNTREND_LOWVOL",
        "DOWNTREND_HIGHVOL",
    }

# Q066 rerun marker: sleeve-path interface hardened.
