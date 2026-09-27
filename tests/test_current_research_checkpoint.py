import json
from pathlib import Path


def test_current_research_checkpoint_contains_t049_t050_t051():
    d=json.loads(Path("research/evidence/current_project_checkpoint.json").read_text(encoding="utf-8"))
    assert d["t049"]["status"]=="COVERAGE_VALIDATED"
    assert d["t050"]["status"]=="COVERAGE_VALIDATED"
    assert d["t051"]["status"]=="PIT_PASSED_NO_PERFORMANCE_EVIDENCE"
    assert d["t051"]["performance_trial_authorized"] is False


def test_decision_basis_current_stage_is_t051_pit_only():
    d=json.loads(Path("research/evidence/decision_basis_latest.json").read_text(encoding="utf-8"))
    assert d["current_stage"]=="T052_FORMAL_EXECUTION_BLOCKED_BY_CI_REGRESSIONS"
    assert d["next_action"].startswith("Repair current CI regressions blocking T052; then rerun the already-authorized fixed-rule T052 performance evaluation")
    assert d["invariants"]=={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}


def test_trial_ledger_contains_new_coverage_and_pit_records_without_promotion():
    d=json.loads(Path("research/evidence/trial_ledger.json").read_text(encoding="utf-8"))
    records={t["trial_id"]:t for t in d["trials"]}
    assert records["T-2026-09-27-049"]["status"]=="coverage_validated"
    assert records["T-2026-09-27-050"]["status"]=="coverage_validated"
    assert records["T-2026-09-27-051"]["status"]=="pit_passed_no_performance_evidence"
    assert records["T-2026-09-27-051"]["outcome"]["performance_authorized"] is False
