import json
from pathlib import Path

import pytest

from automation.q221_fpds_public_atom_identity_bridge import (
    ALLOWED_HOST,
    BOUNDARY_FP,
    BOUNDARY_PATH,
    ENDPOINT,
    EXPECTED_RECORDS,
    PRE_EVENT_FP,
    BridgeError,
    _get,
    _normalize_name,
    _text_values,
    build_receipt,
    canonical_fingerprint,
    parse_atom,
    read_request,
    validate_frozen_inputs,
    verify,
)


ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "research/run_requests/q221_fpds_public_atom_identity_bridge.trigger"
PREREG = ROOT / "research/preregistrations/q221_fpds_public_atom_identity_bridge_2026_10_15.json"


def test_q221_fpds_request_and_frozen_inputs_match_exact_registered_contract():
    request = read_request(REQUEST)
    boundary, prereg, pre_event = validate_frozen_inputs(ROOT, request)

    assert len(boundary["transactions"]) == 348
    assert boundary["receipt_fingerprint"] == BOUNDARY_FP
    assert pre_event["receipt_fingerprint"] == PRE_EVENT_FP
    assert len(prereg["records"]) == 4
    assert [x["piid"] for x in EXPECTED_RECORDS] == [
        "FA875018C0180",
        "FA807520F0004",
        "70RWMD23C00000001",
        "FA865124FB001",
    ]
    assert request["FPDS_PUBLIC_ENDPOINT"] == ENDPOINT
    assert request["NO_SAM_API_REQUESTS"] == "true"
    assert request["FOLLOW_REDIRECTS"] == "false"
    assert request["RETRIES"] == "0"


def test_request_rejects_attempt_to_expand_scope(tmp_path):
    request = REQUEST.read_text(encoding="utf-8")
    expanded = tmp_path / "request.trigger"
    expanded.write_text(request.replace("TARGET_RECORD_COUNT=4", "TARGET_RECORD_COUNT=5"), encoding="utf-8")
    with pytest.raises(BridgeError, match="VALUE_MISMATCH:TARGET_RECORD_COUNT"):
        read_request(expanded)


def test_atom_parser_reads_exact_piid_modification_date_uei_duns_and_legal_name():
    body = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <content>
          <contract>
            <PIID>FA875018C0180</PIID>
            <modNumber>P00003</modNumber>
            <signedDate>2019-01-03T00:00:00Z</signedDate>
            <uniqueEntityId>N3PBJAVNKF61</uniqueEntityId>
            <vendorDunsNumber>123456789</vendorDunsNumber>
            <vendorNameFromContract>CACI, INC. - FEDERAL</vendorNameFromContract>
            <entityDataSource>UEI</entityDataSource>
          </contract>
        </content>
      </entry>
    </feed>"""
    rows = parse_atom(body)
    assert len(rows) == 1
    row = rows[0]
    assert "FA875018C0180" in row["piid_values"]
    assert "P00003" in row["modification_number_values"]
    assert "2019-01-03T00:00:00Z" in row["signed_date_values"]
    assert "N3PBJAVNKF61" in row["uei_values"]
    assert "123456789" in row["duns_values"]
    assert "CACI, INC. - FEDERAL" in row["awardee_name_values"]
    assert "UEI" in row["entity_data_source_values"]


def test_atom_parser_rejects_malformed_xml():
    with pytest.raises(BridgeError, match="ATOM_XML_INVALID"):
        parse_atom(b"<feed><entry>")


def test_legal_name_normalization_only_normalizes_surface_punctuation_and_ampersand():
    assert _normalize_name("AMERICAN SCIENCE & ENGINEERING INC") == _normalize_name(
        "American Science and Engineering, Inc."
    )
    assert _normalize_name("NORTHROP GRUMMAN SYSTEMS CORPORATION") == _normalize_name(
        "Northrop Grumman Systems Corporation"
    )
    assert _normalize_name("CACI INC FEDERAL") != _normalize_name("CACI INTERNATIONAL INC")


def test_offline_verification_checks_receipt_identity_and_performs_no_network(tmp_path):
    request = read_request(REQUEST)
    # Synthetic transport failures keep this test entirely offline. They exercise
    # fingerprint and contract verification, not source availability or evidence.
    observations = [
        {
            "record_id": spec["record_id"],
            "transaction_key": spec["transaction_key"],
            "requested_url": ENDPOINT + "?FEEDNAME=PUBLIC",
            "method": "GET",
            "requested_host": ALLOWED_HOST,
            "http_status": None,
            "content_type": "",
            "response_bytes": 0,
            "response_sha256": None,
            "response_persisted": False,
            "entry_count": 0,
            "piid_entry_count": 0,
            "piid_modification_candidate_count": 0,
            "exact_tuple_count": 0,
            "observed_records": [],
            "status": "NETWORK_ERROR",
            "error_type": "URLError",
        }
        for spec in EXPECTED_RECORDS
    ]
    capture = build_receipt(ROOT, request, observations, 0)
    capture_path = tmp_path / "capture.json"
    capture_path.write_text(json.dumps(capture, sort_keys=True), encoding="utf-8")
    validation_path = tmp_path / "validation.json"

    validation = verify(ROOT, capture_path, validation_path)
    assert validation["status"] == "DETERMINISTIC_CAPTURE_RECEIPT_VALIDATED"
    assert validation["analysis_fingerprint"] == capture["analysis_fingerprint"]
    assert validation["network_requests_made"] == 0
    assert validation["source_gate_positive"] is False
    assert validation["recipient_to_issuer_mapping_frozen"] is False
    assert validation["receipt_fingerprint"] == canonical_fingerprint(validation)


def test_frozen_source_safety_contract_is_not_positive_or_performance_authority():
    request = read_request(REQUEST)
    _, prereg, pre_event = validate_frozen_inputs(ROOT, request)
    assert prereg["required_assertions"]["q221_gate_positive"] is False
    assert prereg["required_assertions"]["recipient_to_issuer_mapping_frozen"] is False
    assert pre_event["interpretation"]["q221_gate_positive"] is False
    assert pre_event["interpretation"]["performance_authorization"] is False
    assert prereg["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "paid_api_budget_usd": 0,
    }
