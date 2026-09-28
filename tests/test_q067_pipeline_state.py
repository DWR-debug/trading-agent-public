import json

from automation.q067_alpha_mechanisms import Q067_SYMBOLS
from automation.q067_pipeline_state import summarize


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _prereg(root):
    _write(
        root / "research/preregistrations/q067_performance_2026_09_28.json",
        {
            "status": "PREREGISTERED_PERFORMANCE",
            "symbols": list(Q067_SYMBOLS),
            "safety": {
                "paper_only": True,
                "live_trading_enabled": False,
                "orders_enabled": False,
                "automatic_promotion": False,
            },
        },
    )
    _write(root / "research/evidence/trial_ledger.json", {"trials": []})


def test_q067_pipeline_blocks_until_both_preflight_receipts_exist(tmp_path):
    _prereg(tmp_path)

    state = summarize(tmp_path)

    assert state["state"] == "PREFLIGHT_BLOCKED"
    assert "coverage receipt missing" in state["blocking_reasons"]
    assert "pit receipt missing" in state["blocking_reasons"]


def test_q067_pipeline_reports_authorized_state_only_after_valid_prerequisites(tmp_path):
    _prereg(tmp_path)
    base_receipt = {
        "status": "COVERAGE_PASSED",
        "trial_id": "T-2026-09-28-067-COVERAGE",
        "performance_trial_authorized": False,
        "selection_used": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    pit_receipt = {
        **base_receipt,
        "status": "PIT_PASSED",
        "trial_id": "T-2026-09-28-067-PIT",
    }
    _write(tmp_path / "research/evidence/q067_coverage_result.json", base_receipt)
    _write(tmp_path / "research/evidence/q067_pit_result.json", pit_receipt)
    _write(
        tmp_path / "research/authorizations/q067_performance_2026_09_28.json",
        {
            "authorized": True,
            "performance_execution_authorized": True,
            "execution_scope": "Q067_FIXED_RULE_PERFORMANCE_ONLY",
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


def test_q067_pipeline_does_not_hide_invalid_authorization(tmp_path):
    _prereg(tmp_path)
    for path, status, trial_id in (
        (
            tmp_path / "research/evidence/q067_coverage_result.json",
            "COVERAGE_PASSED",
            "T-2026-09-28-067-COVERAGE",
        ),
        (
            tmp_path / "research/evidence/q067_pit_result.json",
            "PIT_PASSED",
            "T-2026-09-28-067-PIT",
        ),
    ):
        _write(
            path,
            {
                "status": status,
                "trial_id": trial_id,
                "performance_trial_authorized": False,
                "selection_used": False,
                "safety": {
                    "paper_only": True,
                    "live_trading_enabled": False,
                    "orders_enabled": False,
                    "automatic_promotion": False,
                },
            },
        )
    _write(
        tmp_path / "research/authorizations/q067_performance_2026_09_28.json",
        {"authorized": True, "performance_execution_authorized": False},
    )

    state = summarize(tmp_path)

    assert state["state"] == "PREFLIGHT_BLOCKED"
    assert "Q067 performance authorization exists but is invalid" in state["blocking_reasons"]
