import json

from automation.q068_fresh_coverage import FROZEN_SYMBOLS
from automation.q068_pipeline_state import summarize


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _prereg(root):
    _write(
        root / "research/preregistrations/q068_performance_2026_09_28.json",
        {
            "status": "PREREGISTERED_PERFORMANCE",
            "symbols": list(FROZEN_SYMBOLS),
            "safety": {
                "paper_only": True,
                "live_trading_enabled": False,
                "orders_enabled": False,
                "automatic_promotion": False,
            },
        },
    )
    _write(root / "research/evidence/trial_ledger.json", {"trials": []})


def _receipt(trial_id, status):
    return {
        "status": status,
        "trial_id": trial_id,
        "performance_trial_authorized": False,
        "selection_used": False,
        "symbols": list(FROZEN_SYMBOLS),
        "result_fingerprint": f"{status}-fp",
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def test_q068_pipeline_blocks_until_both_preflight_receipts_exist(tmp_path):
    _prereg(tmp_path)

    state = summarize(tmp_path)

    assert state["state"] == "PREFLIGHT_BLOCKED"
    assert "coverage receipt missing" in state["blocking_reasons"]
    assert "pit receipt missing" in state["blocking_reasons"]


def test_q068_pipeline_reports_waiting_for_auto_auth_after_both_receipts(tmp_path):
    _prereg(tmp_path)
    _write(
        tmp_path / "research/evidence/q068_coverage_result.json",
        _receipt("T-2026-09-28-068-COVERAGE", "COVERAGE_PASSED"),
    )
    _write(
        tmp_path / "research/evidence/q068_pit_result.json",
        _receipt("T-2026-09-28-068-PIT", "PIT_PASSED"),
    )

    state = summarize(tmp_path)

    assert state["state"] == "PREFLIGHT_PASSED_WAITING_FOR_AUTO_AUTH"
    assert state["blocking_reasons"] == []


def test_q068_pipeline_reports_authorized_only_after_matching_receipts(tmp_path):
    _prereg(tmp_path)
    coverage = _receipt("T-2026-09-28-068-COVERAGE", "COVERAGE_PASSED")
    pit = _receipt("T-2026-09-28-068-PIT", "PIT_PASSED")
    _write(tmp_path / "research/evidence/q068_coverage_result.json", coverage)
    _write(tmp_path / "research/evidence/q068_pit_result.json", pit)
    _write(
        tmp_path / "research/authorizations/q068_performance_2026_09_28.json",
        {
            "authorized": True,
            "performance_execution_authorized": True,
            "execution_scope": "Q068_FIXED_RULE_PERFORMANCE_ONLY",
            "source_receipts": {
                "coverage_result_fingerprint": coverage["result_fingerprint"],
                "pit_result_fingerprint": pit["result_fingerprint"],
            },
            "safety": {
                "PAPER_ONLY": True,
                "LIVE_TRADING_ENABLED": False,
                "ORDERS_ENABLED": False,
                "AUTOMATIC_PROMOTION": False,
            },
        },
    )

    state = summarize(tmp_path)

    assert state["state"] == "PERFORMANCE_AUTHORIZED"
    assert state["blocking_reasons"] == []


def test_q068_pipeline_rejects_mismatched_authorization_fingerprint(tmp_path):
    _prereg(tmp_path)
    coverage = _receipt("T-2026-09-28-068-COVERAGE", "COVERAGE_PASSED")
    pit = _receipt("T-2026-09-28-068-PIT", "PIT_PASSED")
    _write(tmp_path / "research/evidence/q068_coverage_result.json", coverage)
    _write(tmp_path / "research/evidence/q068_pit_result.json", pit)
    _write(
        tmp_path / "research/authorizations/q068_performance_2026_09_28.json",
        {
            "authorized": True,
            "performance_execution_authorized": True,
            "execution_scope": "Q068_FIXED_RULE_PERFORMANCE_ONLY",
            "source_receipts": {
                "coverage_result_fingerprint": "wrong",
                "pit_result_fingerprint": pit["result_fingerprint"],
            },
            "safety": {
                "PAPER_ONLY": True,
                "LIVE_TRADING_ENABLED": False,
                "ORDERS_ENABLED": False,
                "AUTOMATIC_PROMOTION": False,
            },
        },
    )

    state = summarize(tmp_path)

    assert state["state"] == "PREFLIGHT_BLOCKED"
    assert "Q068 performance authorization exists but is invalid" in state["blocking_reasons"]
