import json
from pathlib import Path

import pytest

from automation.wayback_cdx_metadata import (
    MetadataProbeError,
    build_cdx_url,
    canonical_fingerprint,
    parse_cdx_rows,
)
from automation.q127r2_finra_wayback_metadata import (
    FIXED_DATES,
    LISTING_URL,
    R1_FP,
    TARGET_URLS,
    validate_r1,
)


def test_cdx_query_is_exact_and_bounded():
    url = build_cdx_url(TARGET_URLS["2024-02-05"], from_year=2024, to_year=2026, limit=100)
    assert url.startswith("https://web.archive.org/cdx/search/cdx?")
    assert "matchType=exact" in url
    assert "limit=100" in url
    assert "CNMSshvol20240205.txt" in url


def test_cdx_empty_result_is_a_valid_negative_not_a_parse_failure():
    assert parse_cdx_rows(b"[]", expected_original=TARGET_URLS["2024-02-05"]) == []


def test_cdx_rows_keep_only_exact_expected_original():
    body = json.dumps([
        ["timestamp", "original", "statuscode", "digest", "length"],
        ["20240722180837", TARGET_URLS["2024-07-01"], "200", "ABC", "323000"],
    ]).encode()
    rows = parse_cdx_rows(body, expected_original=TARGET_URLS["2024-07-01"])
    assert rows[0]["timestamp"] == "20240722180837"
    assert rows[0]["length"] == "323000"


def test_cdx_rejects_other_url_even_if_index_returns_it():
    body = json.dumps([
        ["timestamp", "original", "statuscode", "digest", "length"],
        ["20240722180837", "https://example.invalid/file.txt", "200", "ABC", "12"],
    ]).encode()
    with pytest.raises(MetadataProbeError, match="CDX_CAPTURE_URL_MISMATCH"):
        parse_cdx_rows(body, expected_original=TARGET_URLS["2024-07-01"])


def test_q127_upstream_pins_and_fixed_dates_are_unchanged():
    assert len(FIXED_DATES) == 4
    assert R1_FP == "2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c"
    receipt = {
        "task_id": "Q-2026-10-03-127R1-FINRA-REGSHO-HISTORICAL-PIT",
        "status": "Q127R1_SOURCE_PIT_FEASIBILITY_COMPLETED",
        "receipt_fingerprint": R1_FP,
        "pit": {"same_day_pit_safe": False, "revision_lineage_established": False},
        "observations": {
            date: {
                "source_url": TARGET_URLS[date],
                "status": "PASS",
                "rows_for_fixed_symbols": {symbol: [{}] for symbol in ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")},
            }
            for date in FIXED_DATES
        },
    }
    validate_r1(receipt)


def test_receipt_fingerprint_is_stable_and_excludes_only_itself():
    receipt = {"status": "NO_SUPPORT", "performance_authorized": False}
    first = canonical_fingerprint(receipt)
    receipt["receipt_fingerprint"] = "ignored"
    assert canonical_fingerprint(receipt) == first
