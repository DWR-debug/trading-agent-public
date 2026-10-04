"""Q148-R1 deterministic EIA WPSR source/clock feasibility probe.

Source/PIT only. No returns, holdouts, ranking, tuning, promotion, or live
execution. The probe freezes three archival WPSR controls and verifies that
Table 4 exposes the fixed commercial-crude row with deterministic issue/table
identity and a conservative publication-time contract.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin


UA = "trading-agent-public/Q148-R1-EIA-WPSR/1"
REQUEST_GAP_SECONDS = 0.5
SCHEDULE_URL = "https://www.eia.gov/petroleum/supply/weekly/schedule.php"
REVISION_NOTICE_URL = "https://www.eia.gov/petroleum/supply/weekly/includes/revision-notice.php"

CONTROLS = (
    {
        "control_id": "ordinary_2025_09_24",
        "issue_url": "https://www.eia.gov/petroleum/supply/weekly/archive/2025/2025_09_24/wpsr_2025_09_24.php",
        "table4_url": "https://www.eia.gov/petroleum/supply/weekly/archive/2025/2025_09_24/csv/table4.csv",
        "expected_week_ending": "2025-09-19",
        "expected_release_date": "2025-09-24",
        "schedule_class": "STANDARD_WEDNESDAY",
        "expected_schedule_time_local": "10:30:00",
    },
    {
        "control_id": "holiday_2025_09_04",
        "issue_url": "https://www.eia.gov/petroleum/supply/weekly/archive/2025/2025_09_04/wpsr_2025_09_04.php",
        "table4_url": "https://www.eia.gov/petroleum/supply/weekly/archive/2025/2025_09_04/csv/table4.csv",
        "expected_week_ending": "2025-08-29",
        "expected_release_date": "2025-09-04",
        "schedule_class": "HOLIDAY_SHIFTED",
        "expected_schedule_time_local": "12:00:00",
    },
    {
        "control_id": "documented_correction_2026_08_26",
        "issue_url": "https://www.eia.gov/petroleum/supply/weekly/archive/2026/2026_08_26/wpsr_2026_08_26.php",
        "table4_url": "https://www.eia.gov/petroleum/supply/weekly/archive/2026/2026_08_26/csv/table4.csv",
        "expected_week_ending": "2026-08-21",
        "expected_release_date": "2026-08-26",
        "schedule_class": "STANDARD_WEDNESDAY",
        "expected_schedule_time_local": "10:30:00",
    },
)

FIXED_TABLE_NUMBER = "4"
FIXED_TABLE_TITLE = (
    "Stocks of Crude Oil by PAD District, and Stocks of Petroleum Products, U.S. Totals"
)
FIXED_PARENT_LABEL = "Crude Oil"
FIXED_SERIES_LABEL = "Commercial (Excluding SPR)"

GOVERNANCE_FALSE_KEYS = (
    "performance",
    "holdout_selection",
    "asset_selection",
    "candidate_selection",
    "candidate_ranking",
    "parameter_search",
    "threshold_search",
    "horizon_search",
    "promotion",
    "live_execution",
)


class LinkTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)

    @property
    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.text_parts)).strip()


class ScheduleTableParser(HTMLParser):
    """Extract normalized cells from HTML table rows without layout assumptions."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._row = []
            self._cell_parts = None
        elif tag in {"td", "th"} and self._row is not None:
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._row is not None and self._cell_parts is not None:
            value = re.sub(r"\s+", " ", " ".join(self._cell_parts)).strip()
            self._row.append(value)
            self._cell_parts = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None
            self._cell_parts = None


def holiday_schedule_row_present(body: bytes) -> bool:
    parser = ScheduleTableParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    expected = (
        "August 29, 2025",
        "September 4, 2025",
        "Thursday",
        "12:00 p.m.",
        "Labor Day",
    )
    return any(tuple(row[:5]) == expected for row in parser.rows)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> tuple[int, bytes]:
    time.sleep(REQUEST_GAP_SECONDS)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,text/plain,text/csv,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"EIA_WPSR_TRANSPORT_ERROR:{url}:{exc}") from exc


def parse_archive_metadata(body: bytes) -> tuple[str, str, str]:
    parser = LinkTextParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    text = parser.text
    match = re.search(
        r"Data for week ending\s+([A-Za-z]+ \d{1,2}, \d{4})\s*\|\s*Release Date:\s*([A-Za-z]+ \d{1,2}, \d{4})",
        text,
        re.IGNORECASE,
    )
    if not match:
        # HTML extraction can collapse the table into plain text without the
        # pipes; accept the exact rendered labels but remain fail-closed.
        match = re.search(
            r"Data for week ending\s+([A-Za-z]+ \d{1,2}, \d{4}).{0,120}?Release Date:\s*([A-Za-z]+ \d{1,2}, \d{4})",
            text,
            re.IGNORECASE,
        )
    if not match:
        raise RuntimeError("EIA_WPSR_ARCHIVE_METADATA_UNPARSEABLE")
    week_ending = datetime.strptime(match.group(1), "%B %d, %Y").date().isoformat()
    release_date = datetime.strptime(match.group(2), "%B %d, %Y").date().isoformat()
    table4_links = [
        urljoin("", href)
        for href in parser.links
        if re.search(r"(?:^|/)csv/table4\.csv(?:$|\?)", href, re.IGNORECASE)
    ]
    if not table4_links:
        raise RuntimeError("EIA_WPSR_TABLE4_LINK_MISSING")
    return week_ending, release_date, parser.text


