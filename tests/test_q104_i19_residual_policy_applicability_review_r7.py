import json
from pathlib import Path

import pytest

from automation import q104_i19_residual_policy_applicability_review_r7 as r7
from automation.project_integrity_check import ACTIVE_WORKFLOWS, ROOT


def test_r7_frozen_target_keys_are_exact_and_disjoint_from_existing_seventeen():
    targets = [a for p in r7.ARCHIVES.values() for a in p["accessions"]]
    assert len(targets) == 19
    assert len(set(targets)) == 19
    assert sum(len(p["accessions"]) for p in r7.ARCHIVES.values()) == 19
    assert r7.TOTAL_ARCHIVE_BYTES == 127_943_839
    assert r7.TOTAL_ARCHIVE_BYTES < r7.MAX_TOTAL_BYTES
    assert all(p["bytes"] <= r7.MAX_ARCHIVE_BYTES for p in r7.ARCHIVES.values())
    assert sum(r7.FAILURE_COUNTS.values()) == 53
    assert sum(r7.FAILURE_COUNTS[k] for k in r7.DATE_FAILURES) == 36


def test_checked_in_request_matches_every_frozen_runtime_pin():
    request = ROOT / "research/run_requests/q104_i19_residual_policy_applicability_r7.trigger"
    values = r7.read_request(request)
    assert values["SOURCE_OF_TRUTH"] == "DWR-debug/trading-agent-public"
    assert values["REQUEST_SEQUENCE"] == "2026-10-15T15:42:00Z"
    assert values["EXPECTED_SOURCE_ARCHIVE_DOWNLOAD_BYTES"] == "127943839"
    assert values["DATE_MISMATCH_TARGET_COUNT"] == "19"
    assert values["HEADER_ROUTE_COUNT"] == "57"


def test_request_contract_is_preregistered_paper_only_and_has_no_gate_authority(tmp_path):
    request = tmp_path / "request.trigger"
    values = dict(r7.FROZEN)
    values["REQUEST_SEQUENCE"] = "2026-10-15T09:59:00Z"
    request.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    assert r7.read_request(request) == values
    for key in (
        "CENSUS_RESTART", "REPAIR_RECEIPTS", "APPLY_FIELD_PRECEDENCE",
        "CHANGE_PRODUCTION_JOIN", "PERFORMANCE", "HOLDOUT_SELECTION",
        "RANKING", "TUNING", "PROMOTION", "LIVE_EXECUTION",
    ):
        assert values[key] == "false"
    assert values["NO_NEW_DAILY_FEED_REQUESTS"] == "true"
    assert values["NO_PRIMARY_DOCUMENT_REQUESTS"] == "true"
    assert values["NO_SOURCE_RECEIPT_REWRITES"] == "true"
    assert values["RESEARCH_GATES_REMAIN_CLOSED"] == "true"
    assert values["PAID_API_BUDGET_USD"] == "0"


def test_request_rejects_a_mutated_performance_or_hash_policy(tmp_path):
    vals = dict(r7.FROZEN)
    vals["REQUEST_SEQUENCE"] = "2026-10-15T09:59:00Z"
    vals["APPLY_FIELD_PRECEDENCE"] = "true"
    p = tmp_path / "bad.trigger"
    p.write_text("".join(f"{k}={v}\n" for k, v in vals.items()), encoding="utf-8")
    with pytest.raises(r7.ReviewError, match="REQUEST_VALUE_MISMATCH:APPLY_FIELD_PRECEDENCE"):
        r7.read_request(p)


def test_combined_budget_enforces_total_and_header_limits_separately():
    budget = r7.CombinedBudget(total=20, header=4)
    budget.add(7)
    budget.is_header_phase = True
    budget.add(4)
    assert budget.used == 11
    assert budget.header_used == 4
    with pytest.raises(r7.ReviewError, match="HEADER_DOWNLOAD_BUDGET_EXCEEDED"):
        budget.add(1)
    budget2 = r7.CombinedBudget(total=3, header=3)
    with pytest.raises(r7.ReviewError, match="TOTAL_DOWNLOAD_BUDGET_EXCEEDED"):
        budget2.add(4)


