import json
import pytest

from automation.wayback_cdx_metadata import MetadataProbeError, build_cdx_url, parse_cdx_rows
from automation.q130r2_wikimedia_wayback_metadata import (
    ARTICLES,
    R1_FP,
    START,
    END,
    article_url,
    validate_r1,
)


def test_q130_fixed_api_urls_match_r1_contract():
    assert article_url("S&P Global").endswith("/S%26P_Global/daily/20250920/20250924")
    assert START == "20250920"
    assert END == "20250924"
    assert len(ARTICLES) == 8


def test_q130_exact_cdx_url_targets_historical_api_response_not_live_api():
    original = article_url("S&P Global")
    url = build_cdx_url(original, from_year=2015, to_year=2026, limit=50)
    assert "web.archive.org/cdx/search/cdx" in url
    assert "matchType=exact" in url
    assert "wikimedia.org/api/rest_v1/metrics/pageviews" in url
    assert R1_FP == "4334be29ff2387813ea9586ba12c6899979e0e43125aeaf0585b073063876568"


def test_q130_empty_cdx_is_valid_negative_evidence():
    assert parse_cdx_rows(b"[]", expected_original=article_url("Nasdaq")) == []


def test_q130_rejects_invalid_capture_metadata():
    body = json.dumps([
        ["timestamp", "original", "statuscode", "digest", "length"],
        ["not-a-time", article_url("Nasdaq"), "200", "ABC", "100"],
    ]).encode()
    with pytest.raises(MetadataProbeError, match="CDX_TIMESTAMP_INVALID"):
        parse_cdx_rows(body, expected_original=article_url("Nasdaq"))


def test_q130_upstream_receipt_must_preserve_unresolved_pit_gate():
    receipt = {
        "task_id": "Q-2026-10-03-130R1-WIKIMEDIA-ATTENTION-SOURCE",
        "status": "Q130R1_SOURCE_FEASIBILITY_COMPLETED",
        "receipt_fingerprint": R1_FP,
        "fixed_articles": ARTICLES,
        "feasibility_window": {"start": START, "end": END},
        "pit": {"exact_first_publication_time_proven": False, "revision_lineage_proven": False, "same_day_formal_use_allowed": False},
        "observations": {symbol: {"article": title, "source_url": article_url(title)} for symbol, title in ARTICLES.items()},
    }
    validate_r1(receipt)


def test_q130_uses_only_the_frozen_article_names():
    assert ARTICLES == {
        "SPGI": "S&P Global", "NDAQ": "Nasdaq", "AMP": "Ameriprise Financial",
        "RJF": "Raymond James", "WMB": "Williams Companies", "VLO": "Valero Energy",
        "DVN": "Devon Energy", "EMN": "Eastman Chemical",
    }