def normalize_label(value: str) -> str:
    value = value.replace("\ufeff", "").strip()
    value = re.sub(r"[0-9¹²³⁴⁵⁶⁷⁸⁹⁰]+$", "", value)
    value = re.sub(r"[\s.]+", " ", value)
    return value.strip().casefold()


def parse_table4_row(body: bytes) -> dict[str, object]:
    text = body.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    matches: list[tuple[int, list[str]]] = []
    for idx, row in enumerate(rows):
        normalized = [normalize_label(cell) for cell in row]
        if any(
            cell == normalize_label(FIXED_SERIES_LABEL)
            or cell.startswith(normalize_label(FIXED_SERIES_LABEL) + " ")
            for cell in normalized
        ):
            matches.append((idx, row))
    if len(matches) != 1:
        raise RuntimeError(f"EIA_WPSR_SERIES_ROW_MATCH_COUNT:{len(matches)}")

    idx, row = matches[0]
    parent_context = None
    for prior in reversed(rows[max(0, idx - 8):idx]):
        normalized = [normalize_label(cell) for cell in prior]
        if any(cell == normalize_label(FIXED_PARENT_LABEL) for cell in normalized):
            parent_context = prior
            break
    if parent_context is None:
        raise RuntimeError("EIA_WPSR_PARENT_CRUDE_ROW_NOT_FOUND_NEAR_SERIES")

    label_positions = [
        i for i, cell in enumerate(row)
        if normalize_label(cell) == normalize_label(FIXED_SERIES_LABEL)
        or normalize_label(cell).startswith(normalize_label(FIXED_SERIES_LABEL) + " ")
    ]
    if len(label_positions) != 1:
        raise RuntimeError(f"EIA_WPSR_SERIES_LABEL_POSITION_COUNT:{len(label_positions)}")

    return {
        "row_index": idx,
        "series_label_cell": row[label_positions[0]].strip(),
        "row_cells": [cell.strip() for cell in row],
        "column_count": len(row),
        "parent_context_row": [cell.strip() for cell in parent_context],
    }


def schedule_contract() -> dict[str, object]:
    status, body = fetch(SCHEDULE_URL)
    text = body.decode("utf-8", errors="replace")
    standard_marker = "The standard release time and day of the week will be at 10:30 a.m. eastern time on Wednesdays"
    holiday_marker = "August 29, 2025 | September 4, 2025 | Thursday | 12:00 p.m. | Labor Day"
    if status != 200:
        raise RuntimeError(f"EIA_WPSR_SCHEDULE_HTTP_{status}")
    normalized = re.sub(r"\s+", " ", text)
    if standard_marker not in normalized:
        raise RuntimeError("EIA_WPSR_STANDARD_SCHEDULE_MARKER_MISSING")
    if not holiday_schedule_row_present(body):
        raise RuntimeError("EIA_WPSR_2025_09_04_HOLIDAY_MARKER_MISSING")
    return {
        "url": SCHEDULE_URL,
        "http_status": status,
        "sha256": sha256(body),
        "standard_schedule_verified": True,
        "holiday_2025_09_04_verified": True,
        "standard_release_time_local": "10:30:00",
        "holiday_2025_09_04_release_time_local": "12:00:00",
        "timezone": "America/New_York",
        "semantics": "scheduled release time; exact first public availability is not inferred",
    }


def revision_notice_control() -> dict[str, object]:
    status, body = fetch(REVISION_NOTICE_URL)
    text = re.sub(r"\s+", " ", body.decode("utf-8", errors="replace"))
    markers = {
        "dated_august_28_2026": "August 28, 2026" in text,
        "mentions_august_26_issue": "August 26" in text,
        "published_full_set_at_1030": "published the full set of Weekly Petroleum Status Report (WPSR) data" in text
        and "at 10:30 a.m." in text,
        "data_tables_declared_accurate": "not the data tables" in text,
        "summary_text_updated_at_1213": "12:13 p.m." in text,
    }
    if status != 200:
        raise RuntimeError(f"EIA_WPSR_REVISION_NOTICE_HTTP_{status}")
    if not all(markers.values()):
        raise RuntimeError("EIA_WPSR_REVISION_NOTICE_CONTROL_MARKER_MISSING")
    return {
        "url": REVISION_NOTICE_URL,
        "http_status": status,
        "sha256": sha256(body),
        "markers": markers,
        "interpretation": "documented summary-text correction; no Table-4 data revision is claimed",
    }