def test_current_pinned_helper_implementations_match_the_frozen_contract():
    assert r7.validate_helpers() == r7.HELPER_BLOBS


def test_capture_reader_uses_the_exact_shard_keys_emitted_by_input_loader():
    source = Path(__file__).resolve().parents[1] / "automation/q104_i19_residual_policy_applicability_review_r7.py"
    code = source.read_text(encoding="utf-8")
    loader = code[code.index('inputs={"request":request'):code.index("return inputs,bundle")]
    capture = code[code.index("def capture_headers("):code.index("def build_analysis(")]
    assert '"original_shards":originals' in loader
    assert '"repaired_shards":repaired' in loader
    assert 'inputs["original_shards"]' in capture
    assert 'inputs["repaired_shards"]' in capture
    assert 'inputs["original"]' not in capture
    assert 'inputs["repaired"]' not in capture


def test_capture_validator_fails_closed_before_it_can_authorize_incomplete_evidence():
    incomplete = {
        "record_type": "q104_i19_residual_policy_applicability_r7_capture",
        "status": "Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE",
        "receipt_fingerprint": "not-a-valid-fingerprint",
    }
    with pytest.raises(r7.ReviewError, match="CAPTURE_RECEIPT_FINGERPRINT_OR_STATUS_INVALID"):
        r7.validate_capture_payload({}, incomplete)


def test_safety_contract_has_no_live_orders_or_automatic_promotion():
    assert r7.SAFETY == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "paid_api_budget_usd": 0,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    }


def test_workflow_is_registered_and_requires_only_the_explicit_request_marker():
    name = "q104-i19-residual-policy-applicability-r7.yml"
    assert name in ACTIVE_WORKFLOWS
    workflow = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", 1)[0]
    assert 'paths:\n      - "research/run_requests/q104_i19_residual_policy_applicability_r7.trigger"' in trigger
    assert "workflow_dispatch:" not in trigger
    assert "q104-i19-residual-policy-applicability-r7.yml" in ACTIVE_WORKFLOWS


def test_workflow_uses_immutable_input_artifact_ids_and_no_primary_document_downloads():
    workflow = (ROOT / ".github" / "workflows" / "q104-i19-residual-policy-applicability-r7.yml").read_text(encoding="utf-8")
    for value in (
        "38250105408", "11747003791", "38557631541", "11890995910", "11891525016",
        "38574180245", "11899236364", "38582684174", "11902804060", "38588100012", "11905763813",
        "q104_i19_residual_policy_applicability_r7.trigger",
    ):
        assert value in workflow
    assert "no-new-primary" in workflow.lower()
    assert "NO_PRIMARY_DOCUMENT_REQUESTS" in (ROOT / "research" / "run_requests" / "q104_i19_residual_policy_applicability_r7.trigger").read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04-arm" in workflow
    assert "--expected-analysis-fingerprint" in workflow
    assert "Q104_R7_CROSS_ARCH" in workflow or "cross-arch" in workflow.lower()
