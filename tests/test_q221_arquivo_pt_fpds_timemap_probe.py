import json
from pathlib import Path

import pytest

from automation.q221_arquivo_pt_fpds_timemap_probe import (
    EXPECTED_RECORDS,
    MAX_REQUESTS,
    PREREG_PATH,
    PREREG_PATH_R2,
    REQUEST_PATH,
    REQUEST_PATH_R2,
    ProbeError,
    NoRedirect,
    analysis_fingerprint,
    canonical_fingerprint,
    fallback_receipt,
    parse_timemap_jsonl,
    read_key_value_request,
    timemap_request_url,
    validate_preflight,
    verify_receipt,
)


def test_exact_four_source_urls_are_frozen_and_host_scoped():
    assert len(EXPECTED_RECORDS) == MAX_REQUESTS == 4
    urls = [row["source_url"] for row in EXPECTED_RECORDS]
    assert len(set(urls)) == 4
    for record in EXPECTED_RECORDS:
        assert record["source_url"].startswith(
            "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q="
        )
        encoded = timemap_request_url(record["source_url"])
        assert encoded.startswith("https://arquivo.pt/wayback/timemap/json/https%3A%2F%2Fwww.fpds.gov%2F")
        assert "://" in encoded


def test_parser_keeps_only_bounded_metadata_and_exact_url_match():
    target = EXPECTED_RECORDS[0]["source_url"]
    body = (
        json.dumps(
            {
                "timestamp": "20200102030405",
                "url": target,
                "status": "200",
                "mime": "application/atom+xml",
                "digest": "ABC123",
                "length": "8321",
                "filename": "archive.warc.gz",
                "offset": "128",
            }
        )
        + "\n"
    ).encode()
    rows = parse_timemap_jsonl(body, target)
    assert len(rows) == 1
    assert rows[0]["capture_timestamp_utc"] == "2020-01-02T03:04:05Z"
    assert rows[0]["exact_original_url_match"] is True
    assert rows[0]["source_http_status"] == "200"
    assert rows[0]["mime"] == "application/atom+xml"
    assert rows[0]["warc_filename_present"] is True
    assert rows[0]["warc_offset_present"] is True
    assert "filename" not in rows[0]
    assert "body" not in rows[0]


def test_empty_timemap_is_valid_zero_rows_but_not_evidence_of_absence():
    assert parse_timemap_jsonl(b"", EXPECTED_RECORDS[0]["source_url"]) == []


def test_parser_rejects_invalid_json_missing_timestamp_and_unzoned_timestamp():
    target = EXPECTED_RECORDS[0]["source_url"]
    with pytest.raises(ProbeError, match="INVALID_JSON"):
        parse_timemap_jsonl(b"<html>not a TimeMap</html>", target)
    with pytest.raises(ProbeError, match="TIMESTAMP"):
        parse_timemap_jsonl((json.dumps({"url": target, "status": "200"}) + "\n").encode(), target)
    with pytest.raises(ProbeError, match="TIMEZONE"):
        parse_timemap_jsonl((json.dumps({"url": target, "timestamp": "2020-01-02T03:04:05", "status": "200"}) + "\n").encode(), target)


def test_parser_keeps_nonmatching_original_url_as_nonmatching_metadata():
    target = EXPECTED_RECORDS[0]["source_url"]
    body = (json.dumps({"timestamp": "20200102030405", "url": target + "&extra=1", "status": "200"}) + "\n").encode()
    rows = parse_timemap_jsonl(body, target)
    assert len(rows) == 1
    assert rows[0]["exact_original_url_match"] is False


def test_request_parser_rejects_duplicate_and_unexpected_keys(tmp_path: Path):
    path = tmp_path / "request.trigger"
    path.write_text("A=1\nA=2\n", encoding="utf-8")
    with pytest.raises(ProbeError, match="INVALID_KEY_VALUE"):
        read_key_value_request(path)
    path.write_text("unexpected=1\n", encoding="utf-8")
    with pytest.raises(ProbeError, match="KEY_SET_MISMATCH"):
        read_key_value_request(path)


def test_redirect_handler_never_follows_redirects():
    assert NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://other.example/") is None


def test_fallback_receipt_is_fail_closed_and_fingerprinted():
    receipt = fallback_receipt(123, "PREFLIGHT_FAILED", source_requests_known_zero=True)
    assert receipt["source_contract"]["archive_metadata_requests_attempted"] == 0
    assert receipt["status"] == "Q221_ARQUIVO_PT_PREFLIGHT_REJECTED"
    assert receipt["aggregate"]["historical_first_public_observation_proven"] is False
    assert receipt["aggregate"]["q221_gate_positive"] is False
    assert receipt["safety"]["live_execution"] is False
    assert receipt["receipt_fingerprint"] == canonical_fingerprint(receipt)
    assert receipt["analysis_fingerprint"] == analysis_fingerprint(receipt)
    assert verify_receipt(receipt)["validation_status"] == "VALIDATED"


def test_verifier_rejects_gate_mutation_and_receipt_mutation():
    receipt = fallback_receipt(123, "PREFLIGHT_FAILED", source_requests_known_zero=True)
    mutated = dict(receipt)
    mutated["aggregate"] = dict(receipt["aggregate"], q221_gate_positive=True)
    assert verify_receipt(mutated)["validation_status"] == "FAILED_CLOSED"

    mutated = dict(receipt)
    mutated["status"] = "GATE_CLEARED"
    assert verify_receipt(mutated)["validation_status"] == "FAILED_CLOSED"


def test_actual_preregistration_and_upstream_receipts_pass_offline_preflight():
    root = Path(__file__).resolve().parents[1]
    result = validate_preflight(root, root / REQUEST_PATH, root / PREREG_PATH)
    assert len(result["records"]) == 4
    assert result["prior_fpds"]["workflow_run_id"] == 38712516839
    assert result["boundary"]["sampled_transaction_count"] == 348
    assert result["pre_event"]["interpretation"]["recipient_to_issuer_mapping_frozen"] is False



def test_r2_preflight_pins_the_r1_zero_source_request_failure():
    root = Path(__file__).resolve().parents[1]
    result = validate_preflight(root, root / REQUEST_PATH_R2, root / PREREG_PATH_R2)
    assert len(result["records"]) == 4
    assert result["request_path"] == REQUEST_PATH_R2
    assert result["preregistration_path"] == PREREG_PATH_R2
    assert result["previous_arquivo_attempt"] == {
        "path": "research/evidence/q221_arquivo_pt_fpds_timemap_attempt_38863558147.json",
        "git_blob_sha1": "049c75c80b267434b62c654c4fa9a9d8bc3f4068",
        "receipt_fingerprint": "1b983784ea7b8d2d496021560b324195e9c219eafc9c538e7be32b232599aaae",
        "workflow_run_id": 38863558147,
        "source_requests_attempted": 0,
        "failure_reason_code": "PREFLIGHT_FAILED_NO_SOURCE_REQUESTS",
    }


def test_r2_preflight_rejects_crossed_request_and_preregistration():
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(ProbeError, match="CONTRACT_PATH_PAIR_MISMATCH"):
        validate_preflight(root, root / REQUEST_PATH, root / PREREG_PATH_R2)
