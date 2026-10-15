import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research/evidence/q220_original_response_body_availability_audit_2026_10_15.json"


def canonical_fingerprint(value):
    payload = dict(value)
    payload.pop("receipt_fingerprint", None)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_q220_body_availability_inventory_is_fingerprint_valid_and_bounded():
    row = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert row["record_type"] == "q220_original_response_body_availability_audit"
    assert row["status"] == "ORIGINAL_DIRECT_PRIMARY_BYTES_NOT_PRESENT_IN_REVIEWED_RETAINED_ARTIFACTS"
    assert row["receipt_fingerprint"] == "9d3bab479450124d07d8f19640aa82fc899c5087b7a630f9c9afea02c56d586c"
    assert canonical_fingerprint(row) == row["receipt_fingerprint"]
    assert row["repository_snapshot"]["commit_sha"] == "dbe45ea03456e4533f7651a40f3f58e8747d810b"
    assert row["repository_snapshot"]["tree_entry_count"] == 3053
    assert row["repository_snapshot"]["tree_truncated"] is False
    assert row["repository_snapshot"]["q220_named_raw_body_file_count"] == 0
    assert row["review_scope"]["network_source_requests_made"] == 0
    assert row["review_scope"]["sec_feed_redownloads"] == 0
    assert row["review_scope"]["direct_primary_document_requests"] == 0
    assert row["review_scope"]["review_is_exhaustive_over_all_actions_history"] is False


def test_q220_original_body_inventory_distinguishes_alternate_submission_blocks():
    row = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    population = next(x for x in row["retained_artifacts"] if x["role"] == "frozen_55_row_population_receipt")
    historic_positive = next(x for x in row["retained_artifacts"] if x["role"] == "historical_positive_independent_reproduction")
    capture = next(x for x in row["retained_artifacts"] if x["role"] == "complete_submission_capture_with_alternate_representation_blocks")
    assert population["contains_raw_direct_primary_bodies"] is False
    assert historic_positive["contains_raw_direct_primary_bodies"] is False
    assert capture["contains_raw_direct_primary_bodies"] is False
    assert capture["contains_complete_submission_txt_bodies"] is False
    assert capture["contains_alternate_route_primary_document_blocks"] is True
    assert len(capture["retained_blocks"]) == 3
    assert all(x["matches_frozen_expected"] is False for x in capture["retained_blocks"])


def test_q220_hashes_and_gates_remain_frozen_and_fail_closed():
    row = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert row["findings"]["expected_hashes_unchanged"] is True
    assert row["findings"]["source_population_unchanged"] is True
    assert row["findings"]["q220_historical_pit_gate_positive"] is False
    assert row["findings"]["q220_independent_reproduction_gate_current"] is False
    assert row["findings"]["historical_source_vintage_proven"] is False
    assert row["findings"]["exact_byte_level_cause_identifiable_from_retained_sources"] is False
    assert row["decision"]["status"] == "RETAIN_PROVENANCE_GAP_NO_FURTHER_IDENTICAL_SOURCE_RERUN"
    assert row["safety"] == {
        "automatic_promotion": False,
        "holdout_selection": False,
        "live_execution": False,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "paid_api_budget_usd": 0,
        "paper_only": True,
        "performance_authorization": False,
        "promotion": False,
        "ranking": False,
        "tuning": False,
    }
