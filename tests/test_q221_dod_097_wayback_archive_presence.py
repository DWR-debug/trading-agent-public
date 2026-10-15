import csv
import io
import zipfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from automation import q221_dod_097_wayback_archive_presence as probe

ROOT = Path(__file__).resolve().parents[1]


def _zip_with_csv(rows):
    fields = ["Award ID PIID", "Modification Number", "Action Date", "Recipient UEI", "Awarding Agency Code"]
    payload = io.StringIO(newline="")
    writer = csv.DictWriter(payload, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "Award ID PIID": row["piid"], "Modification Number": row["modification"],
            "Action Date": row["action_date"], "Recipient UEI": row["recipient_uei"],
            "Awarding Agency Code": row.get("agency_code", "097"),
        })
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("FY2025_097_Contracts_Full.csv", payload.getvalue().encode("utf-8"))
    return out.getvalue()


def test_frozen_input_contract_selects_exactly_28_existing_fy2025_dod_rows():
    validated = probe.validate_frozen_inputs(ROOT)
    targets = validated["targets"]
    assert validated["manifest_blob_sha1"] == probe.MANIFEST_BLOB
    assert len(targets) == 28
    assert len({row["transaction_key"] for row in targets}) == 28
    assert all(row["action_date"].startswith("2025-") for row in targets)
    assert all(row["awarding_agency"] == "Department of Defense" for row in targets)
    assert all(row["agency_exception_class"] == "DOD_90_DAY_EXCEPTION_CANDIDATE" for row in targets)
    assert validated["request"]["CENSUS_RESTART"] == "false"
    assert validated["request"]["LIVE_EXECUTION"] == "false"
    assert probe.MAX_REQUESTS == 2
    assert probe.MAX_TOTAL_BYTES == 25_000_000


def test_r2_recovery_is_separately_registered_and_preserves_the_exact_frozen_scope():
    original = probe.validate_frozen_inputs(ROOT)
    recovery = probe.validate_frozen_inputs(ROOT, ROOT / probe.PREREG_PATH_R2, ROOT / probe.REQUEST_PATH_R2)
    assert recovery["request_profile"] == "R2"
    assert recovery["attempt_number"] == 2
    assert recovery["request"]["REQUEST_SEQUENCE"] == probe.R2_REQUEST_SEQUENCE
    assert recovery["preregistration"]["recovery"]["prior_workflow_run_id"] == 38791554425
    assert recovery["preregistration"]["recovery"]["source_request_count_known"] is False
    assert recovery["preregistration"]["recovery"]["archive_outcome_known"] is False
    assert recovery["targets"] == original["targets"]
    assert recovery["manifest_blob_sha1"] == original["manifest_blob_sha1"]
    assert recovery["preregistration_path"] == probe.PREREG_PATH_R2
    assert recovery["request_marker_path"] == probe.REQUEST_PATH_R2
    assert recovery["request"]["LIVE_EXECUTION"] == "false"


def test_r1_and_r2_markers_are_not_interchangeable():
    with pytest.raises(probe.ProbeError, match="marker differs"):
        probe._marker(ROOT / probe.REQUEST_PATH_R2, probe.FROZEN_REQUEST)
    with pytest.raises(probe.ProbeError, match="marker differs"):
        probe._marker(ROOT / probe.REQUEST_PATH, probe.FROZEN_REQUEST_R2)
    with pytest.raises(probe.ProbeError) as exc:
        probe.validate_frozen_inputs(ROOT, ROOT / probe.PREREG_PATH, ROOT / probe.REQUEST_PATH_R2)
    assert exc.value.status == "Q221_DOD_097_PREREGISTRATION_PROFILE_MISMATCH"


def test_frozen_cdx_capture_pin_and_mismatch_fail_closed():
    row = {"timestamp":probe.CAPTURE_TIMESTAMP,"original":probe.ARCHIVE_URL,"statuscode":"200",
           "digest":probe.CDX_SHA1_BASE32,"length":str(probe.CDX_LENGTH)}
    assert probe.verify_pinned_capture([row]) == row
    with pytest.raises(probe.ProbeError, match="digest/length"):
        probe.verify_pinned_capture([{**row,"digest":"WRONG"}])
    with pytest.raises(probe.ProbeError) as missing:
        probe.verify_pinned_capture([])
    assert missing.value.status == "Q221_DOD_097_PINNED_CDX_CAPTURE_COUNT_MISMATCH"


