from __future__ import annotations

import argparse
import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

from automation import q121r1_sec_reverse_issuer_coverage as r1


WINDOW_START = "2024-02-05"
WINDOW_END = "2025-09-24"
FORMS = ("SC 13D", "SC 13G", "SC 13D/A", "SC 13G/A")
TARGET_ISSUERS = {
    "SPGI": "0000064040",
    "NDAQ": "0001120193",
    "AMP": "0000820027",
    "RJF": "0000720005",
    "WMB": "0000107263",
    "VLO": "0001035002",
    "DVN": "0001090012",
    "EMN": "0000915389",
}
TARGET_BY_CIK = {cik: symbol for symbol, cik in TARGET_ISSUERS.items()}
ET = ZoneInfo("America/New_York")
STANDARD_CUTOFF = dtime(17, 30, 0)
DISSEMINATION_CUTOFF = dtime(22, 0, 0)
R5_ROW_MULTICHET = "7251f0e25d7293802d389cac875abfd8552b9441ac604b69918bd7d5b9aec554"
R5_ROW_COUNT = 61818
DEFAULT_WORKERS = 8
DEFAULT_REQUEST_GAP_SECONDS = 0.13
UA = "trading-agent-public/Q121R6-sec-acceptance-time-compilation/1"


def sha256_json(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class RateLimiter:
    def __init__(self, gap_seconds: float) -> None:
        self.gap_seconds = gap_seconds
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait_for = self._next_allowed - now
            if wait_for > 0:
                time.sleep(wait_for)
            self._next_allowed = time.monotonic() + self.gap_seconds


def http_get(url: str, limiter: RateLimiter, retries: int = 3) -> tuple[int, bytes]:
    last_error: str | None = None
    for attempt in range(retries):
        limiter.wait()
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "text/html,text/plain,*/*",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                return int(getattr(response, "status", 200)), response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read()
            status = int(exc.code)
            last_error = f"HTTP_{status}"
            if status not in {429, 500, 502, 503, 504}:
                return status, body
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = f"TRANSPORT:{exc!r}"
        if attempt + 1 < retries:
            time.sleep(min(8.0, 2.0 ** attempt))
    raise RuntimeError(f"SEC_HEADER_FETCH_FAILED:{url}:{last_error or 'unknown'}")


def archive_header_url(filename: str) -> str:
    parts = filename.split("/")
    if len(parts) < 4 or parts[0] != "edgar" or parts[1] != "data":
        raise ValueError(f"INVALID_ARCHIVE_FILENAME:{filename}")
    cik = str(int(parts[2]))
    accession = r1.accession_from_filename(filename).replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/"
        f"{accession}-index-headers.html"
    )


def extract_header_value(text: str, label: str) -> str | None:
    compact = r1.plain_text(text)
    match = re.search(rf"{re.escape(label)}\s*:?\s*([0-9A-Za-z./:-]+)", compact, re.IGNORECASE)
    return match.group(1) if match else None


def extract_acceptance_datetime(text: str) -> str | None:
    match = re.search(
        r"ACCEPTANCE-DATETIME\s*[:=>]?\s*([0-9]{14})",
        r1.unescape(text),
        re.IGNORECASE,
    )
    if match:
        raw = match.group(1)
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]} {raw[8:10]}:{raw[10:12]}:{raw[12:14]}"
    return r1.extract_accepted(text)


def extract_submission_type(text: str) -> str | None:
    compact = r1.plain_text(text)
    patterns = (
        r"CONFORMED\s+SUBMISSION\s+TYPE\s*:?\s*([A-Z0-9/ ]+?)(?=\s+(?:PUBLIC DOCUMENT COUNT|CONFORMED PERIOD|FILED AS OF DATE|DATE AS OF CHANGE)\b|$)",
        r"\bType:\s*(SC\s+13[DG](?:/A)?)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, compact, re.IGNORECASE)
        if match:
            value = re.sub(r"\s+", " ", match.group(1)).strip().upper()
            if value in {x.upper() for x in FORMS}:
                return value
    return None


def classify_acceptance(filing_date: str, accepted_datetime: str) -> dict[str, object]:
    filing = date.fromisoformat(filing_date)
    accepted = datetime.fromisoformat(accepted_datetime).replace(tzinfo=ET)
    acceptance_date = accepted.date()
    local_time = accepted.timetz().replace(tzinfo=None)
    date_matches = acceptance_date == filing
    if not date_matches:
        event_class = "OUT_OF_CONTRACT"
    elif local_time < STANDARD_CUTOFF:
        event_class = "STANDARD_DAY"
    elif local_time <= DISSEMINATION_CUTOFF:
        event_class = "LATE_DAY_SAME_DATE"
    else:
        event_class = "OUT_OF_CONTRACT"
    return {
        "acceptance_datetime_local": accepted.isoformat(),
        "acceptance_calendar_date": acceptance_date.isoformat(),
        "acceptance_local_time": local_time.isoformat(),
        "filing_date_matches_acceptance_date": date_matches,
        "event_class": event_class,
        "timezone": "America/New_York",
    }


def stable_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row["cik"],
        row["form"],
        row["filed_date"],
        row["accession_number"],
    )


def key_fingerprint(rows: list[dict[str, str]]) -> str:
    keys = [stable_key(row) for row in rows]
    return sha256_json(keys)


