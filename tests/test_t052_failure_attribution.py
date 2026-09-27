import json
from pathlib import Path

from automation.t052_failure_attribution import EXPECTED_CELLS, attribute, load_result


def _result():
    return {
        "trial_id": "T-2026-09-27-052",
        "status": "COMPLETED",
        "code_version": "x",
        "report_fingerprint": "f" * 64,
        "governance": {
            "selection_used": False,
            "holdout_used_for_selection": False,
            "parameter_search": False,
        },
        "universes": {
            "T-2026-09-27-049": {
                "trend_sma_50_200": {
                    "all_gates_passed": False,
                    "gates": {"a": False, "b": True},
                },
                "cs_momentum_12_1_top2": {
                    "all_gates_passed": False,
                    "gates": {"a": False, "b": False},
                },
            },
            "T-2026-09-27-050": {
                "trend_sma_50_200": {
                    "all_gates_passed": False,
                    "gates": {"a": False, "b": True},
                },
                "cs_momentum_12_1_top2": {
                    "all_gates_passed": False,
                    "gates": {"a": False, "b": False},
                },
            },
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def test_fixed_cell_set_and_counts():
    out = attribute(_result())
    assert set(out["cells"]) == EXPECTED_CELLS
    assert out["gate_failure_counts"] == {"a": 4, "b": 2}
    assert out["shared_failures_all_cells"] == ["a"]


def test_load_result_rejects_selection():
    bad = _result()
    bad["governance"]["selection_used"] = True
    path = Path("/tmp/t052-attribution-bad.json")
    path.write_text(json.dumps(bad), encoding="utf-8")
    try:
        load_result(path)
    except ValueError as exc:
        assert "selection_used" in str(exc)
    else:
        raise AssertionError("selection-enabled result must be rejected")


def test_safety_is_preserved():
    out = attribute(_result())
    assert out["safety"]["paper_only"] is True
    assert out["safety"]["live_trading_enabled"] is False
    assert out["safety"]["orders_enabled"] is False
    assert out["safety"]["automatic_promotion"] is False
