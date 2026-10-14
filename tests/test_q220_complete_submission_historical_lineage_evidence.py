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

    paths = history["code_path_comparison"]
    assert paths["old_vs_current_population_fetch_function_identical"] is True
    assert paths["fetch_function_contract"]["accept_encoding"] == "identity"
    assert paths["fetch_function_contract"]["retry_attempts"] == 3
    assert paths["current_pit_compiler_fetch_is_separate"] is True
    assert paths["current_pit_compiler_fetch_contract"]["retry_attempts"] == 4
    assert paths["current_pit_compiler_fetch_contract"]["response_fields_embedded_in_hash_failure_receipt"] == [
        "content_type", "content_length_header", "content_encoding",
        "last_modified", "etag", "final_url",
    ]
    assert "requested_url" in paths["current_pit_compiler_fetch_contract"]["response_headers_returned_by_fetch_helper"]
    assert "requested_url" not in paths["current_pit_compiler_fetch_contract"]["response_fields_embedded_in_hash_failure_receipt"]
    assert paths["root_cause_proven"] is False

    historical_independent = history["historical_independent_reproduction"]
    assert historical_independent["receipt_status"] == "Q220_INDEPENDENT_PIT_REPRODUCED"
    assert historical_independent["historical_gate_positive"] is True
    assert historical_independent["record_count"] == 55
    assert historical_independent["independently_retrieved_documents"] == 55
    assert historical_independent["source_hash_failure_count"] == 0
    assert historical_independent["receipt_generated_at_utc"] == "2026-10-11T23:08:31.626126+00:00"
    assert historical_independent["workflow_run"]["id"] == 38183038217
    assert historical_independent["workflow_run"]["conclusion"] == "success"
    assert historical_independent["workflow_run"]["started_at_utc"] == "2026-10-11T23:06:46Z"
    assert historical_independent["workflow_run"]["terminal_updated_at_utc"] == "2026-10-11T23:08:40Z"
    assert historical_independent["immutable_artifact"]["id"] == 11717643698
    assert historical_independent["immutable_artifact"]["sha256"] == (
        "1147d01f71d11c5436b85791bbd4157c8db8fe8d6d11791461627325b6d4477b"
    )
    assert historical_independent["upstream"]["compiler_receipt_fingerprint"] == (
        "1b34b3ac2f3a6fc3ff90fa42cd8ea1c7b73297b5cbd71414a0877bb25d9b203c"
    )
    assert historical_independent["historical_compiler"]["gate_positive"] is True
    assert historical_independent["historical_compiler"]["generated_at_utc"] == (
        "2026-10-11T23:06:37.379425+00:00"
    )
    assert historical_independent["historical_compiler"]["compiler_source_git_blob_sha1"] == (
        "c4587f75551297c1ceae9ed151196681eddfbdb8"
    )
    independent_code = historical_independent["independent_retrieval_source_code"]
    assert independent_code["git_blob_sha1"] == "3a424e17e2ca35b531e48c011480b1b9fab186db"
    assert independent_code["same_blob_at_historical_receipt_and_current_master"] is True
    assert independent_code["user_agent"] == (
        "DWR-debug/trading-agent-public Q220 independent PIT reproduction/1.0 research@example.invalid"
    )
    assert independent_code["accept"] == "text/html,application/xhtml+xml,*/*"
    assert independent_code["max_attempts"] == 3
    assert historical_independent["current_comparison"]["compiler_receipt_fingerprint"] == (
        "b394356b05c0c3e512f750174ffd501aafd9de8809da2266115b57c21d5bb93e"
    )
    assert historical_independent["current_comparison"]["compiler_source_git_blob_sha1"] == (
        "5092a459ce8a976af2a07af926653885a7c86281"
    )
    assert historical_independent["current_comparison"]["source_hash_failure_count"] == 55
    assert historical_independent["current_comparison"]["verified_primary_document_count"] == 0
    assert historical_independent["current_comparison"]["gate_positive"] is False
    assert historical_independent["present_gate_clearance"] is False

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


def test_q220_first_blocked_compiler_receipt_pins_observed_transition_window():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    history = evidence["historical_population_hash_drift"]
    timeline = history["compiler_representation_timeline"]

    positive = timeline["known_positive_compiler_observation"]
    negative = timeline["earliest_known_blocked_observation"]
    window = timeline["first_observed_transition_window"]

    assert positive["workflow_run_id"] == 38182963418
    assert positive["generated_at_utc"] == "2026-10-11T23:06:37.379425Z"
    assert positive["receipt_fingerprint"] == (
        "1b34b3ac2f3a6fc3ff90fa42cd8ea1c7b73297b5cbd71414a0877bb25d9b203c"
    )
    assert positive["compiler_code_sha256"] == (
        "6a8fb9496181fb2a46393d4d9dc348660b068d50255d807401bb8eff0da686ed"
    )
    assert positive["compiler_source_git_blob_sha1"] == (
        "c4587f75551297c1ceae9ed151196681eddfbdb8"
    )
    assert positive["verified_primary_document_count"] == 55
    assert positive["source_hash_failure_count"] == 0
    assert positive["gate_positive"] is True

    assert negative["workflow_run_id"] == 38210402239
    assert negative["receipt_generated_at_utc"] == "2026-10-12T06:00:28.208402Z"
    assert negative["receipt_fingerprint"] == (
        "c9cc85da4e632a801a2cf451ecaf83ae8a375688ea33aad42eaba7eee50e3e5d"
    )
    assert negative["compiler_code_sha256"] == positive["compiler_code_sha256"]
    assert negative["compiler_source_git_blob_sha1"] == positive["compiler_source_git_blob_sha1"]
    assert negative["source_hash_failure_count"] == 55
    assert negative["verified_primary_document_count"] == 0
    assert negative["gate_positive"] is False
    assert negative["artifact_id"] == 11729007177
    assert negative["artifact_sha256"] == (
        "1780ac90f403b977d0f80235964c0d828f89534c701d92ffecf36c564120b778"
    )

    assert window["last_known_positive_compiler_receipt_utc"] == positive["generated_at_utc"]
    assert window["positive_independent_reproduction_receipt_utc"] == (
        "2026-10-11T23:08:31.626126Z"
    )
    assert window["first_known_negative_compiler_receipt_utc"] == negative["receipt_generated_at_utc"]
    assert window["elapsed_from_positive_compiler_receipt_seconds"] == 24_830.828977

    snapshots = timeline["observed_receipt_snapshots"]
    assert len(snapshots) == 9
    assert snapshots[0]["byte_delta_distribution"] is None
    assert snapshots[1]["byte_delta_distribution"] == {"0": 55}
    assert snapshots[3]["byte_delta_distribution"] == {"7": 55}
    assert snapshots[6]["byte_delta_distribution"] == {"-1": 55}
    assert snapshots[-1]["receipt_fingerprint"] == (
        "b394356b05c0c3e512f750174ffd501aafd9de8809da2266115b57c21d5bb93e"
    )
    assert timeline["status"] == "TIME_VARYING_PRIMARY_RESPONSE_REPRESENTATIONS_OBSERVED"
    assert "precise byte-level cause" in timeline["interpretation"]
    assert all(value is False for value in evidence["gates"].values())
    assert evidence["safety"]["live_trading_enabled"] is False
    assert evidence["safety"]["orders_enabled"] is False