def test_cdx_query_is_bounded_wayback_prefix_not_live_archive_access():
    query = probe.build_cdx_query_url()
    params = parse_qs(urlparse(query).query)
    assert urlparse(query).netloc == "web.archive.org"
    assert params["matchType"] == ["prefix"]
    assert params["limit"] == ["100"]
    assert params["gzip"] == ["false"]
    assert "original:.*097.*Contracts.*zip" in params["filter"]
    assert "files.usaspending.gov/award_data_archive/" in params["url"][0]


def test_schema_parser_reports_snapshot_presence_and_snapshot_only_absences():
    targets = probe.select_frozen_targets(probe._json(ROOT / probe.MANIFEST_PATH))
    observed = probe.inspect_archive_bytes(_zip_with_csv(targets[:1]), targets)
    assert observed["schema_recognized"] is True
    assert observed["matchable_csv_member_count"] == 1
    assert observed["presence_counts"]["present"] == 1
    assert observed["presence_counts"]["absent_from_this_snapshot_only"] == 27
    assert observed["presence_counts"]["ambiguous"] == 0
    assert observed["row_presence"][0]["observation_status"] == "PRESENT_IN_ARCHIVE_SNAPSHOT"
    assert sum(r["observation_status"] == "NOT_FOUND_IN_THIS_ARCHIVE_SNAPSHOT_ONLY" for r in observed["row_presence"]) == 27


def test_duplicate_composite_rows_are_ambiguous_not_positive_evidence():
    targets = probe.select_frozen_targets(probe._json(ROOT / probe.MANIFEST_PATH))
    observed = probe.inspect_archive_bytes(_zip_with_csv([targets[0], targets[0]]), targets)
    assert observed["row_presence"][0]["observation_status"] == "AMBIGUOUS_DUPLICATE_MATCH_IN_ARCHIVE_SNAPSHOT"
    assert observed["presence_counts"]["ambiguous"] == 1
    assert observed["presence_counts"]["present"] == 0


def test_matching_identity_with_other_agency_code_is_not_accepted():
    targets = probe.select_frozen_targets(probe._json(ROOT / probe.MANIFEST_PATH))
    observed = probe.inspect_archive_bytes(_zip_with_csv([{**targets[0],"agency_code":"001"}]), targets)
    assert observed["presence_counts"]["present"] == 0
    assert observed["presence_counts"]["agency_code_mismatch"] == 1
    assert observed["row_presence"][0]["observation_status"] == "IDENTITY_MATCH_BUT_AGENCY_CODE_MISMATCH"


def test_unknown_csv_schema_is_not_reported_as_absence():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("unknown.csv", b"made_up_field,another_field\nx,y\n")
    targets = probe.select_frozen_targets(probe._json(ROOT / probe.MANIFEST_PATH))
    observed = probe.inspect_archive_bytes(out.getvalue(), targets)
    assert observed["schema_recognized"] is False
    assert observed["schema_status"] == "Q221_DOD_097_ARCHIVE_CSV_SCHEMA_UNRECOGNIZED"
    assert observed["row_presence"] == []


def test_non_wayback_hosts_and_redirects_fail_closed():
    with pytest.raises(probe.ProbeError) as exc:
        probe.fetch_wayback_bounded("https://files.usaspending.gov/award_data_archive/fake.zip", {}, 100)
    assert exc.value.status == "Q221_DOD_097_NON_WAYBACK_URL_FORBIDDEN"
    assert probe._NoRedirect().redirect_request(None,None,302,"Found",{},"https://files.usaspending.gov/") is None


