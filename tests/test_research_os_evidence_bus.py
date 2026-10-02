from __future__ import annotations
import json
from pathlib import Path
import pytest
from automation.research_os_evidence_bus import build_receipt,source_index,validate_receipt
from automation.research_os_scheduler import build_plan
REGISTRY=Path(__file__).resolve().parents[1]/"research/governance/research_os_source_registry_2026_09_30.json"
def test_receipt_is_registry_bound_and_non_authoritative():
    r=json.loads(REGISTRY.read_text(encoding="utf-8")); x=build_receipt(source_id="SRC-SEC-FTD",retrieved_at="2026-09-30T19:00:00Z",raw_payload={"status":200},registry=r)
    assert x["source_url"]==source_index(r)["SRC-SEC-FTD"]["source_url"]
    assert x["scientific_evidence"] is False and x["performance_authorization"] is False and x["holdout_used"] is False
    validate_receipt(x,registry=r)
def test_receipt_rejects_url_drift():
    r=json.loads(REGISTRY.read_text(encoding="utf-8")); x=build_receipt(source_id="SRC-SEC-FTD",retrieved_at="2026-09-30T19:00:00Z",raw_payload={"status":200},registry=r); x["source_url"]="https://example.invalid/drift"
    with pytest.raises(ValueError,match="Source URL drift"): validate_receipt(x,registry=r)
def test_scheduler_is_ex_ante_and_two_lane_capped():
    p=build_plan(run_number=1); assert len(p["assignments"])<=2; assert p["resource_policy"]["maximum_deterministic_lanes"]==2; assert p["resource_policy"]["performance_authorization"] is False
    assert {"holdout_return","holdout_drawdown","performance_rank"}<=set(p["forbidden_inputs"])
    assert all(x["performance_evaluated"] is False and x["holdout_used"] is False for x in p["tracks"])
def test_scheduler_fingerprint_stable():
    assert build_plan(run_number=7)["fingerprint"]==build_plan(run_number=7)["fingerprint"]
def test_receipt_rejects_future_availability():
    r=json.loads(REGISTRY.read_text(encoding="utf-8"))
    x=build_receipt(
        source_id="SRC-FRED-ALFRED",
        retrieved_at="2026-09-30T19:00:00Z",
        raw_payload={"status":200},
        registry=r,
    )
    x["available_at"]="2026-09-30T20:00:00Z"
    with pytest.raises(ValueError,match="available_at cannot"):
        validate_receipt(x,registry=r)


def test_scheduler_exposes_s10_as_receipt_gated_resource(tmp_path, monkeypatch):
    import automation.research_os_scheduler as scheduler
    receipt = tmp_path / "s10_acceptance_receipt.json"
    receipt.write_text(
        json.dumps({"status": "S10_UTILITY_ACCEPTED"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(scheduler, "S10_ACCEPTANCE_PATH", receipt)
    monkeypatch.setattr(scheduler, "S10_OS_STATUS_PATH", tmp_path / "missing-os-status.json")
    p = scheduler.build_plan(run_number=9)
    s10 = next(item for item in p["agent_resources"] if item["id"] == "S10")
    assert s10["eligible"] is True
    assert s10["receipt_status"] == "S10_UTILITY_ACCEPTED"
    assert s10["formal_evidence_allowed"] is False
    assert s10["performance_authorization"] is False


def test_scheduler_keeps_s10_fail_closed_without_receipt(tmp_path, monkeypatch):
    import automation.research_os_scheduler as scheduler
    missing = tmp_path / "missing-s10-receipt.json"
    monkeypatch.setattr(scheduler, "S10_ACCEPTANCE_PATH", missing)
    monkeypatch.setattr(scheduler, "S10_OS_STATUS_PATH", tmp_path / "missing-os-status.json")
    p = scheduler.build_plan(run_number=10)
    s10 = next(item for item in p["agent_resources"] if item["id"] == "S10")
    assert s10["eligible"] is False
    assert s10["receipt_status"] == "NOT_PRESENT"
