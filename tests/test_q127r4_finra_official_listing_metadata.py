from __future__ import annotations

from pathlib import Path
import json

import pytest

from automation.q127r4_finra_official_listing_metadata import (
    FIXED_DATES,
    FROZEN,
    R1_FP,
    R1_TASK,
    SYMBOLS,
    ProbeError,
    parse_listing_page,
    read_request,
    run,
    target_urls,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture_page(year: int, value: str, rows: list[tuple[str, str]]) -> str:
    links = "".join(
        f'<li><div class="field-content"><a href="{url}">{label}</a> (TXT {size})</div></li>'
        for url, label, size in rows
    )
    return f"""
      <select name="custom_year[year]"><option value="{value}" selected="selected">{year}</option></select>
      <p>FINRA posts the Daily Short Sale Volume Files to this no later than 6:00:00pm ET of the same day on the relevant trade date.</p>
      <p>In rare instances, FINRA may need to update a file on a subsequent day. FINRA will reflect both the original and updated files on this page and will identify the updated file as "Updated."</p>
      <ul>{links}</ul>
    """


def test_q127r4_parses_year_filtered_exact_links_and_size_labels():
    urls = target_urls()
    page = fixture_page(
        2024,
        "2",
        [(urls["2024-02-05"], "Monday 5th", "321 KB"), (urls["2024-07-01"], "Monday 1st", "323 KB")],
    )
    parsed = parse_listing_page(page, 2024, ("2024-02-05", "2024-07-01"))
    assert parsed["selected_year_filter_verified"] is True
    assert parsed["publication_policy_markers"]["by_1800_et_same_trade_date"] is True
    assert parsed["publication_policy_markers"]["later_update_possible"] is True
    assert parsed["publication_policy_markers"]["original_and_updated_both_listed"] is True
    assert parsed["publication_policy_markers"]["updated_variant_is_labelled"] is True
    assert parsed["target_observations"]["2024-02-05"]["listing_rows"][0]["file_size_label"] == "321 KB"
    assert parsed["target_observations"]["2024-07-01"]["exact_url_listed_once"] is True
    assert parsed["target_observations"]["2024-02-05"]["listing_rows"][0]["updated_label_visible_in_row"] is False


def test_q127r4_captures_updated_badge_without_claiming_historical_revision_lineage():
    urls = target_urls()
    page = fixture_page(2025, "1", [(urls["2025-01-02"], "Thursday 2nd Updated", "342 KB")])
    parsed = parse_listing_page(page, 2025, ("2025-01-02",))
    row = parsed["target_observations"]["2025-01-02"]["listing_rows"][0]
    assert row["updated_label_visible_in_row"] is True
    assert parsed["target_observations"]["2025-01-02"]["exact_url_listed_once"] is True


def test_q127r4_fails_closed_for_wrong_selected_year():
    urls = target_urls()
    page = fixture_page(2024, "1", [(urls["2024-02-05"], "Monday 5th", "321 KB")])
    with pytest.raises(ProbeError, match="YEAR_FILTER_NOT_CONFIRMED"):
        parse_listing_page(page, 2024, ("2024-02-05",))


def test_q127r4_preserves_duplicate_target_link_evidence_for_validation():
    urls = target_urls()
    row = (urls["2025-09-24"], "Wednesday 24th", "358 KB")
    page = fixture_page(2025, "1", [row, row])
    parsed = parse_listing_page(page, 2025, ("2025-09-24",))
    assert parsed["target_observations"]["2025-09-24"]["exact_url_listing_count"] == 2
    assert parsed["target_observations"]["2025-09-24"]["exact_url_listed_once"] is False


def test_q127r4_live_request_is_frozen_and_non_authorizing():
    request = read_request(ROOT / "research/run_requests/q127r4_finra_official_listing_metadata.trigger")
    for key, expected in FROZEN.items():
        assert request[key] == expected
    assert request["PERFORMANCE"] == "false"
    assert request["HOLDOUT_SELECTION"] == "false"
    assert request["LIVE_EXECUTION"] == "false"


def test_q127r4_full_probe_never_infers_historical_same_day_pit(tmp_path):
    targets = target_urls()
    upstream = {
        "task_id": R1_TASK,
        "status": "Q127R1_SOURCE_PIT_FEASIBILITY_COMPLETED",
        "receipt_fingerprint": R1_FP,
        "observations": {
            day: {
                "source_url": targets[day],
                "status": "PASS",
                "rows_for_fixed_symbols": {symbol: {} for symbol in SYMBOLS},
            }
            for day in FIXED_DATES
        },
        "pit": {"same_day_pit_safe": False, "revision_lineage_established": False},
    }
    upstream_path = tmp_path / "upstream.json"
    upstream_path.write_text(json.dumps(upstream), encoding="utf-8")
    out_path = tmp_path / "receipt.json"
    rows_2024 = [(targets["2024-02-05"], "Monday 5th", "321 KB"), (targets["2024-07-01"], "Monday 1st", "323 KB")]
    rows_2025 = [(targets["2025-01-02"], "Thursday 2nd", "342 KB"), (targets["2025-09-24"], "Wednesday 24th", "358 KB")]
    pages = {
        2024: fixture_page(2024, "2", rows_2024).encode("utf-8"),
        2025: fixture_page(2025, "1", rows_2025).encode("utf-8"),
    }

    def fake_fetch(url, max_bytes):
        year = 2024 if "custom_year%5Byear%5D=2" in url else 2025
        body = pages[year]
        assert len(body) <= max_bytes
        return 200, body, {"content-type": "text/html", "content-length": str(len(body))}, url, None

    receipt = run(
        ROOT / "research/run_requests/q127r4_finra_official_listing_metadata.trigger",
        upstream_path,
        out_path,
        fetcher=fake_fetch,
    )
    assert receipt["status"] == "Q127R4_OFFICIAL_LISTING_METADATA_COMPLETED"
    assert receipt["summary"]["target_urls_present_exactly_once"] is True
    assert receipt["pit_interpretation"]["official_nominal_publication_upper_bound_stated"] is True
    assert receipt["pit_interpretation"]["publication_statement_historical_applicability_proven"] is False
    assert receipt["pit_interpretation"]["exact_first_publication_time_proven"] is False
    assert receipt["pit_interpretation"]["historical_listing_snapshot_proven"] is False
    assert receipt["pit_interpretation"]["same_day_formal_use_allowed"] is False
