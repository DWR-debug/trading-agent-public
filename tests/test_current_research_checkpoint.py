import json
from pathlib import Path


def test_current_research_checkpoint_contains_t049_t050_t051():
    d = json.loads(
        Path("research/evidence/current_project_checkpoint.json").read_text(
            encoding="utf-8"
        )
    )
    assert d["t049"]["status"] == "COVERAGE_VALIDATED"
    assert d["t050"]["status"] == "COVERAGE_VALIDATED"
    assert d["t051"]["status"] == "PIT_PASSED_NO_PERFORMANCE_EVIDENCE"
    assert d["t051"]["performance_trial_authorized"] is False


def test_decision_basis_uses_current_schema_and_blocks_promotion():
    d = json.loads(
        Path("research/evidence/decision_basis_latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert d["schema_version"] == "2.1"
    assert d["scientific_status"]["latest_formal_status"] == (
        "PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES"
    )
    assert d["scientific_status"]["performance_authorization_allowed"] is False
    assert d["scientific_status"]["promotion_allowed"] is False
    assert d["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "paid_usage_usd": 0,
    }


def test_trial_ledger_contains_new_coverage_and_pit_records_without_promotion():
    d = json.loads(
        Path("research/evidence/trial_ledger.json").read_text(encoding="utf-8")
    )
    records = {t["trial_id"]: t for t in d["trials"]}
    assert records["T-2026-09-27-049"]["status"] == "coverage_validated"
    assert records["T-2026-09-27-050"]["status"] == "coverage_validated"
    assert records["T-2026-09-27-051"]["status"] == "pit_passed_no_performance_evidence"
    assert records["T-2026-09-27-051"]["outcome"]["performance_authorized"] is False
