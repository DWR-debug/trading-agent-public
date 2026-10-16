import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from automation.q221_fpds_wayback_cdx_metadata_probe import (
    EXPECTED_RECORDS, OUTPUT_FIELDS, REQUEST_PATH, PREREG_PATH, ProbeError,
    build_cdx_url, build_fallback_receipt, parse_cdx_body, read_marker,
    validate_preflight, validate_receipt,
)

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_preflight_validates_exact_four_rows_without_requests():
    result = validate_preflight(ROOT, ROOT / REQUEST_PATH, ROOT / PREREG_PATH)
    assert result["status"] == "Q221_WAYBACK_CDX_FROZEN_INPUTS_VALID"
    assert result["request_count"] == 0
    assert result["source_requests_made"] == 0
    assert result["records_validated"] == 4
    assert result["historical_first_public_observation_proven"] is False
    assert result["recipient_to_issuer_mapping_frozen"] is False


def test_cdx_query_is_exact_and_preserves_frozen_original_url():
    source_url = EXPECTED_RECORDS[0]["source_url"]
    url = build_cdx_url(source_url)
    query = parse_qs(urlsplit(url).query)
    assert urlsplit(url).netloc == "web.archive.org"
    assert query["url"] == [source_url]
    assert query["matchType"] == ["exact"]
    assert query["output"] == ["json"]
    assert query["fl"] == [",".join(OUTPUT_FIELDS)]
    assert query["limit"] == ["1000"]
    assert query["gzip"] == ["false"]
    assert source_url not in url


def test_valid_cdx_response_retains_only_capture_metadata():
    source_url = EXPECTED_RECORDS[0]["source_url"]
    body = json.dumps([
        list(OUTPUT_FIELDS),
        ["20250128184322", source_url, "application/atom+xml", "200", "EXAMPLE-DIGEST", "812"],
        ["20250201010203", source_url, "application/atom+xml", "302", "REDIRECT-DIGEST", "0"],
    ]).encode("utf-8")
    parsed = parse_cdx_body(body, source_url)
    assert parsed["query_completed"] is True
    assert parsed["capture_count"] == 2
    assert parsed["exact_original_url_capture_count"] == 2
    assert parsed["exact_original_url_http_200_capture_count"] == 1
    assert parsed["captures"][0]["timestamp"] == "20250128184322"
    assert "body" not in parsed
    assert "response_body" not in parsed


def test_header_only_cdx_response_is_valid_empty_metadata_result():
    body = json.dumps([list(OUTPUT_FIELDS)]).encode("utf-8")
    parsed = parse_cdx_body(body, EXPECTED_RECORDS[0]["source_url"])
    assert parsed["query_completed"] is True
    assert parsed["capture_count"] == 0
    assert parsed["exact_original_url_http_200_capture_count"] == 0


@pytest.mark.parametrize("body", [b"", b"[]", b'{"captures": []}', b"not-json"])
def test_empty_or_wrong_shape_is_incomplete_not_a_no_hit(body):
    with pytest.raises(ProbeError):
        parse_cdx_body(body, EXPECTED_RECORDS[0]["source_url"])


def test_cdx_parser_rejects_nonexact_url_rows():
    body = json.dumps([
        list(OUTPUT_FIELDS),
        ["20250128184322", "https://example.invalid/not-the-frozen-url", "application/atom+xml", "200", "DIGEST", "12"],
    ]).encode("utf-8")
    with pytest.raises(ProbeError):
        parse_cdx_body(body, EXPECTED_RECORDS[0]["source_url"])


def test_fallback_receipt_is_fail_closed_and_verifiable():
    receipt = build_fallback_receipt(123456, source_requests_known_zero=True, reason="PREFLIGHT_FAILED_NO_SOURCE_REQUESTS")
    validate_receipt(receipt)
    assert receipt["status"] == "PREFLIGHT_FAILED_NO_SOURCE_REQUESTS"
    assert receipt["source_contract"]["archive_metadata_requests_attempted"] == 0
    assert receipt["safety"]["paper_only"] is True
    assert receipt["safety"]["historical_first_public_observation_proven"] is False


def test_receipt_fingerprint_detects_mutation():
    receipt = build_fallback_receipt(123456, source_requests_known_zero=True, reason="PREFLIGHT_FAILED_NO_SOURCE_REQUESTS")
    mutated = dict(receipt)
    mutated["status"] = "Q221_WAYBACK_CDX_METADATA_COMPLETE"
    with pytest.raises(ProbeError):
        validate_receipt(mutated)


def test_changed_request_marker_is_rejected(tmp_path):
    original = (ROOT / REQUEST_PATH).read_text(encoding="utf-8")
    path = tmp_path / "marker.trigger"
    path.write_text(original.replace("MAX_REQUESTS=4", "MAX_REQUESTS=5"), encoding="utf-8")
    with pytest.raises(ProbeError):
        read_marker(path)
