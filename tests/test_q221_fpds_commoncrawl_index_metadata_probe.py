import copy
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from automation.q221_fpds_commoncrawl_index_metadata_probe import (
    EXPECTED_RECORDS,
    OUTPUT_FIELDS,
    PREREG_PATH,
    REQUEST_PATH,
    ProbeError,
    build_fallback_receipt,
    build_index_url,
    parse_jsonl_body,
    read_marker,
    validate_preflight,
    validate_receipt,
)

ROOT = Path(__file__).resolve().parents[1]


def _row(record, *, timestamp="20181210121212", status="200", url=None, filename=None):
    return {
        "timestamp": timestamp,
        "url": url or record["original_url"],
        "status": status,
        "mime": "application/atom+xml",
        "digest": "EXAMPLE-DIGEST",
        "length": "812",
        "offset": "12345",
        "filename": filename or (
            f"crawl-data/{record['crawl']}/segments/123.1/warc/CC-MAIN-20181210120000-20181210130000-00000.warc.gz"
        ),
    }


def test_frozen_preflight_validates_four_pre_event_rows_without_network():
    result = validate_preflight(ROOT, ROOT / REQUEST_PATH, ROOT / PREREG_PATH)
    assert result["status"] == "Q221_COMMONCRAWL_FROZEN_INPUTS_VALID"
    assert result["request_count"] == 0
    assert result["source_requests_made"] == 0
    assert result["records_validated"] == 4
    assert result["historical_first_public_observation_proven"] is False
    assert result["recipient_to_issuer_mapping_frozen"] is False
    assert all(record["crawl_end_date"] < record["action_date"] for record in EXPECTED_RECORDS)


def test_index_url_uses_fixed_collection_exact_original_url_and_json_output():
    record = EXPECTED_RECORDS[0]
    url = build_index_url(record)
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    assert parts.scheme == "https"
    assert parts.netloc == "index.commoncrawl.org"
    assert parts.path == f"/{record['crawl']}-index"
    assert query["url"] == [record["original_url"]]
    assert query["matchType"] == ["exact"]
    assert query["output"] == ["json"]
    assert query["limit"] == ["50"]
    assert record["original_url"] not in url


def test_valid_jsonl_capture_is_metadata_only_and_exact():
    record = EXPECTED_RECORDS[0]
    body = (json.dumps(_row(record)) + "\n").encode("utf-8")
    parsed = parse_jsonl_body(body, record)
    assert parsed["query_completed"] is True
    assert parsed["status"] == "COMMONCRAWL_INDEX_METADATA_VALID"
    assert parsed["capture_count"] == 1
    assert parsed["exact_url_capture_count"] == 1
    assert parsed["exact_url_http_200_capture_count"] == 1
    assert parsed["captures"][0]["timestamp"] == "20181210121212"
    assert set(parsed["captures"][0]) == set(OUTPUT_FIELDS)
    assert "response_body" not in parsed


def test_empty_commoncrawl_index_response_is_a_valid_no_row_result_for_that_collection_only():
    parsed = parse_jsonl_body(b"", EXPECTED_RECORDS[0])
    assert parsed["query_completed"] is True
    assert parsed["status"] == "COMMONCRAWL_INDEX_VALID_EMPTY"
    assert parsed["capture_count"] == 0
    assert parsed["exact_url_http_200_capture_count"] == 0


@pytest.mark.parametrize("body", [b"{", b'{"url":', b"not-json\n", b"\n{\n"])
def test_malformed_or_partial_jsonl_is_incomplete_not_no_hit(body):
    with pytest.raises(ProbeError):
        parse_jsonl_body(body, EXPECTED_RECORDS[0])


def test_parser_fails_closed_on_nonexact_url():
    record = EXPECTED_RECORDS[0]
    body = (json.dumps(_row(record, url=record["original_url"] + "&different=1")) + "\n").encode()
    with pytest.raises(ProbeError, match="NONEXACT"):
        parse_jsonl_body(body, record)


def test_parser_fails_closed_on_capture_from_a_different_collection():
    record = EXPECTED_RECORDS[0]
    body = (json.dumps(_row(record, filename="crawl-data/CC-MAIN-2025-43/segments/1.1/warc/other.warc.gz")) + "\n").encode()
    with pytest.raises(ProbeError, match="FILENAME_COLLECTION"):
        parse_jsonl_body(body, record)


def test_parser_fails_closed_on_capture_timestamp_outside_frozen_collection_window():
    record = EXPECTED_RECORDS[0]
    body = (json.dumps(_row(record, timestamp="20190104121212")) + "\n").encode()
    with pytest.raises(ProbeError, match="TIMESTAMP_OUTSIDE"):
        parse_jsonl_body(body, record)


def test_fallback_receipt_is_fail_closed_and_verifiable_when_preflight_fails():
    receipt = build_fallback_receipt(
        123456, request_count_known_zero=True, reason="PREFLIGHT_FAILED_NO_SOURCE_REQUESTS"
    )
    validate_receipt(receipt)
    assert receipt["status"] == "PREFLIGHT_FAILED_NO_SOURCE_REQUESTS"
    assert receipt["source_contract"]["index_metadata_requests_attempted"] == 0
    assert receipt["safety"]["paper_only"] is True
    assert receipt["safety"]["historical_first_public_observation_proven"] is False


def test_receipt_fingerprint_detects_mutation():
    receipt = build_fallback_receipt(
        123456, request_count_known_zero=True, reason="PREFLIGHT_FAILED_NO_SOURCE_REQUESTS"
    )
    changed = copy.deepcopy(receipt)
    changed["status"] = "Q221_COMMONCRAWL_INDEX_METADATA_COMPLETE"
    with pytest.raises(ProbeError):
        validate_receipt(changed)


def test_changed_request_marker_is_rejected(tmp_path):
    original = (ROOT / REQUEST_PATH).read_text(encoding="utf-8")
    changed = original.replace("MAX_REQUESTS=4", "MAX_REQUESTS=5")
    assert changed != original
    path = tmp_path / "modified.trigger"
    path.write_text(changed, encoding="utf-8")
    with pytest.raises(ProbeError):
        read_marker(path)
