"""Q127-R1 FINRA Reg-SHO historical source/PIT feasibility probe.

This is source/PIT feasibility only. It never reads prices, returns, holdouts,
performance outputs, ranking or promotion state.

The probe fetches a fixed historical sample of the public Consolidated NMS
Daily Short Sale Volume file, preserves raw fingerprints and parses exact
rows for a fixed symbol universe. Revision lineage is deliberately not claimed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

FINRA_PAGE_URL = (
    "https://www.finra.org/finra-data/browse-catalog/"
    "short-sale-volume-data/daily-short-sale-volume-files"
)
URL_TEMPLATE = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{yyyymmdd}.txt"
DATES = ("2024-02-05", "2024-07-01", "2025-01-02", "2025-09-24")
SYMBOLS = ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")
EXPECTED_HEADER = ("Date", "Symbol", "ShortVolume", "ShortExemptVolume", "TotalVolume", "Market")
UA = "trading-agent-public/Q127R1-finra-regsho-historical-pit/1"

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fetch(url: str) -> tuple[int, bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "text/plain,text/html,*/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return int(getattr(response, "status", 200)), response.read(), {
                k.lower(): v for k, v in response.headers.items()
            }
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), {}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"FINRA_TRANSPORT_ERROR:{url}:{exc}") from exc

def parse_file(body: bytes) -> tuple[tuple[str, ...], dict[str, list[dict[str, str]]], list[str], int]:
    text = body.decode("utf-8-sig", errors="strict")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("FINRA_EMPTY_FILE")
    header = tuple(lines[0].split("|"))
    if header != EXPECTED_HEADER:
        raise RuntimeError(f"FINRA_SCHEMA_MISMATCH:{header!r}")

    payload = lines[1:]
    if not payload:
        raise RuntimeError("FINRA_TRAILER_MISSING")
    trailer = payload[-1]
    if "|" in trailer or not trailer.isdigit():
        raise RuntimeError(f"FINRA_TRAILER_INVALID:{trailer[:120]!r}")
    trailer_count = int(trailer)
    data_lines = payload[:-1]

    rows: dict[str, list[dict[str, str]]] = {}
    seen_keys: set[tuple[str, str]] = set()
    for line in data_lines:
        parts = line.split("|")
        if len(parts) != len(EXPECTED_HEADER):
            raise RuntimeError(f"FINRA_ROW_WIDTH_MISMATCH:{line[:120]!r}")
        row = dict(zip(EXPECTED_HEADER, parts))
        if not row["Date"] or not row["Symbol"] or not row["Market"]:
            raise RuntimeError("FINRA_ROW_IDENTITY_MISSING")
        if not row["Market"].isalpha() or len(row["Market"]) != 1:
            raise RuntimeError(f"FINRA_MARKET_INVALID:{row['Symbol']}:{row['Market']!r}")
        try:
            numeric = [
                float(row[name])
                for name in ("ShortVolume", "ShortExemptVolume", "TotalVolume")
            ]
        except ValueError as exc:
            raise RuntimeError(f"FINRA_NUMERIC_PARSE_ERROR:{row['Symbol']}") from exc
        if not all(math.isfinite(value) and value >= 0 for value in numeric):
            raise RuntimeError(f"FINRA_NUMERIC_RANGE_ERROR:{row['Symbol']}")

        key = (row["Symbol"], row["Market"])
        if key in seen_keys:
            raise RuntimeError(f"FINRA_DUPLICATE_SYMBOL_MARKET:{row['Symbol']}:{row['Market']}")
        seen_keys.add(key)
        rows.setdefault(row["Symbol"], []).append(row)

    if trailer_count != len(data_lines):
        raise RuntimeError(
            f"FINRA_TRAILER_COUNT_MISMATCH:{trailer_count}!={len(data_lines)}"
        )
    return header, rows, lines, trailer_count

def date_url(value: str) -> str:
    parsed = date.fromisoformat(value)
    return URL_TEMPLATE.format(yyyymmdd=parsed.strftime("%Y%m%d"))

def run(output: Path) -> dict[str, object]:
    page_status, page_body, page_headers = fetch(FINRA_PAGE_URL)
    page_text = page_body.decode("utf-8", errors="replace")
    required_markers = [
        "Daily Short Sale Volume Files",
        "6:00:00pm ET",
        "Updated",
    ]
    missing_markers = [marker for marker in required_markers if marker.lower() not in page_text.lower()]
    if page_status != 200 or missing_markers:
        raise RuntimeError(f"FINRA_PAGE_CONTRACT_FAILED:{page_status}:{missing_markers}")

    observations: dict[str, object] = {}
    for sample_date in DATES:
        url = date_url(sample_date)
        status, body, headers = fetch(url)
        if status != 200:
            raise RuntimeError(f"FINRA_HISTORICAL_FILE_HTTP_{status}:{sample_date}")
        header, rows, lines, trailer_count = parse_file(body)
        expected_date = date.fromisoformat(sample_date).strftime("%Y%m%d")
        wrong_dates = sorted({
            row["Date"]
            for symbol_rows in rows.values()
            for row in symbol_rows
            if row["Date"] != expected_date
        })
        symbol_rows = {symbol: rows[symbol] for symbol in SYMBOLS if symbol in rows}
        missing_symbols = [symbol for symbol in SYMBOLS if symbol not in rows]
        observations[sample_date] = {
            "source_url": url,
            "source_sha256": sha256(body),
            "response_headers": {
                "content_type": headers.get("content-type"),
                "last_modified": headers.get("last-modified"),
                "etag": headers.get("etag"),
            },
            "header": list(header),
            "line_count": len(lines),
            "data_record_count": len(lines) - 2,
            "trailer_count": trailer_count,
            "rows_for_fixed_symbols": symbol_rows,
            "missing_fixed_symbols": missing_symbols,
            "wrong_dates": wrong_dates,
            "status": "PASS" if not wrong_dates else "FAIL",
        }
        if wrong_dates:
            raise RuntimeError(f"FINRA_DATE_MISMATCH:{sample_date}:{wrong_dates}")

    result: dict[str, object] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-127R1-FINRA-REGSHO-HISTORICAL-PIT",
        "status": "Q127R1_SOURCE_PIT_FEASIBILITY_COMPLETED",
        "fixed_dates": list(DATES),
        "fixed_symbols": list(SYMBOLS),
        "source": {
            "page_url": FINRA_PAGE_URL,
            "page_sha256": sha256(page_body),
            "page_headers": {
                "content_type": page_headers.get("content-type"),
                "last_modified": page_headers.get("last-modified"),
                "etag": page_headers.get("etag"),
            },
            "dataset": "Consolidated NMS Daily Short Sale Volume",
            "url_template": URL_TEMPLATE,
        },
        "observations": observations,
        "pit": {
            "publication_upper_bound": "18:00:00 ET same trade date",
            "exact_first_publication_time_proven": False,
            "later_update_possible": True,
            "revision_lineage_established": False,
            "same_day_pit_safe": False,
            "formal_security_identity_established": False,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout": False,
            "ranking": False,
            "selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({
        "status": result["status"],
        "dates": len(DATES),
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