def test_receipt_safety_stays_closed():
    receipt = probe._base_receipt()
    for key in ("live_trading_enabled","orders_enabled","historical_first_public_observation_proven",
                "event_level_public_boundary_proven","recipient_to_issuer_mapping_frozen","scientific_evidence",
                "performance_authorization","holdout_selection","ranking","tuning","promotion","live_execution",
                "census_restarted","source_population_changed","source_receipts_modified"):
        assert receipt["safety"][key] is False


def test_workflow_is_master_marker_only_and_one_shot_guarded():
    text = (ROOT / ".github/workflows/q221-dod-097-wayback-archive-presence.yml").read_text(encoding="utf-8")
    triggers = text.split("permissions:",1)[0]
    assert "branches: [master]" in triggers
    assert "research/run_requests/q221_dod_097_wayback_archive_presence.trigger" in triggers
    assert "schedule:" not in triggers
    assert "workflow_dispatch:" not in triggers
    assert "Q221_097_ONE_SHOT_GUARD=PASS" in text
    assert "one-shot source request" in text.lower()
    assert "Ensure a fail-closed fallback receipt exists" in text
    assert "Q221_DOD_097_RECEIPT_PERSISTENCE_FAILED_SOURCE_OUTCOME_UNKNOWN" in text
    assert '"request_count_known": False' in text


def test_r2_workflow_has_its_own_master_only_one_shot_guard_and_marker():
    text = (ROOT / ".github/workflows/q221-dod-097-wayback-archive-presence-r2.yml").read_text(encoding="utf-8")
    triggers = text.split("permissions:", 1)[0]
    assert "branches: [master]" in triggers
    assert "research/run_requests/q221_dod_097_wayback_archive_presence_r2.trigger" in triggers
    assert "schedule:" not in triggers
    assert "workflow_dispatch:" not in triggers
    assert "q221-dod-097-wayback-archive-presence-r2.yml/runs" in text
    assert "Q221_097_ONE_SHOT_GUARD=PASS" in text
    assert "probe_attempt_number" in text
    assert "recovery_of_workflow_run_id" in text
    assert "upload-artifact@v6" in text

 
 