def _synthetic_r7_capture(status):
    request = dict(r7.FROZEN)
    request["REQUEST_SEQUENCE"] = r7.R7_SOURCE_CAPTURE_SEQUENCE
    inputs = {"request": request, "helper_blobs": dict(r7.HELPER_BLOBS)}
    expected_404 = set(r7.R7_EXPECTED_INDEX_404_ACCESSIONS)
    samples = []
    for archive_name, pin in r7.ARCHIVES.items():
        for accession in pin["accessions"]:
            exception = accession in expected_404
            source_row = {
                "accession": accession,
                "filer_cik": "1234567",
                "form": "13F-HR",
                "filing_date_iso": "2000-01-01",
            }
            normalized = accession.replace("-", "")
            base = f"https://www.sec.gov/Archives/edgar/data/1234567/{normalized}"
            route_defs = [
                ("index_headers", f"{base}/{accession}-index-headers.html", "FETCHED"),
                ("raw_sgml_header", f"{base}/{accession}.hdr.sgml", "FETCHED"),
                ("complete_submission_header_prefix", f"{base}/{accession}.txt", "FETCHED_PREFIX"),
            ]
            probes = []
            for route, url, fetch_status in route_defs:
                if exception and route == "index_headers":
                    probes.append({
                        "route": route,
                        "requested_url": url,
                        "http_status": 404,
                        "status": "HTTP_ERROR",
                        "error": "HTTP_404",
                        "response_error": "HTTP_404",
                        "response_bytes": 0,
                        "observed_identity": None,
                        "comparison_to_frozen_archive_row": None,
                    })
                    continue
                observed = {
                    "accession": accession,
                    "filer_cik": "1234567",
                    "form": "13F-HR",
                    "filing_date": "2000-01-02",
                    "acceptance_datetime": "2000-01-02T13:00:00",
                    "date_of_filing_date_change": None,
                }
                probes.append({
                    "route": route,
                    "requested_url": url,
                    "http_status": 200,
                    "status": fetch_status,
                    "response_sha256": "a" * 64,
                    "response_bytes": 128,
                    "observed_identity": observed,
                    "comparison_to_frozen_archive_row": {
                        "accession_matches": True,
                        "filer_cik_matches": True,
                        "form_matches": True,
                        "filing_date_matches": False,
                    },
                })
            legacy = status == "Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE"
            samples.append({
                "accession": accession,
                "source_archive_name": archive_name,
                "source_archive_url": pin["url"],
                "frozen_failure": "FILING_DATE_MISMATCH",
                "source_row": source_row,
                "source_archive_sha256_match": True,
                "probes": probes,
                "summary": {
                    "usable_route_count": 2 if exception else 3,
                    "all_three_routes_usable": not exception,
                    "identity_fields_match_frozen_source_row": (not exception) or (not legacy),
                    **({"known_index_header_404_exception": True} if exception and not legacy else {}),
                    "header_filing_dates_agree": True,
                    "acceptance_datetimes_agree": True,
                    "bulk_filing_date_differs_from_header": True,
                    "date_change_values_agree_where_observed": True,
                    "observed_edgar_header_filing_date": "2000-01-02",
                    "observed_acceptance_datetime": "2000-01-02T13:00:00",
                    "observed_date_of_filing_date_change": None,
                },
                "status": (
                    "OBSERVATION_INCOMPLETE_OR_IDENTITY_CONFLICT"
                    if exception and legacy
                    else "OBSERVED_TWO_ROUTE_INDEX_404"
                    if exception
                    else "OBSERVED"
                ),
            })
    source_archives = {}
    for name, pin in r7.ARCHIVES.items():
        source_archives[name] = {
            "url": pin["url"],
            "expected_sha256": pin["sha"],
            "expected_bytes": pin["bytes"],
            "actual_sha256": pin["sha"],
            "actual_bytes": pin["bytes"],
            "verified": True,
            "http": {
                "status": "FETCHED",
                "http_status": 200,
                "response_bytes": pin["bytes"],
                "response_sha256": pin["sha"],
            },
            "requested_accessions": sorted(pin["accessions"]),
            "source_rows_found": sorted(pin["accessions"]),
            "source_rows_missing": [],
        }
    legacy = status == "Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE"
    capture = {
        "schema_version": 1,
        "record_type": "q104_i19_residual_policy_applicability_r7_capture",
        "candidate_id": "Q104:I19",
        "status": status,
        "generated_at_utc": "2026-10-15T15:44:35Z",
        "frozen_request_sequence": request["REQUEST_SEQUENCE"],
        "frozen_input_receipt_fingerprints": r7.frozen_fingerprints(inputs),
        "helper_code_blobs": dict(r7.HELPER_BLOBS),
        "source_archives": source_archives,
        "sample_count": 19,
        "sample_count_complete": 15 if legacy else 19,
        "source_row_count": 19,
        "header_route_request_count": 57,
        "header_route_usable_count": 53,
        "bulk_date_differs_count": 19,
        "identity_validated_count": 15 if legacy else 19,
        "acceptance_routes_agree_count": 19,
        "source_archive_download_expected_bytes": r7.TOTAL_ARCHIVE_BYTES,
        "source_archive_download_actual_bytes": r7.TOTAL_ARCHIVE_BYTES,
        "download_budget": {
            "bytes_consumed": r7.TOTAL_ARCHIVE_BYTES + 218911,
            "max_total_bytes": r7.MAX_TOTAL_BYTES,
            "header_bytes_consumed": 218911,
            "max_header_response_bytes": r7.MAX_HEADER_TOTAL,
            "max_header_response_bytes_each": r7.MAX_HEADER_EACH,
        },
        "samples": samples,
        "source_bodies_persisted": False,
        "complete_submission_text_bodies_persisted": False,
        "primary_document_requests": 0,
        "daily_feed_requests": 0,
        "archive_census_restarted": False,
        "source_receipts_modified": False,
        "frozen_expected_dates_modified": False,
        "field_precedence_applied": False,
        "production_join_changed": False,
        "acceptance_time_gate_cleared": False,
        "historical_archive_gate_cleared": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": dict(r7.SAFETY),
        "errors": [],
    }
    capture["receipt_fingerprint"] = r7.fp(capture)
    return inputs, capture