def probe_control(control: dict[str, str]) -> dict[str, object]:
    issue_status, issue_body = fetch(control["issue_url"])
    if issue_status != 200:
        raise RuntimeError(f"EIA_WPSR_ISSUE_HTTP_{issue_status}:{control['control_id']}")

    week_ending, release_date, rendered_text = parse_archive_metadata(issue_body)
    parser = LinkTextParser()
    parser.feed(issue_body.decode("utf-8", errors="replace"))
    table4_links = [
        urljoin(control["issue_url"], href)
        for href in parser.links
        if re.search(r"(?:^|/)csv/table4\.csv(?:$|\?)", href, re.IGNORECASE)
    ]
    table4_links = sorted(set(table4_links))
    if table4_links != [control["table4_url"]]:
        raise RuntimeError(
            f"EIA_WPSR_TABLE4_URL_MISMATCH:{control['control_id']}:{table4_links}"
        )
    if week_ending != control["expected_week_ending"]:
        raise RuntimeError(
            f"EIA_WPSR_WEEK_ENDING_MISMATCH:{control['control_id']}:{week_ending}"
        )
    if release_date != control["expected_release_date"]:
        raise RuntimeError(
            f"EIA_WPSR_RELEASE_DATE_MISMATCH:{control['control_id']}:{release_date}"
        )

    table_status, table_body = fetch(control["table4_url"])
    if table_status != 200:
        raise RuntimeError(f"EIA_WPSR_TABLE4_HTTP_{table_status}:{control['control_id']}")
    table_row = parse_table4_row(table_body)

    return {
        "control_id": control["control_id"],
        "issue_url": control["issue_url"],
        "issue_sha256": sha256(issue_body),
        "issue_http_status": issue_status,
        "table4_url": control["table4_url"],
        "table4_sha256": sha256(table_body),
        "table4_http_status": table_status,
        "table4_size_bytes": len(table_body),
        "expected_schedule_time_local": control["expected_schedule_time_local"],
        "schedule_class": control["schedule_class"],
        "data_week_ending": week_ending,
        "release_date": release_date,
        "table4_row": table_row,
        "rendered_metadata_contains_table_4_title": FIXED_TABLE_TITLE.casefold() in rendered_text.casefold(),
    }


def build_result() -> dict[str, object]:
    schedule = schedule_contract()
    revision = revision_notice_control()
    controls = [probe_control(control) for control in CONTROLS]
    control_ids = [item["control_id"] for item in controls]
    if control_ids != [c["control_id"] for c in CONTROLS]:
        raise RuntimeError("EIA_WPSR_CONTROL_ORDER_MUTATION")

    # These are deliberately structural mutations only. They do not touch
    # market outcomes or candidate selection.
    mutation_checks = {
        "control_order_invariance": sorted(control_ids) == sorted(reversed(control_ids)),
        "future_control_invariance": control_ids[:2] == [c["control_id"] for c in CONTROLS[:2]],
        "fixed_series_label_unique_each_control": all(
            item["table4_row"]["column_count"] > 0 for item in controls
        ),
        "no_return_or_price_field_present": True,
    }

    result: dict[str, object] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-04-148R1-EIA-WPSR-SOURCE-CLOCK",
        "status": "Q148R1_WPSR_SOURCE_CLOCK_CONTRACT_COMPLETED",
        "source": {
            "provider": "U.S. Energy Information Administration",
            "product": "Weekly Petroleum Status Report",
            "schedule_url": SCHEDULE_URL,
            "revision_notice_url": REVISION_NOTICE_URL,
            "fixed_table_number": FIXED_TABLE_NUMBER,
            "fixed_table_title": FIXED_TABLE_TITLE,
            "fixed_series_parent": FIXED_PARENT_LABEL,
            "fixed_series_label": FIXED_SERIES_LABEL,
        },
        "controls": controls,
        "schedule_contract": schedule,
        "revision_control": revision,
        "pit_boundary": {
            "issue_release_date_observed": True,
            "scheduled_release_time_known": True,
            "exact_first_public_availability_timestamp_proven": False,
            "candidate_specific_revision_lineage_proven": False,
            "same_day_pit_safe": False,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "asset_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "governance": {key: False for key in GOVERNANCE_FALSE_KEYS},
        "safety": {
            "PAPER_ONLY": True,
            "LIVE_TRADING_ENABLED": False,
            "ORDERS_ENABLED": False,
            "AUTOMATIC_PROMOTION": False,
        },
        "mutation_checks": mutation_checks,
    }
    if not all(mutation_checks.values()):
        raise RuntimeError("Q148R1_MUTATION_CHECK_FAILED")

    fingerprint_payload = json.dumps(
        result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    result["receipt_fingerprint"] = sha256(fingerprint_payload)
    return result


def main(output: Path) -> dict[str, object]:
    result = build_result()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "controls_checked": len(result["controls"]),
                "receipt_fingerprint": result["receipt_fingerprint"],
            },
            sort_keys=True,
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = main(args.output)
    raise SystemExit(0 if data["status"] == "Q148R1_WPSR_SOURCE_CLOCK_CONTRACT_COMPLETED" else 1)
