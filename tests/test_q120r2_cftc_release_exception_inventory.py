from __future__ import annotations

from pathlib import Path

import pytest

from automation.q120r2_cftc_release_exception_inventory import (
    FROZEN,
    ProbeError,
    parse_exception_rows,
    read_request,
)

ROOT = Path(__file__).resolve().parents[1]


def test_q120r2_parses_official_report_and_publish_dates_and_annotations():
    html = """
    <html><body><table>
      <tr><th>COT Report Date</th><th>Original Publish Date</th><th>New Publish Date</th></tr>
      <tr><td>09/30/2025</td><td>10/03/2025</td><td><a>11/19/2025+</a></td></tr>
      <tr><td>10/07/2025</td><td>10/10/2025</td><td>11/21/2025</td></tr>
      <tr><td>12/23/2025</td><td>12/29/2025</td><td>12/29/2025++</td></tr>
    </table></body></html>
    """
    rows = parse_exception_rows(html)
    assert len(rows) == 3
    assert rows[0]["report_date"] == "2025-09-30"
    assert rows[0]["official_original_publish_date"] == "2025-10-03"
    assert rows[0]["official_new_publish_date"] == "2025-11-19"
    assert rows[0]["publish_date_changed"] is True
    assert rows[2]["publish_date_changed"] is False
    assert rows[2]["new_publish_date_cell"] == "12/29/2025++"


def test_q120r2_deduplicates_exact_rows_but_rejects_conflicting_dates():
    base = """
    <table><tr><th>COT Report Date</th><th>Original Publish Date</th><th>New Publish Date</th></tr>
    <tr><td>09/30/2025</td><td>10/03/2025</td><td>11/19/2025</td></tr>
    """
    repeated = base + '<tr><td>09/30/2025</td><td>10/03/2025</td><td>11/19/2025</td></tr></table>'
    assert len(parse_exception_rows(repeated)) == 1

    conflicting = base + '<tr><td>09/30/2025</td><td>10/03/2025</td><td>11/20/2025</td></tr></table>'
    with pytest.raises(ProbeError, match="Q120R2_CONFLICTING_EXCEPTION_ROWS"):
        parse_exception_rows(conflicting)


def test_q120r2_fails_closed_when_cftc_exception_table_schema_is_missing():
    with pytest.raises(ProbeError, match="Q120R2_EXCEPTION_TABLE_HEADER_NOT_FOUND"):
        parse_exception_rows("<html><table><tr><th>Report Date</th><th>Release Date</th></tr></table></html>")


def test_q120r2_live_request_is_frozen_and_performance_prohibited():
    request = read_request(ROOT / "research/run_requests/q120r2_cftc_release_exception_inventory.trigger")
    for key, expected in FROZEN.items():
        assert request[key] == expected
    assert request["PERFORMANCE"] == "false"
    assert request["LIVE_EXECUTION"] == "false"
