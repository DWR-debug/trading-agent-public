from __future__ import annotations

import json
from pathlib import Path

from automation.q102_regime_negative_evidence import SOURCE, _load, analyze


def test_q102_identifies_common_mode_regime_directions_without_new_data():
    root = Path(__file__).parents[1]
    source_path = root / SOURCE
    result = analyze(_load(source_path))
    assert result["status"] == "RETROSPECTIVE_REGIME_DIAGNOSTIC_ONLY"
    assert result["method"]["new_market_data"] is False
    assert result["method"]["new_backtest"] is False
    assert result["method"]["candidate_ranking"] is False
    assert result["method"]["performance_authorization"] is False

    states = {row["regime"]: row for row in result["possible_common_mode_states"]}
    assert "DOWNTREND_HIGHVOL" in states
    assert "UPTREND_LOWVOL" in states
    assert states["DOWNTREND_HIGHVOL"]["common_direction"] == "positive"
    assert states["UPTREND_LOWVOL"]["common_direction"] == "negative"


def test_q102_is_deterministic():
    root = Path(__file__).parents[1]
    source_path = root / SOURCE
    a = analyze(_load(source_path))
    b = analyze(_load(source_path))
    assert a["analysis_fingerprint"] == b["analysis_fingerprint"]
