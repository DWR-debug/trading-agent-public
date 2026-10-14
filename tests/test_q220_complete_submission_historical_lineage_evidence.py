from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research/evidence/q220_complete_submission_representation_audit_38619590525.json"


def test_q220_same_code_historical_capture_shows_five_byte_shift_for_all_55_rows():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["record_type"] == "q220_complete_submission_representation_audit_result"
    history = evidence["historical_population_hash_drift"]
    assert history["status"] == "SAME_CODE_FIVE_BYTE_SHIFT_ACROSS_ALL_55_PRIMARY_DOCUMENTS"

    snapshots = {row["commit"]: row for row in history["snapshots"]}
    first = snapshots["65f725a4cde933750d2b06bd4345ab314018bab9"]
    republish = snapshots["7aab3a11af3a533c4ff1078cf303395022614694"]
    second = snapshots["3d41bfbf18e525522da7c274e68ed692ef54c8d1"]

    # The rigorous comparison is 17:19 UTC to 08:24 UTC with the same exact source-code blob.
    assert first["gate_code_sha256"] == second["gate_code_sha256"] == (
        "62ef075c9fe5ccc2527e5a918f9653a5a6d1602359d4bb795a0e97a5370ddcc1"
    )
    assert first["gate_code_git_blob_sha1"] == second["gate_code_git_blob_sha1"] == (
        "17d3464605138e5035718664fb02ff1a56dcf5cc"
    )
    assert republish["source_hash_and_length_set_matches_previous_snapshot"] is True
    assert second["changed_primary_hash_count"] == 55
    assert second["changed_primary_byte_length_count"] == 55
    assert second["primary_byte_delta_distribution"] == {"-5": 55}
    assert second["all_55_hashes_changed"] is True

    field_diff = history["same_code_receipt_diff_field_counts"]
    changed_fields = {row["field"]: row for row in field_diff["fields_changed"]}
    assert changed_fields["header_sha256"]["removed_values"] == 55
    assert changed_fields["header_sha256"]["added_values"] == 55
    assert changed_fields["primary_document_bytes"]["removed_values"] == 55
    assert changed_fields["primary_document_bytes"]["added_values"] == 55
    assert changed_fields["primary_document_sha256"]["removed_values"] == 55
    assert changed_fields["primary_document_sha256"]["added_values"] == 55
    assert field_diff["observed_unchanged_fields"]["directory_index_sha256"] is True
    assert field_diff["observed_unchanged_fields"]["primary_document"] is True
    assert field_diff["observed_unchanged_fields"]["acceptance_datetime"] is True

    samples = {row["record_key"]: row for row in history["same_code_sample_comparisons"]}
    spgi = samples["0000064040|0000064040-19-000059|10-K|2019-02-13"]
    assert spgi["oct10_1719_bytes"] == 4_774_463
    assert spgi["oct11_0824_bytes"] == 4_774_458
    assert spgi["delta_bytes"] == -5
    dvn = samples["0001090012|0001564590-19-003382|10-K|2019-02-20"]
    assert dvn["oct10_1719_bytes"] == 10_558_511
    assert dvn["oct11_0824_bytes"] == 10_558_506
    assert dvn["delta_bytes"] == -5


def test_q220_current_direct_primary_view_remains_a_separate_one_byte_shift_and_blocked():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    history = evidence["historical_population_hash_drift"]
    current = history["current_direct_primary_observations"]
    assert current["total_rows"] == 55
    assert current["current_hashes_differ_from_frozen_count"] == 55
    assert current["current_actual_byte_delta_vs_frozen_distribution"] == {"-1": 55}
    assert current["current_hash_set_matches_frozen_set"] is False

    assert evidence["aggregate_result"]["expected_hash_matches"] == 0
    assert evidence["aggregate_result"]["gate_positive"] is False
    assert all(value is False for value in evidence["gates"].values())
    assert evidence["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