@pytest.mark.parametrize("status", [
    "Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE",
    "Q104_I19_RESIDUAL_R7_CAPTURE_COMPLETE",
])
def test_validator_accepts_only_the_four_pinned_2013_index_404_exceptions(status):
    inputs, capture = _synthetic_r7_capture(status)
    r7.validate_capture_payload(inputs, capture)


def test_validator_rejects_any_non_allowlisted_header_404():
    inputs, capture = _synthetic_r7_capture("Q104_I19_RESIDUAL_R7_CAPTURE_COMPLETE")
    sample = next(s for s in capture["samples"] if s["accession"] == "0000950123-15-003218")
    probe = next(p for p in sample["probes"] if p["route"] == "index_headers")
    probe.update({
        "http_status": 404,
        "status": "HTTP_ERROR",
        "error": "HTTP_404",
        "response_error": "HTTP_404",
        "response_bytes": 0,
        "observed_identity": None,
        "comparison_to_frozen_archive_row": None,
    })
    capture["header_route_usable_count"] = 52
    capture["receipt_fingerprint"] = r7.fp(capture)
    with pytest.raises(r7.ReviewError, match="CAPTURE_SAMPLE_NOT_VALIDATED|CAPTURE_ROUTE_HTTP_OR_SIZE_INVALID"):
        r7.validate_capture_payload(inputs, capture)


def test_expected_2013_index_404_requires_exact_urls_and_both_identity_consistent_routes():
    inputs, capture = _synthetic_r7_capture("Q104_I19_RESIDUAL_R7_CAPTURE_INCOMPLETE")
    sample = next(s for s in capture["samples"] if s["accession"] == "0000950123-13-006949")
    assert r7.known_index_header_404_exception(sample)
    sample["probes"][0]["requested_url"] += "?different"
    assert not r7.known_index_header_404_exception(sample)


def test_replay_accepts_the_input_prefix_emitted_by_the_capture_bundle_writer():
    from_original = {f"original/{shard}.json" for shard in r7.ORIGINAL}
    from_input = {f"input/{shard}.json" for shard in r7.ORIGINAL}
    assert r7.resolve_original_shard_prefix(from_original) == "original"
    assert r7.resolve_original_shard_prefix(from_input) == "input"
    with pytest.raises(r7.ReviewError, match="BUNDLE_ORIGINAL_SHARD_PREFIX_INVALID"):
        r7.resolve_original_shard_prefix({"recovery.json"})


def test_analysis_keeps_expected_404_policy_separate_from_all_research_and_execution_gates():
    source = Path(r7.__file__).read_text(encoding="utf-8")
    assert "Only the four frozen 2013Q3 accessions may use" in source
    assert '"offline_route_exception_used":True' in source
    assert '"acceptance_time_gate_cleared":False' in source
    assert '"historical_archive_gate_cleared":False' in source
    assert '"performance_authorization":False' in source
    assert '"promotion":False' in source
    assert '"live_execution":False' in source