def _write_r2_persistable_receipt(path, *, fallback=False):
    import json
    from automation import q221_dod_097_wayback_receipt_persist as persistence

    if fallback:
        receipt = {
            "schema_version": 1,
            "record_type": "q221_dod_097_wayback_archive_presence_recovery_fallback_receipt",
            "candidate_id": "Q221",
            "probe_attempt_number": 2,
            "recovery_of_workflow_run_id": 38791554425,
            "status": "Q221_DOD_097_RECEIPT_PERSISTENCE_FAILED_SOURCE_OUTCOME_UNKNOWN",
            "source_probe": {
                "request_cap": 2, "request_count": None, "request_count_known": False,
                "response_bytes": None, "responses": [], "response_outcome_known": False,
            },
            "archive_schema_and_row_presence": None,
            "safety": {
                "paper_only": True, "live_trading_enabled": False, "orders_enabled": False,
                "scientific_evidence": False, "performance_authorization": False, "holdout_selection": False,
                "ranking": False, "tuning": False, "promotion": False, "live_execution": False,
            },
        }
    else:
        receipt = probe._base_receipt()
        receipt["source_probe"].update({
            "request_profile": "R2", "one_shot_attempt": 2,
            "preregistration_path": probe.PREREG_PATH_R2,
            "request_marker_path": probe.REQUEST_PATH_R2,
            "request_marker_validated": True, "preregistration_validated": True,
            "request_count": 1, "response_bytes": 10, "responses": [{"http_status": 200}],
        })
    receipt["receipt_fingerprint"] = persistence.canonical_fingerprint(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def test_r2_receipt_persistence_accepts_only_a_pinned_fingerprinted_probe_receipt(tmp_path):
    import json
    from automation import q221_dod_097_wayback_receipt_persist as persistence

    artifact = tmp_path / "artifacts" / "q221-r2"
    artifact.mkdir(parents=True)
    source = artifact / persistence.RECEIPT_FILENAME
    original = _write_r2_persistable_receipt(source)
    result = persistence.persist_receipt(artifact, tmp_path / "evidence", "123456")
    attempt = Path(result["attempt_path"])
    latest = Path(result["latest_path"])
    assert attempt.read_bytes() == source.read_bytes()
    assert latest.read_bytes() == source.read_bytes()
    assert json.loads(attempt.read_text(encoding="utf-8"))["receipt_fingerprint"] == original["receipt_fingerprint"]
    with pytest.raises(persistence.ReceiptPersistenceError) as exc:
        persistence.persist_receipt(artifact, tmp_path / "evidence", "123456")
    assert exc.value.code == "IMMUTABLE_WAYBACK_ATTEMPT_RECEIPT_ALREADY_EXISTS"


def test_r2_receipt_persistence_rejects_bad_fingerprint_and_open_safety_flags(tmp_path):
    from automation import q221_dod_097_wayback_receipt_persist as persistence

    source = tmp_path / persistence.RECEIPT_FILENAME
    receipt = _write_r2_persistable_receipt(source)
    receipt["receipt_fingerprint"] = "0" * 64
    with pytest.raises(persistence.ReceiptPersistenceError, match="canonical fingerprint differs"):
        persistence.validate_receipt(receipt)

    receipt["receipt_fingerprint"] = persistence.canonical_fingerprint(receipt)
    receipt["safety"]["live_trading_enabled"] = True
    receipt["receipt_fingerprint"] = persistence.canonical_fingerprint(receipt)
    with pytest.raises(persistence.ReceiptPersistenceError, match="live_trading_enabled"):
        persistence.validate_receipt(receipt)


def test_r2_receipt_persistence_accepts_fail_closed_unknown_outcome_fallback(tmp_path):
    from automation import q221_dod_097_wayback_receipt_persist as persistence

    source = tmp_path / persistence.RECEIPT_FILENAME
    _write_r2_persistable_receipt(source, fallback=True)
    result = persistence.persist_receipt(tmp_path, tmp_path / "evidence", "654321")
    assert Path(result["attempt_path"]).is_file()
    assert Path(result["latest_path"]).is_file()


def test_r2_receipt_sync_validates_fingerprint_safety_and_persists_immutably():
    text = (ROOT / ".github/workflows/q221-dod-097-wayback-archive-presence-r2-sync.yml").read_text(encoding="utf-8")
    triggers = text.split("permissions:", 1)[0]
    assert "workflow_run:" in triggers
    assert "Q221 DoD 097 Wayback Archive Schema and Row-Presence Probe (Recovery R2)" in triggers
    assert "types: [completed]" in triggers
    assert "github.event.workflow_run.head_branch == 'master'" in text
    assert "conclusion != 'cancelled'" in text
    assert "actions: read" in text
    assert "contents: write" in text
    assert "automation.q221_dod_097_wayback_receipt_persist" in text
    persistence = (ROOT / "automation/q221_dod_097_wayback_receipt_persist.py").read_text(encoding="utf-8")
    assert "canonical_fingerprint" in persistence
    assert "WAYBACK_RECEIPT_FINGERPRINT_MISMATCH" in persistence
    assert "IMMUTABLE_WAYBACK_ATTEMPT_RECEIPT_ALREADY_EXISTS" in persistence
    assert "q221_dod_097_wayback_archive_presence_attempt_" in text
    assert "github_contents_publish.py" in text
    assert '"live_trading_enabled"' in persistence




def test_r3_recovery_uses_a_distinct_preregistration_marker_and_only_changes_timeout():
    r2 = probe.validate_frozen_inputs(
        ROOT, ROOT / probe.PREREG_PATH_R2, ROOT / probe.REQUEST_PATH_R2
    )
    r3 = probe.validate_frozen_inputs(
        ROOT, ROOT / probe.PREREG_PATH_R3, ROOT / probe.REQUEST_PATH_R3
    )
    assert r2["request_timeout_seconds"] == 25
    assert r3["request_timeout_seconds"] == 60
    assert r3["request_profile"] == "R3"
    assert r3["attempt_number"] == 3
    assert r3["request"]["PER_REQUEST_TIMEOUT_SECONDS"] == "60"
    assert r3["request"]["REQUEST_SEQUENCE"] == probe.R3_REQUEST_SEQUENCE
    assert r3["preregistration"]["recovery"]["prior_workflow_run_id"] == 38797148893
    assert r3["preregistration"]["recovery"]["prior_source_request_count"] == 1
    assert r3["preregistration"]["recovery"]["prior_source_request_count_known"] is True
    assert r3["preregistration"]["recovery"]["prior_response_bytes"] == 0
    assert r3["preregistration"]["recovery"]["prior_archive_outcome_known"] is False
    assert r3["preregistration"]["transport_contract"] == {
        "previous_per_request_timeout_seconds": 25,
        "per_request_timeout_seconds": 60,
        "max_source_requests": 2,
        "automatic_retries": 0,
        "alternate_sources_allowed": False,
        "scope_or_caps_changed": False,
    }
    assert r3["targets"] == r2["targets"]
    assert r3["manifest_blob_sha1"] == r2["manifest_blob_sha1"]
    assert r3["preregistration"]["caps"] == r2["preregistration"]["caps"]
    assert r3["request"]["LIVE_EXECUTION"] == "false"


def test_r1_r2_and_r3_request_markers_cannot_be_interchanged():
    with pytest.raises(probe.ProbeError, match="marker differs"):
        probe._marker(ROOT / probe.REQUEST_PATH_R3, probe.FROZEN_REQUEST_R2)
    with pytest.raises(probe.ProbeError, match="marker differs"):
        probe._marker(ROOT / probe.REQUEST_PATH_R2, probe.FROZEN_REQUEST_R3)
    with pytest.raises(probe.ProbeError) as exc:
        probe.validate_frozen_inputs(ROOT, ROOT / probe.PREREG_PATH_R2, ROOT / probe.REQUEST_PATH_R3)
    assert exc.value.status == "Q221_DOD_097_PREREGISTRATION_PROFILE_MISMATCH"


def test_bounded_fetcher_uses_profile_timeout_without_network_access(monkeypatch):
    captured = {}

    class FakeResponse:
        status = 200
        headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, limit):
            captured["read_limit"] = limit
            return b"[]"

    class FakeOpener:
        def open(self, request, timeout):
            captured["timeout"] = timeout
            captured["url"] = request.full_url
            return FakeResponse()

    monkeypatch.setattr(probe.urllib.request, "build_opener", lambda *handlers: FakeOpener())
    state = {
        "request_count": 0, "response_bytes": 0, "responses": [],
        "transport_errors": [], "request_timeout_seconds": 60,
    }
    status, body, headers = probe.fetch_wayback_bounded(probe.build_cdx_query_url(), state, 5_000_000)
    assert status == 200
    assert body == b"[]"
    assert captured["timeout"] == 60
    assert captured["url"].startswith("https://web.archive.org/cdx/search/cdx?")
    assert captured["read_limit"] == 5_000_001
    assert state["request_count"] == 1
    assert state["response_bytes"] == 2


