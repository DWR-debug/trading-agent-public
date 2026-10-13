from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from automation.q127r3_finra_commoncrawl_metadata import (
    FROZEN,
    ProbeError,
    parse_cdx_jsonl,
    select_collection,
    read_request,
)

ROOT = Path(__file__).resolve().parents[1]
TARGET = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol20240701.txt"


def test_q127r3_selects_earliest_collection_starting_after_fixed_report_date():
    rows = [
        {"id": "CC-MAIN-2024-26", "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2024-26-index", "from": "2024-06-15T00:00:00Z", "to": "2024-06-30T00:00:00Z"},
        {"id": "CC-MAIN-2024-30", "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2024-30-index", "from": "2024-07-15T00:00:00Z", "to": "2024-07-30T00:00:00Z"},
        {"id": "CC-MAIN-2024-33", "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2024-33-index", "from": "2024-08-01T00:00:00Z", "to": "2024-08-15T00:00:00Z"},
    ]
    chosen = select_collection(rows, "2024-07-01")
    assert chosen is not None
    assert chosen["id"] == "CC-MAIN-2024-30"


def test_q127r3_fails_closed_when_no_collection_starts_within_lookahead_window():
    rows = [
        {"id": "CC-MAIN-2024-33", "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2024-33-index", "from": "2024-08-15T00:00:00Z", "to": "2024-08-31T00:00:00Z"}
    ]
    assert select_collection(rows, "2024-07-01") is None


def test_q127r3_parse_cdx_jsonl_preserves_capture_metadata_without_payload():
    body = (
        '{"timestamp":"20240719090000","url":"' + TARGET + '","status":"200","mime":"text/plain",'
        '"digest":"ABCDEF","length":"350000","filename":"crawl-data/CC-MAIN-2024-30/warc/example.warc.gz","offset":"12345"}\n'
    ).encode()
    rows = parse_cdx_jsonl(body, TARGET)
    assert len(rows) == 1
    assert rows[0]["timestamp"] == "20240719090000"
    assert rows[0]["digest_sha1_base32"] == "ABCDEF"
    assert rows[0]["warc_record_length"] == "350000"


def test_q127r3_empty_index_result_is_valid_negative_metadata():
    assert parse_cdx_jsonl(b"", TARGET) == b"" if False else []


def test_q127r3_rejects_other_url_even_if_index_returns_it():
    wrong = TARGET.replace("20240701", "20240702")
    body = (
        '{"timestamp":"20240719090000","url":"' + wrong + '","status":"200","digest":"ABCDEF",'
        '"length":"10","filename":"x.warc.gz","offset":"1"}\n'
    ).encode()
    with pytest.raises(ProbeError, match="COMMONCRAWL_EXACT_URL_MISMATCH"):
        parse_cdx_jsonl(body, TARGET)


def test_q127r3_live_request_is_frozen():
    request = read_request(ROOT / "research/run_requests/q127r3_finra_commoncrawl_metadata.trigger")
    for key, expected in FROZEN.items():
        assert request[key] == expected
    assert request["PERFORMANCE"] == "false"
    assert request["LIVE_EXECUTION"] == "false"
