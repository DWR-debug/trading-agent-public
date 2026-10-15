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
    recovery = probe.validate_frozen_inputs(ROOT, probe.PREREG_PATH_R2, probe.REQUEST_PATH_R2)
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
    with pytest.raises(probe.ProbeError, match="PROFILE_MISMATCH"):
        probe.validate_frozen_inputs(ROOT, probe.PREREG_PATH, probe.REQUEST_PATH_R2)


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
    assert "receipt_fingerprint" in text
    assert "R2_RECEIPT_FINGERPRINT_MISMATCH" in text
    assert "q221_dod_097_wayback_archive_presence_attempt_" in text
    assert "IMMUTABLE_R2_ATTEMPT_RECEIPT_ALREADY_EXISTS" in text
    assert "github_contents_publish.py" in text
    assert "live_trading_enabled" in text



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
