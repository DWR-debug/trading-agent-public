from __future__ import annotations

from pathlib import Path
import json

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


def test_q120r2_mocked_full_run_writes_utc_receipt(tmp_path):
    from datetime import datetime, timezone

    from automation import q120r2_cftc_release_exception_inventory as q120r2_module

    request_path = ROOT / "research/run_requests/q120r2_cftc_release_exception_inventory.trigger"
    upstream = {
        "task_id": q120r2_module.UPSTREAM_TASK_ID,
        "status": "Q120_SOURCE_ARCHIVE_AND_RELEASE_SCHEDULE_FEASIBILITY_COMPLETED",
        "receipt_fingerprint": q120r2_module.UPSTREAM_RECEIPT_FINGERPRINT,
        "release_dates_recovered": False,
        "safety": {"paper_only": True, "live_trading_enabled": False},
    }
    upstream_path = tmp_path / "upstream.json"
    upstream_path.write_text(json.dumps(upstream), encoding="utf-8")
    output_path = tmp_path / "receipt.json"
    requested = []

    def fake_fetcher(url, max_bytes):
        requested.append(url)
        if url == q120r2_module.RELEASE_SCHEDULE_URL:
            body = b"<html><body>3:30 p.m. Eastern time; 2026 Release Schedule</body></html>"
        elif url == q120r2_module.SPECIAL_ANNOUNCEMENTS_URL:
            body = (
                "<html><table><tr><th>COT Report Date</th><th>Original Publish Date</th>"
                "<th>New Publish Date</th></tr><tr><td>09/30/2025</td><td>10/03/2025</td>"
                "<td>11/19/2025+</td></tr></table></html>"
            ).encode("utf-8")
        else:
            raise AssertionError(f"unexpected Q120 source URL: {url}")
        if isinstance(body, str):
            body = body.encode("utf-8")
        assert len(body) <= max_bytes
        return 200, body, {"content-type": "text/html; charset=utf-8"}, url, None

    result = q120r2_module.run(
        request_path, upstream_path, output_path, fetcher=fake_fetcher
    )
    assert requested == [
        q120r2_module.RELEASE_SCHEDULE_URL,
        q120r2_module.SPECIAL_ANNOUNCEMENTS_URL,
    ]
    assert result["status"] == "Q120R2_CFTC_RELEASE_EXCEPTION_INVENTORY_COMPLETED"
    stamp = datetime.fromisoformat(result["generated_at_utc"])
    assert stamp.tzinfo is not None
    assert stamp.utcoffset() == timezone.utc.utcoffset(stamp)
    assert result["summary"]["official_exception_rows_parsed"] == 1
    assert result["summary"]["request_count"] == 2
    assert json.loads(output_path.read_text(encoding="utf-8")) == result



def test_q120r2_preserves_multiple_dated_schedule_versions_for_same_report_date():
    html = """
    <p><strong>December 9, 2025:</strong> revised catch-up schedule</p>
    <table>
      <tr><th>COT Report Date</th><th>Original Publish Date</th><th>New Publish Date</th></tr>
      <tr><td>11/10/2025</td><td>11/14/2025</td><td>12/10/2025</td></tr>
    </table>
    <p><strong>November 18, 2025:</strong> earlier catch-up schedule</p>
    <table>
      <tr><th>COT Report Date</th><th>Original Publish Date</th><th>New Publish Date</th></tr>
      <tr><td>11/10/2025</td><td>11/14/2025</td><td>12/12/2025</td></tr>
    </table>
    """
    rows = parse_exception_rows(html)
    versions = [row for row in rows if row["report_date"] == "2025-11-10"]
    assert len(versions) == 2
    assert {
        row["announcement_date"]: row["official_new_publish_date"]
        for row in versions
    } == {
        "2025-12-09": "2025-12-10",
        "2025-11-18": "2025-12-12",
    }
    assert all(row["official_original_publish_date"] == "2025-11-14" for row in versions)