def compile_header(row: dict[str, str], body: bytes) -> dict[str, object]:
    text = body.decode("utf-8", errors="replace")
    subject = r1.extract_header_section_cik(text, "Subject") or r1.extract_labeled_cik(text, "Subject")
    filer = r1.extract_header_section_cik(text, "Filed by") or r1.extract_labeled_cik(text, "Filed by")
    accepted = extract_acceptance_datetime(text)
    filed_as_of = extract_header_value(text, "FILED AS OF DATE")
    date_as_change = extract_header_value(text, "DATE AS OF CHANGE")
    accession_header = extract_header_value(text, "ACCESSION NUMBER")
    submission_type = extract_submission_type(text)

    if not subject:
        raise RuntimeError(f"MISSING_SUBJECT_CIK:{row['accession_number']}")
    if not filer:
        raise RuntimeError(f"MISSING_FILED_BY_CIK:{row['accession_number']}")
    if not accepted:
        raise RuntimeError(f"MISSING_ACCEPTANCE_DATETIME:{row['accession_number']}")
    if filed_as_of and filed_as_of.replace("-", "") != row["filed_date"].replace("-", ""):
        raise RuntimeError(
            f"FILED_DATE_MISMATCH:{row['accession_number']}:{row['filed_date']}:{filed_as_of}"
        )
    if accession_header and accession_header != row["accession_number"]:
        raise RuntimeError(
            f"ACCESSION_MISMATCH:{row['accession_number']}:{accession_header}"
        )
    if submission_type and submission_type.upper() != row["form"].upper():
        raise RuntimeError(
            f"FORM_MISMATCH:{row['accession_number']}:{row['form']}:{submission_type}"
        )
    if filer != row["cik"]:
        raise RuntimeError(
            f"INDEX_FILERC_CIK_MISMATCH:{row['accession_number']}:{row['cik']}:{filer}"
        )

    timing = classify_acceptance(row["filed_date"], accepted)
    event = {
        "canonical_key": {
            "cik": row["cik"],
            "form": row["form"],
            "filed_date": row["filed_date"],
            "accession_number": row["accession_number"],
        },
        "subject_cik": subject,
        "subject_symbol": TARGET_BY_CIK.get(subject),
        "filed_by_cik": filer,
        "accepted_datetime": accepted,
        "filed_as_of_date": filed_as_of,
        "date_as_of_change": date_as_change,
        "submission_type": submission_type,
        **timing,
    }
    event["target_issuer_match"] = subject in TARGET_BY_CIK
    return event


def compile_shard(
    population: list[dict[str, str]],
    *,
    shard_index: int,
    shard_count: int,
    request_gap_seconds: float,
    workers: int,
) -> dict[str, object]:
    if not 0 <= shard_index < shard_count:
        raise ValueError("SHARD_INDEX_OUT_OF_RANGE")
    if len(population) != R5_ROW_COUNT:
        raise RuntimeError(f"R5_ROW_COUNT_MISMATCH:{len(population)}")
    if key_fingerprint(population) != R5_ROW_MULTICHET:
        raise RuntimeError("R5_ROW_MULTISE T_FINGERPRINT_MISMATCH")
    ordered = sorted(population, key=stable_key)
    start = (len(ordered) * shard_index) // shard_count
    end = (len(ordered) * (shard_index + 1)) // shard_count
    rows = ordered[start:end]
    limiter = RateLimiter(request_gap_seconds)
    records: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []

    def fetch_one(row: dict[str, str]) -> dict[str, object]:
        url = archive_header_url(row["filename"])
        status, body = http_get(url, limiter)
        if status != 200:
            raise RuntimeError(f"SEC_HEADER_HTTP_{status}:{row['accession_number']}")
        header = compile_header(row, body)
        return {
            "canonical_key": stable_key(row),
            "header_sha256": hashlib.sha256(body).hexdigest(),
            "source_url": url,
            "header": header,
        }

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_one, row): row for row in rows}
        for future in as_completed(futures):
            row = futures[future]
            try:
                records.append(future.result())
            except Exception as exc:
                failures.append(
                    {
                        "accession_number": row["accession_number"],
                        "cik": row["cik"],
                        "form": row["form"],
                        "filed_date": row["filed_date"],
                        "error": str(exc),
                    }
                )

    records.sort(key=lambda item: tuple(item["canonical_key"]))
    header_hash_aggregate = hashlib.sha256(
        "".join(f"{json.dumps(r['canonical_key'], sort_keys=True)}:{r['header_sha256']}\n" for r in records).encode("utf-8")
    ).hexdigest()

    status = "COMPLETED" if not failures and len(records) == len(rows) else "INCOMPLETE_HEADER_SCAN"
    return {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-121R6-SEC-ACCEPTANCE-TIME-COMPILATION",
        "status": status,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "population_count": len(population),
        "slice_start": start,
        "slice_end_exclusive": end,
        "slice_count": len(rows),
        "population_fingerprint": R5_ROW_MULTICHET,
        "records_fetched": len(records),
        "failures": failures,
        "header_hash_aggregate": header_hash_aggregate,
        "records": records,
        "scientific_boundary": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--population", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, default=16)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--request-gap-seconds", type=float, default=DEFAULT_REQUEST_GAP_SECONDS)
    args = parser.parse_args()

    population_payload = json.loads(args.population.read_text(encoding="utf-8"))
    population = population_payload["rows"]
    if population_payload.get("row_count") != R5_ROW_COUNT:
        raise SystemExit("POPULATION_ARTIFACT_ROW_COUNT_MISMATCH")
    if population_payload.get("row_multiset_fingerprint") != R5_ROW_MULTICHET:
        raise SystemExit("POPULATION_ARTIFACT_FINGERPRINT_MISMATCH")

    result = compile_shard(
        population,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
        request_gap_seconds=args.request_gap_seconds,
        workers=args.workers,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if result["status"] != "COMPLETED":
        raise SystemExit("Q121R6_SHARD_INCOMPLETE")


if __name__ == "__main__":
    main()
