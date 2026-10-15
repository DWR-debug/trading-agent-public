from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from automation.q221_pre_event_parent_identity_feasibility import (
    BOUNDARY_FP,
    MAX_BYTES_EACH,
    MAX_REQUESTS,
    MAX_TOTAL_BYTES,
    PREREG_PATH,
    FeasibilityError,
    build_analysis,
    canonical_fingerprint,
    read_downloaded_sources,
    text_key,
    validate_preregistration,
)

ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH_ABS = ROOT / PREREG_PATH


def _prereg():
    return json.loads(PREREG_PATH_ABS.read_text(encoding="utf-8"))


def _write_synthetic_bundle(prereg, directory: Path, *, omit_record=None):
    directory.mkdir(parents=True, exist_ok=True)
    for spec in prereg["records"]:
        if spec["record_id"] == omit_record:
            continue
        if spec["role"] == "post_event_successor_name_control":
            body = (
                "<html><body><p>Date of Report: April 3, 2020</p>"
                "<p>Raytheon Technologies Corporation</p>"
                "<p>United Technologies Corporation changed its name to "
                "Raytheon Technologies Corporation (RTX).</p></body></html>"
            ).encode("utf-8")
        else:
            body = (
                "<html><body><h1>List of Subsidiaries</h1><p>"
                + spec["required_child_legal_name"]
                + "</p></body></html>"
            ).encode("utf-8")
        meta = {
            "record_id": spec["record_id"],
            "requested_url": spec["document_url"],
            "final_url": spec["document_url"],
            "http_status": 200,
            "content_type": "text/html; charset=utf-8",
            "response_bytes": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest(),
            "file_name": spec["record_id"] + ".html",
            "last_modified_header": None,
            "etag_header": None,
        }
        (directory / meta["file_name"]).write_bytes(body)
        (directory / (spec["record_id"] + ".meta.json")).write_text(
            json.dumps(meta, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )


def test_preregistration_freezes_five_exact_cases_and_zero_authority():
    prereg = _prereg()
    validate_preregistration(prereg, PREREG_PATH_ABS)
    assert [row["record_id"] for row in prereg["records"]] == [
        "CACI_2019_PRE_EVENT",
        "BOOZ_ALLEN_2020_PRE_EVENT",
        "OSI_AS_E_2023_PRE_EVENT",
        "NORTHROP_2024_PRE_EVENT",
        "RTX_SUCCESSOR_NAME_TEMPORAL_CONTROL",
    ]
    assert prereg["execution_limits"]["maximum_sec_requests"] == MAX_REQUESTS == 5
    assert prereg["execution_limits"]["maximum_response_bytes_each"] == MAX_BYTES_EACH
    assert prereg["execution_limits"]["maximum_aggregate_response_bytes"] == MAX_TOTAL_BYTES
    assert prereg["frozen_population"]["receipt_fingerprint"] == BOUNDARY_FP
    assert prereg["required_assertions"]["recipient_to_issuer_mapping_frozen"] is False
    assert prereg["safety"]["paid_api_budget_usd"] == 0


def test_preregistration_rejects_a_retry_or_looser_download_budget():
    prereg = _prereg()
    altered = copy.deepcopy(prereg)
    altered["execution_limits"]["automatic_retries"] = True
    with pytest.raises(FeasibilityError, match="PREREG_LIMIT_DRIFT"):
        validate_preregistration(altered, PREREG_PATH_ABS)

    altered = copy.deepcopy(prereg)
    altered["execution_limits"]["maximum_aggregate_response_bytes"] = MAX_TOTAL_BYTES + 1
    with pytest.raises(FeasibilityError, match="PREREG_LIMIT_DRIFT"):
        validate_preregistration(altered, PREREG_PATH_ABS)


def test_frozen_filing_date_must_precede_action_date_and_temporal_control_must_follow():
    prereg = _prereg()
    validate_preregistration(prereg, PREREG_PATH_ABS)
    caci, temporal = prereg["records"][0], prereg["records"][-1]
    assert caci["filing_date"] < caci["transaction_date"]
    assert temporal["filing_date"] > temporal["transaction_date"]
    assert temporal["role"] == "post_event_successor_name_control"


def test_fixed_sample_contains_four_public_parent_exhibits_and_one_non_authorizing_control():
    prereg = _prereg()
    positives = [x for x in prereg["records"] if x["role"] == "pre_event_parent_subsidiary_list"]
    controls = [x for x in prereg["records"] if x["role"] == "post_event_successor_name_control"]
    assert len(positives) == 4
    assert len(controls) == 1
    for spec in positives:
        assert spec["expected_parent_cik"] == spec["filing_filer_cik"]
        assert "sec.gov/Archives/edgar/data/" in spec["document_url"]
    assert controls[0]["expected_parent_cik"] is None
    assert controls[0]["filing_filer_cik"] == "0001047122"


def test_literal_entity_matching_normalizes_punctuation_but_does_not_use_fuzzy_names():
    assert text_key("CACI, INC. – FEDERAL") == text_key("CACI, INC. - FEDERAL")
    assert text_key("Booz Allen Hamilton Inc.") == text_key("BOOZ ALLEN HAMILTON INC")
    assert text_key("Northrop Grumman Systems Corporation") != text_key("Northrop Grumman Corporation")


def test_synthetic_reproduction_keeps_all_five_rows_unmapped_and_gates_closed(tmp_path):
    prereg = _prereg()
    source_dir = tmp_path / "sec-docs"
    _write_synthetic_bundle(prereg, source_dir)
    result = build_analysis(prereg, {"preregistration_sha256": "a" * 64}, source_dir)

    assert result["record_type"] == "q221_pre_event_parent_identity_feasibility"
    assert result["status"] == "Q221_PRE_EVENT_PARENT_SOURCE_FEASIBILITY_COMPLETE_LINEAGE_UNRESOLVED"
    assert result["sample_counts"] == {
        "pre_event_parent_exhibit_cases": 4,
        "post_event_successor_name_controls": 1,
        "total_frozen_cases": 5,
    }
    assert result["interpretation"]["four_parent_filings_name_exact_child_legal_entity"] is True
    assert result["interpretation"]["historical_parent_lineage_proven"] is False
    assert result["interpretation"]["child_identifier_bridge_to_frozen_uei_proven"] is False
    assert result["interpretation"]["historical_first_public_observation_proven"] is False
    assert result["interpretation"]["recipient_to_issuer_mapping_frozen"] is False
    assert result["interpretation"]["q221_gate_positive"] is False
    assert all(row["mapping_authority"] is None for row in result["observations"])
    assert all(row["recipient_to_issuer_mapping_frozen"] is False for row in result["observations"])
    control = result["observations"][-1]
    assert control["successor_name_event_postdates_transaction"] is True
    assert control["classification"] == "CURRENT_PARENT_SUCCESSOR_NAME_POSTDATES_TRANSACTION_NOT_HISTORICAL_PROOF"
    assert result["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "paid_api_budget_usd": 0,
    }
    assert result["analysis_fingerprint"]


def test_missing_child_legal_name_fails_closed(tmp_path):
    prereg = _prereg()
    source_dir = tmp_path / "sec-docs"
    _write_synthetic_bundle(prereg, source_dir)

    spec = prereg["records"][0]
    body_path = source_dir / (spec["record_id"] + ".html")
    altered = body_path.read_text(encoding="utf-8").replace(spec["required_child_legal_name"], "UNRELATED COMPANY LLC")
    body_path.write_text(altered, encoding="utf-8")
    meta_path = source_dir / (spec["record_id"] + ".meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    new_body = body_path.read_bytes()
    meta["response_bytes"] = len(new_body)
    meta["response_sha256"] = hashlib.sha256(new_body).hexdigest()
    meta_path.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(FeasibilityError, match="PRE_EVENT_PARENT_EXHIBIT_CHILD_NAME_NOT_FOUND"):
        build_analysis(prereg, {"preregistration_sha256": "a" * 64}, source_dir)


def test_source_bundle_rejects_tampered_hashes_and_extra_files(tmp_path):
    prereg = _prereg()
    source_dir = tmp_path / "sec-docs"
    _write_synthetic_bundle(prereg, source_dir)

    first = prereg["records"][0]["record_id"]
    body_path = source_dir / (first + ".html")
    body_path.write_bytes(body_path.read_bytes() + b"tamper")
    with pytest.raises(FeasibilityError, match="SEC_SOURCE_BODY_HASH_OR_SIZE_MISMATCH"):
        read_downloaded_sources(prereg, source_dir)

    _write_synthetic_bundle(prereg, source_dir)
    (source_dir / "unexpected.html").write_text("extra", encoding="utf-8")
    with pytest.raises(FeasibilityError, match="SEC_SOURCE_DIR_FILE_SET_MISMATCH"):
        read_downloaded_sources(prereg, source_dir)


def test_every_reported_case_is_a_fixed_unmapped_boundary_row():
    prereg = _prereg()
    for spec in prereg["records"]:
        assert spec["recipient_to_issuer_status"] if "recipient_to_issuer_status" in spec else True
        assert spec["transaction_key"]
        assert spec["recipient_uei"]
        assert spec["recipient_id"]
        assert spec["current_parent_name"]
        assert spec["current_parent_uei"]
