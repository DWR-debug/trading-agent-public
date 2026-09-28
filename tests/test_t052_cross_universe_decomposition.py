import json
from pathlib import Path

from automation.t052_cross_universe_decomposition import decompose, load_result


def _result():
    false = False
    true = True
    return {
        "trial_id": "T-2026-09-27-052",
        "status": "COMPLETED",
        "report_fingerprint": "f" * 64,
        "governance": {
            "selection_used": false,
            "parameter_search": false,
            "asset_search": false,
            "threshold_search": false,
            "horizon_search": false,
            "variant_search": false,
            "holdout_used_for_selection": false,
            "automatic_promotion": false,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "universes": {
            "T-2026-09-27-049": {
                "trend_sma_50_200": {"gates": {"a": false, "b": false}},
                "cs_momentum_12_1_top2": {"gates": {"a": false, "b": false}},
            },
            "T-2026-09-27-050": {
                "trend_sma_50_200": {"gates": {"a": false, "b": true}},
                "cs_momentum_12_1_top2": {"gates": {"a": false, "b": true}},
            },
        },
    }


def test_cross_universe_shared_is_detected():
    out = decompose(_result())
    assert out["cross_universe_shared_failure_gates"] == ["a"]


def test_within_universe_sleeve_pattern_is_descriptive():
    out = decompose(_result())
    assert out["cross_sleeve"]["T-2026-09-27-049"]["shared_between_sleeves"] == ["a", "b"]
    assert out["cross_sleeve"]["T-2026-09-27-050"]["shared_between_sleeves"] == ["a"]


def test_selection_is_not_used():
    data = _result()
    data["governance"]["selection_used"] = True
    path = Path("t052-cross-universe-bad.json")
    path.write_text(json.dumps(data), encoding="utf-8")
    try:
        load_result(path)
    except ValueError as exc:
        assert "governance" in str(exc)
    else:
        raise AssertionError("selection-enabled result must be rejected")