def _write_r3_persistable_receipt(path):
    import json
    from automation import q221_dod_097_wayback_receipt_persist as persistence

    validated = probe.validate_frozen_inputs(
        ROOT, ROOT / probe.PREREG_PATH_R3, ROOT / probe.REQUEST_PATH_R3
    )
    receipt = probe._base_receipt()
    receipt["status"] = "Q221_DOD_097_WAYBACK_TRANSPORT_ERROR"
    receipt["errors"] = [{"code": "Q221_DOD_097_WAYBACK_TRANSPORT_ERROR", "message": "TimeoutError"}]
    receipt["next_gate"] = "Retain blocker; this one-shot authorizes no retry or archive expansion."
    receipt["source_probe"].update({
        "request_sequence": validated["request"]["REQUEST_SEQUENCE"],
        "manifest_blob_sha1_verified": validated["manifest_blob_sha1"],
        "request_marker_validated": True,
        "preregistration_validated": True,
        "request_profile": "R3",
        "one_shot_attempt": 3,
        "preregistration_path": probe.PREREG_PATH_R3,
        "request_marker_path": probe.REQUEST_PATH_R3,
        "request_timeout_seconds": 60,
        "request_count": 1,
        "response_bytes": 0,
        "responses": [],
        "transport_errors": ["TimeoutError"],
    })
    receipt["safety"]["source_requests_made"] = 1
    receipt["receipt_fingerprint"] = persistence.canonical_fingerprint(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    return receipt


def test_r3_receipt_persistence_accepts_the_preregistered_timeout_and_preserves_unknown_result(tmp_path):
    from automation import q221_dod_097_wayback_receipt_persist as persistence

    artifact = tmp_path / "artifacts" / "q221-r3"
    artifact.mkdir(parents=True)
    source = artifact / persistence.RECEIPT_FILENAME_R3
    original = _write_r3_persistable_receipt(source)
    result = persistence.persist_receipt(
        artifact, tmp_path / "evidence", "765432",
        receipt_filename=persistence.RECEIPT_FILENAME_R3,
    )
    attempt = Path(result["attempt_path"])
    latest = Path(result["latest_path"])
    assert attempt.read_bytes() == source.read_bytes()
    assert latest.read_bytes() == source.read_bytes()
    assert original["source_probe"]["request_count"] == 1
    assert original["source_probe"]["response_bytes"] == 0
    assert original["source_probe"]["transport_errors"] == ["TimeoutError"]
    assert original["safety"]["performance_authorization"] is False
    assert original["safety"]["live_execution"] is False


def test_r3_receipt_persistence_rejects_r2_profile_on_r3_filename(tmp_path):
    from automation import q221_dod_097_wayback_receipt_persist as persistence

    receipt = _write_r3_persistable_receipt(tmp_path / persistence.RECEIPT_FILENAME_R3)
    with pytest.raises(persistence.ReceiptPersistenceError, match="R3 marker/preregistration/timeout differs"):
        persistence.validate_receipt(receipt, persistence.RECEIPT_FILENAME)


def test_r3_source_and_sync_workflows_are_marker_only_and_one_shot():
    source = (ROOT / ".github/workflows/q221-dod-097-wayback-archive-presence-r3.yml").read_text(encoding="utf-8")
    source_triggers = source.split("permissions:", 1)[0]
    assert "branches: [master]" in source_triggers
    assert "research/run_requests/q221_dod_097_wayback_archive_presence_r3.trigger" in source_triggers
    assert "schedule:" not in source_triggers and "workflow_dispatch:" not in source_triggers
    assert "q221-dod-097-wayback-archive-presence-r3.yml/runs" in source
    assert "probe_attempt_number" in source and "recovery_of_workflow_run_id" in source
    assert "60-second" in source
    assert "upload-artifact@v6" in source

    sync = (ROOT / ".github/workflows/q221-dod-097-wayback-archive-presence-r3-sync.yml").read_text(encoding="utf-8")
    assert "Q221 DoD 097 Wayback Archive Schema and Row-Presence Probe (Recovery R3)" in sync
    assert "github.event.workflow_run.head_branch == 'master'" in sync
    assert "--receipt-filename q221-dod-097-wayback-presence-r3.json" in sync
    assert "github_contents_publish.py" in sync
    persistence = (ROOT / "automation/q221_dod_097_wayback_receipt_persist.py").read_text(encoding="utf-8")
    assert "RECEIPT_FILENAME_R3" in persistence
    assert '"timeout": 60' in persistence
    assert "WAYBACK_RECEIPT_FINGERPRINT_MISMATCH" in persistence





def test_receipt_writer_persists_a_verifiable_canonical_fingerprint(tmp_path):
    path = tmp_path / "attempt-receipt.json"
    receipt = probe._base_receipt()
    receipt["status"] = "TEST_ONLY_RECEIPT_WRITER"
    probe._write_receipt(path, receipt)
    saved = probe._json(path)
    assert saved["receipt_fingerprint"] == probe._fingerprint(saved)
    assert saved["status"] == "TEST_ONLY_RECEIPT_WRITER"
    assert saved["safety"]["source_requests_made"] == 0
    assert saved["safety"]["historical_first_public_observation_proven"] is False
    assert saved["safety"]["performance_authorization"] is False
