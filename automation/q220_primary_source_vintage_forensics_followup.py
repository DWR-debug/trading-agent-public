"""Separately preregistered bounded Q220 follow-up comparison of frozen primary hashes to original SEC Feed submissions.

This probe does not alter the frozen Q220 receipt, expected hashes, or any research
gate. It retrieves only three preregistered SEC filing-day Feed archives and the
three matching current public primary documents, with strict byte/time ceilings.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import tarfile
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RECEIPT_PATH = "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json"
SOURCE_RECEIPT_GIT_BLOB_SHA = "2a3abbff6c6950e4f11d85dba92cb9c57a5c7ee0"
SOURCE_RECEIPT_FINGERPRINT = "c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075"
SOURCE_POPULATION_RECEIPT_FINGERPRINT = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
EXPECTED_SOURCE_HASH_FAILURE_COUNT = 55
WORKPACK_ID = "Q220-ORIGINAL-FEED-FOLLOWUP-2026-10-12"
SAMPLE_EXPECTED_HASHES = {
    "0000064040|0000064040-19-000059|10-K|2019-02-13": "27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83",
    "0000107263|0000107263-19-000007|10-K|2019-02-21": "bfd1f6fef8d5d4cc60fcc746c08be12a0de5cbd5e3e8fbe4b4847ea5f331a17e",
    "0000064040|0000064040-25-000052|10-K|2025-02-11": "afe05282d5d5af7f3068287cceaa679db962264d5d704d2d32ac19e2c4d3531d",
}
SAMPLE_PRIMARY_NAMES = {
    "0000064040|0000064040-19-000059|10-K|2019-02-13": "spgi-20181231x10k.htm",
    "0000107263|0000107263-19-000007|10-K|2019-02-21": "wmb_20181231x10k.htm",
    "0000064040|0000064040-25-000052|10-K|2025-02-11": "spgi-20241231.htm",
}
SAMPLE_KEYS = tuple(SAMPLE_EXPECTED_HASHES)
MAX_SAMPLE_COUNT = 3
MAX_FEED_ARCHIVE_BYTES = 1_500_000_000
MAX_CURRENT_PRIMARY_BYTES = 15_000_000
MAX_PRIMARY_MEMBER_BYTES = 30_000_000
MAX_TAR_SCAN_BYTES = 12_000_000_000
MAX_TOTAL_DOWNLOAD_BYTES = 4_600_000_000
REQUEST_TIMEOUT_SECONDS = 600
REQUEST_GAP_SECONDS = 1.0
USER_AGENT = "DWR-debug/trading-agent-public Q220 SEC Feed follow-up forensic research@example.invalid"

FROZEN_REQUEST_VALUES = {
    "RUN_Q220_PRIMARY_SOURCE_VINTAGE_FORENSICS": "true",
    "REASON": "FOLLOWUP_FIXED_SAMPLE_AFTER_MEMBER_OVER_LIMIT_BLOCK",
    "WORKPACK_ID": WORKPACK_ID,
    "SOURCE_RECEIPT_PATH": SOURCE_RECEIPT_PATH,
    "SOURCE_RECEIPT_GIT_BLOB_SHA": SOURCE_RECEIPT_GIT_BLOB_SHA,
    "SOURCE_RECEIPT_FINGERPRINT": SOURCE_RECEIPT_FINGERPRINT,
    "SOURCE_POPULATION_RECEIPT_FINGERPRINT": SOURCE_POPULATION_RECEIPT_FINGERPRINT,
    "SOURCE_HASH_FAILURE_COUNT": str(EXPECTED_SOURCE_HASH_FAILURE_COUNT),
    "SAMPLE_COUNT": str(MAX_SAMPLE_COUNT),
    "SAMPLE_RECORD_KEYS": ";".join(SAMPLE_KEYS),
    "MAX_FEED_ARCHIVE_BYTES": str(MAX_FEED_ARCHIVE_BYTES),
    "MAX_CURRENT_PRIMARY_BYTES": str(MAX_CURRENT_PRIMARY_BYTES),
    "MAX_PRIMARY_MEMBER_BYTES": str(MAX_PRIMARY_MEMBER_BYTES),
    "MAX_TAR_SCAN_BYTES": str(MAX_TAR_SCAN_BYTES),
    "MAX_TOTAL_DOWNLOAD_BYTES": str(MAX_TOTAL_DOWNLOAD_BYTES),
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}


class BoundedSourceError(ValueError):
    """A requested source exceeded its preregistered limit or failed identity checks."""


class DownloadBudget:
    def __init__(self, maximum: int):
        self.maximum = maximum
        self.used = 0
        self.last_request_monotonic = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delay = REQUEST_GAP_SECONDS - (now - self.last_request_monotonic)
        if delay > 0:
            time.sleep(delay)
        self.last_request_monotonic = time.monotonic()

    def add(self, count: int) -> None:
        if count < 0 or self.used + count > self.maximum:
            raise BoundedSourceError("Q220_FORENSICS_TOTAL_DOWNLOAD_BUDGET_EXCEEDED")
        self.used += count


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def git_blob_sha1(body: bytes) -> str:
    header = b"blob " + str(len(body)).encode("ascii") + b"\0"
    return hashlib.sha1(header + body).hexdigest()


def read_request(request_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(request_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise BoundedSourceError(f"Q220_FORENSICS_REQUEST_INVALID_LINE:{number}")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value:
            raise BoundedSourceError(f"Q220_FORENSICS_REQUEST_INVALID_KEY_VALUE:{number}")
        if key in values:
            raise BoundedSourceError("Q220_FORENSICS_REQUEST_DUPLICATE_KEY:" + key)
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise BoundedSourceError("Q220_FORENSICS_REQUEST_KEY_SET_MISMATCH")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise BoundedSourceError("Q220_FORENSICS_REQUEST_SEQUENCE_INVALID")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise BoundedSourceError("Q220_FORENSICS_REQUEST_VALUE_MISMATCH:" + key)
    return values


def validate_frozen_source(request_path: Path, receipt_path: Path) -> tuple[dict[str, str], dict[str, Any]]:
    request = read_request(request_path)
    raw = receipt_path.read_bytes()
    actual_blob_sha = git_blob_sha1(raw)
    if actual_blob_sha != request["SOURCE_RECEIPT_GIT_BLOB_SHA"]:
        raise BoundedSourceError("Q220_FORENSICS_SOURCE_RECEIPT_BLOB_MISMATCH:" + actual_blob_sha)
    receipt = json.loads(raw.decode("utf-8"))
    if receipt.get("receipt_fingerprint") != request["SOURCE_RECEIPT_FINGERPRINT"]:
        raise BoundedSourceError("Q220_FORENSICS_SOURCE_RECEIPT_FINGERPRINT_MISMATCH")
    if receipt.get("source_population_receipt_fingerprint") != request["SOURCE_POPULATION_RECEIPT_FINGERPRINT"]:
        raise BoundedSourceError("Q220_FORENSICS_POPULATION_RECEIPT_FINGERPRINT_MISMATCH")
    if receipt.get("candidate_id") != "Q220" or receipt.get("gate_positive") is not False:
        raise BoundedSourceError("Q220_FORENSICS_SOURCE_GATE_STATE_MISMATCH")
    if receipt.get("source_hash_failure_count") != EXPECTED_SOURCE_HASH_FAILURE_COUNT:
        raise BoundedSourceError("Q220_FORENSICS_SOURCE_HASH_FAILURE_COUNT_MISMATCH")
    failures = receipt.get("source_hash_failures")
    if not isinstance(failures, list) or len(failures) != EXPECTED_SOURCE_HASH_FAILURE_COUNT:
        raise BoundedSourceError("Q220_FORENSICS_SOURCE_FAILURE_LIST_INVALID")
    found = {str(x.get("record_key")): x for x in failures if isinstance(x, dict)}
    for key, expected_sha in SAMPLE_EXPECTED_HASHES.items():
        row = found.get(key)
        if row is None:
            raise BoundedSourceError("Q220_FORENSICS_SAMPLE_KEY_NOT_IN_FROZEN_RECEIPT:" + key)
        error = str(row.get("error") or "")
        match = re.search(r"(?:^|:)expected=([0-9a-f]{64})(?:$|:)", error)
        if not match or match.group(1) != expected_sha:
            raise BoundedSourceError("Q220_FORENSICS_EXPECTED_HASH_PIN_MISMATCH:" + key)
        primary = re.search(r"(?:^|:)primary=([^:]+)(?:$|:)", error)
        if not primary or primary.group(1) != SAMPLE_PRIMARY_NAMES[key]:
            raise BoundedSourceError("Q220_FORENSICS_PRIMARY_FILENAME_PIN_MISMATCH:" + key)
        if not re.search(r"(?:^|:)status=200(?:$|:)", error):
            raise BoundedSourceError("Q220_FORENSICS_SOURCE_STATUS_NOT_200:" + key)
    return request, receipt


def _bounded_get(url: str, max_bytes: int, budget: DownloadBudget) -> dict[str, Any]:
    """Fetch a bounded response and reject a truncated body when Content-Length is known."""
    budget.wait()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,text/plain,application/gzip,application/x-gzip,*/*",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(getattr(response, "status", 200))
            headers = response.headers
            length_header = headers.get("Content-Length")
            declared_length = int(length_header) if length_header and str(length_header).isdigit() else None
            meta = {
                "requested_url": url,
                "final_url": str(response.geturl()),
                "http_status": status,
                "content_type": str(headers.get("Content-Type", "")),
                "content_encoding": str(headers.get("Content-Encoding", "")),
                "content_length_header": declared_length,
                "last_modified": str(headers.get("Last-Modified", "")),
                "etag": str(headers.get("ETag", "")),
            }
            # A declared object that is already too large is rejected without
            # downloading it. This is a bound, not evidence of a complete source.
            if declared_length is not None and declared_length > max_bytes:
                return {**meta, "status": "SKIPPED_DECLARED_LENGTH_OVER_LIMIT", "body": b"", "response_bytes": 0}
            body = response.read(max_bytes + 1)
            # Count bytes actually received even when a size ceiling rejects the response.
            budget.add(len(body))
            if len(body) > max_bytes:
                return {
                    **meta,
                    "status": "SKIPPED_ACTUAL_LENGTH_OVER_LIMIT",
                    "body": b"",
                    "response_bytes": len(body),
                    "response_sha256": sha256(body),
                }
            # urllib may return a short read without raising when the peer closes
            # early. Never label that partial object FETCHED when the HTTP contract
            # supplied a Content-Length. Preserve only its bounded fingerprint.
            if declared_length is not None and len(body) != declared_length:
                return {
                    **meta,
                    "status": "INCOMPLETE_CONTENT_LENGTH",
                    "body": b"",
                    "response_bytes": len(body),
                    "response_sha256": sha256(body),
                    "error": f"CONTENT_LENGTH_MISMATCH:declared={declared_length}:received={len(body)}",
                }
            return {
                **meta,
                "status": "FETCHED",
                "body": body,
                "response_bytes": len(body),
                "response_sha256": sha256(body),
            }
    except urllib.error.HTTPError as exc:
        meta = {
            "requested_url": url,
            "final_url": str(getattr(exc, "url", url)),
            "http_status": int(exc.code),
            "content_type": str((exc.headers or {}).get("Content-Type", "")),
            "content_encoding": str((exc.headers or {}).get("Content-Encoding", "")),
            "content_length_header": None,
            "last_modified": str((exc.headers or {}).get("Last-Modified", "")),
            "etag": str((exc.headers or {}).get("ETag", "")),
        }
        return {**meta, "status": "HTTP_ERROR", "response_bytes": 0, "body": b"", "error": f"HTTP_{exc.code}"}
    except (urllib.error.URLError, TimeoutError, OSError, BoundedSourceError) as exc:
        return {"requested_url": url, "status": "FETCH_ERROR", "response_bytes": 0, "body": b"", "error": f"{type(exc).__name__}: {exc}"[:500]}


def parse_submission_header(body: bytes) -> dict[str, str | None]:
    """Parse submission metadata before the first document, with filer-scoped identity.

    SEC daily Feed members contain an SEC-HEADER with SGML tags. Some historical
    member variants place TYPE/FILING-DATE/ACCEPTANCE-DATETIME in the pre-document
    header area but outside the SEC-HEADER block, so metadata falls back only to
    bytes preceding the first <DOCUMENT>. Form values from exhibit/document bodies
    are therefore never accepted as submission identity.
    """
    bounded = body[:2_000_000]
    pre_document = bounded.split(b"<DOCUMENT>", 1)[0]
    header_match = re.search(
        rb"<SEC-HEADER\b[^>]*>(.*?)(?=</SEC-HEADER>|<DOCUMENT>)",
        bounded,
        re.I | re.S,
    )
    header = header_match.group(1) if header_match else pre_document

    def capture(
        patterns: tuple[bytes, ...],
        source: bytes = pre_document,
    ) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, source, re.I | re.M)
            if match:
                return match.group(1).decode("ascii", "replace").strip()
        return None

    filer_match = re.search(
        rb"<FILER>(.*?)(?=</FILER>|<ISSUER>|$)",
        pre_document,
        re.I | re.S,
    )
    # When a tagged FILER block exists, its CIK is authoritative. If it does
    # not, retain the legacy label parser but stop before a possible ISSUER block.
    filer_scope = (
        filer_match.group(1)
        if filer_match
        else pre_document.split(b"<ISSUER>", 1)[0]
    )
    result: dict[str, str | None] = {
        "accession": capture((
            rb"<ACCESSION-NUMBER>\s*([0-9]{10}-[0-9]{2}-[0-9]{6})",
            rb"ACCESSION NUMBER:\s*([0-9]{10}-[0-9]{2}-[0-9]{6})",
        )),
        "filer_cik": capture((
            rb"<CIK>\s*([0-9]{10})",
            rb"CENTRAL INDEX KEY:\s*([0-9]{10})",
        ), filer_scope),
        "form": capture((
            rb"(?m)^\s*<TYPE>\s*([^\r\n<]+)",
            rb"CONFORMED SUBMISSION TYPE:\s*([^\r\n<]+)",
        )),
        "filed_date": capture((
            rb"<FILING-DATE>\s*([0-9]{8})",
            rb"FILED AS OF DATE:\s*([0-9]{8})",
        )),
        "acceptance_datetime": capture((
            rb"<ACCEPTANCE-DATETIME>\s*([0-9]{14})",
        )),
        "header_format": (
            "sec_sgml_tags"
            if b"<ACCESSION-NUMBER>" in pre_document.upper() or b"<FILER>" in pre_document.upper()
            else "legacy_text_labels"
        ),
    }
    if result["filed_date"]:
        raw = str(result["filed_date"])
        result["filed_date_iso"] = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    else:
        result["filed_date_iso"] = None
    if result["acceptance_datetime"]:
        raw = str(result["acceptance_datetime"])
        result["acceptance_datetime_iso"] = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}T{raw[8:10]}:{raw[10:12]}:{raw[12:14]}"
    else:
        result["acceptance_datetime_iso"] = None
    return result


def extract_primary_document(submission: bytes, expected_filename: str) -> dict[str, Any]:
    matches = []
    for document_match in re.finditer(rb"<DOCUMENT>\s*(.*?)</DOCUMENT>", submission, re.I | re.S):
        block = document_match.group(1)
        filename_match = re.search(rb"<FILENAME>\s*([^\r\n<]+)", block, re.I)
        if not filename_match:
            continue
        filename = filename_match.group(1).decode("utf-8", "replace").strip()
        if filename.lower() != expected_filename.lower():
            continue
        text_match = re.search(rb"<TEXT>(.*?)</TEXT>", block, re.I | re.S)
        if not text_match:
            matches.append({"filename": filename, "error": "PRIMARY_DOCUMENT_TEXT_BLOCK_MISSING"})
            continue
        raw_body = text_match.group(1)
        candidates = {
            "raw_text_block": raw_body,
            "drop_one_leading_linebreak": raw_body[2:] if raw_body.startswith(b"\r\n") else raw_body[1:] if raw_body.startswith(b"\n") else raw_body,
            "drop_outer_linebreaks": raw_body.strip(b"\r\n"),
        }
        variants = {
            name: {"sha256": sha256(value), "bytes": len(value)}
            for name, value in candidates.items()
        }
        matches.append({
            "filename": filename,
            "document_block_sha256": sha256(document_match.group(0)),
            "raw_text_block_sha256": sha256(raw_body),
            "raw_text_block_bytes": len(raw_body),
            "body_hash_variants": variants,
        })
    if not matches:
        return {"found": False, "error": "FROZEN_PRIMARY_FILENAME_NOT_FOUND_IN_ORIGINAL_SUBMISSION"}
    if len(matches) != 1:
        return {"found": False, "error": "DUPLICATE_PRIMARY_FILENAME_IN_ORIGINAL_SUBMISSION", "match_count": len(matches)}
    return {"found": True, **matches[0]}


def daily_feed_url(filing_date: str) -> str:
    """Return the SEC daily Feed URL using the official year/quarter directory."""
    filed = date.fromisoformat(filing_date)
    quarter = (filed.month - 1) // 3 + 1
    return (
        f"https://www.sec.gov/Archives/edgar/Feed/{filed.year}/QTR{quarter}/"
        f"{filed.strftime('%Y%m%d')}.nc.tar.gz"
    )


def scan_daily_feed(
    feed_blob: bytes,
    accession: str,
    primary_filename: str,
    *,
    max_scan_bytes: int,
    max_member_bytes: int,
) -> dict[str, Any]:
    scan: dict[str, Any] = {
        "feed_archive_sha256": sha256(feed_blob),
        "feed_archive_bytes": len(feed_blob),
        "original_member_name": None,
        "original_member_sha256": None,
        "original_member_bytes": None,
        "primary": None,
        "correction_members": [],
        "total_uncompressed_member_bytes_scanned": 0,
        "scan_complete": False,
        "scan_error": None,
    }
    original_payload: bytes | None = None
    expected_names = {accession + ".nc", accession, accession + ".txt"}
    correction_re = re.compile(re.escape(accession) + r"\.corr[0-9]+", re.I)
    try:
        with tarfile.open(fileobj=io.BytesIO(feed_blob), mode="r|gz") as archive:
            for member in archive:
                if not member.isfile():
                    continue
                scan["total_uncompressed_member_bytes_scanned"] += int(member.size)
                if scan["total_uncompressed_member_bytes_scanned"] > max_scan_bytes:
                    scan["scan_error"] = "FEED_UNCOMPRESSED_SCAN_LIMIT_EXCEEDED"
                    break
                basename = PurePosixPath(member.name).name
                if basename in expected_names:
                    if member.size > max_member_bytes:
                        scan["scan_error"] = "ORIGINAL_SUBMISSION_MEMBER_OVER_LIMIT"
                        break
                    fh = archive.extractfile(member)
                    if fh is None:
                        scan["scan_error"] = "ORIGINAL_SUBMISSION_MEMBER_UNREADABLE"
                        break
                    payload = fh.read(max_member_bytes + 1)
                    if len(payload) > max_member_bytes:
                        scan["scan_error"] = "ORIGINAL_SUBMISSION_MEMBER_ACTUAL_BYTES_OVER_LIMIT"
                        break
                    if original_payload is not None:
                        scan["scan_error"] = "DUPLICATE_ORIGINAL_SUBMISSION_MEMBER"
                        break
                    original_payload = payload
                    scan["original_member_name"] = member.name
                    scan["original_member_sha256"] = sha256(payload)
                    scan["original_member_bytes"] = len(payload)
                elif correction_re.fullmatch(basename):
                    scan["correction_members"].append({"name": member.name, "declared_bytes": int(member.size)})
            else:
                scan["scan_complete"] = True
    except (tarfile.TarError, OSError, EOFError) as exc:
        scan["scan_error"] = f"{type(exc).__name__}: {exc}"[:500]
    if original_payload is not None:
        scan["submission_header"] = parse_submission_header(original_payload)
        scan["primary"] = extract_primary_document(original_payload, primary_filename)
    elif scan["scan_error"] is None:
        scan["scan_error"] = "ORIGINAL_SUBMISSION_MEMBER_NOT_FOUND_IN_FILING_DAY_FEED"
    return scan


def compare_hash_origin(expected_sha: str, current_sha: str | None, primary_variants: dict[str, Any] | None) -> str:
    matches = []
    if isinstance(primary_variants, dict):
        matches = [name for name, info in primary_variants.items() if isinstance(info, dict) and info.get("sha256") == expected_sha]
    if matches:
        if current_sha and current_sha != expected_sha:
            return "FROZEN_HASH_MATCHES_ORIGINAL_FEED_BODY_CURRENT_ARCHIVE_DIFFERS"
        return "FROZEN_HASH_MATCHES_ORIGINAL_FEED_BODY"
    if current_sha == expected_sha:
        return "FROZEN_HASH_MATCHES_CURRENT_ARCHIVE_ONLY"
    return "FROZEN_HASH_MATCHES_NEITHER_OBSERVED_BODY"


def run(request_path: Path, receipt_path: Path, output_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q220_original_sec_feed_primary_hash_forensics_followup",
        "candidate_id": "Q220",
        "workpack_id": WORKPACK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NOT_STARTED",
        "request_validation_passed": False,
        "source_receipt_fingerprint": None,
        "source_population_receipt_fingerprint": None,
        "source_hash_failure_count": None,
        "source_sample_count": 0,
        "samples": [],
        "original_feed_hash_match_count": 0,
        "current_archive_hash_match_count": 0,
        "gate_positive": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "next_gate": "do not replace expected hashes or reopen Q220 unless original accepted-submission bytes and exact identity are independently reconciled",
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    try:
        request, frozen = validate_frozen_source(request_path, receipt_path)
        result.update({
            "request_validation_passed": True,
            "request_sequence": request["REQUEST_SEQUENCE"],
            "source_receipt_git_blob_sha": request["SOURCE_RECEIPT_GIT_BLOB_SHA"],
            "source_receipt_fingerprint": frozen["receipt_fingerprint"],
            "source_population_receipt_fingerprint": frozen["source_population_receipt_fingerprint"],
            "source_hash_failure_count": frozen["source_hash_failure_count"],
            "sample_record_keys": list(SAMPLE_KEYS),
            "source_receipt_path": SOURCE_RECEIPT_PATH,
            "request_mode": "FOLLOWUP_THREE_FIXED_SEC_DAILY_FEED_ORIGINAL_SUBMISSIONS_AND_CURRENT_PRIMARY_DOCUMENTS; BOUNDED_READ_ONLY",
            "maximum_sample_count": MAX_SAMPLE_COUNT,
            "maximum_feed_archive_bytes": MAX_FEED_ARCHIVE_BYTES,
            "maximum_current_primary_bytes": MAX_CURRENT_PRIMARY_BYTES,
            "maximum_primary_member_bytes": MAX_PRIMARY_MEMBER_BYTES,
            "maximum_tar_scan_bytes": MAX_TAR_SCAN_BYTES,
            "maximum_total_download_bytes": MAX_TOTAL_DOWNLOAD_BYTES,
            "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        })
    except Exception as exc:
        result.update({
            "status": "REQUEST_REJECTED",
            "error": f"{type(exc).__name__}: {exc}"[:700],
            "next_gate": "repair or explicitly re-register the exact Q220 source fingerprint and sample; no SEC network request was made",
        })
        _write_receipt(output_path, result)
        return result

    failures = {str(x["record_key"]): x for x in frozen["source_hash_failures"]}
    budget = DownloadBudget(MAX_TOTAL_DOWNLOAD_BYTES)
    completed = True
    for record_key in SAMPLE_KEYS:
        row = failures[record_key]
        parts = record_key.split("|")
        cik, accession, form, filed_date = parts
        error = str(row["error"])
        expected_match = re.search(r"(?:^|:)expected=([0-9a-f]{64})(?:$|:)", error)
        actual_match = re.search(r"(?:^|:)actual=([0-9a-f]{64})(?:$|:)", error)
        expected_bytes_match = re.search(r"(?:^|:)expected_bytes=([0-9]+)(?:$|:)", error)
        actual_bytes_match = re.search(r"(?:^|:)actual_bytes=([0-9]+)(?:$|:)", error)
        primary_match = re.search(r"(?:^|:)primary=([^:]+)(?:$|:)", error)
        primary = SAMPLE_PRIMARY_NAMES[record_key]
        sample: dict[str, Any] = {
            "record_key": record_key,
            "cik": cik,
            "accession": accession,
            "form": form,
            "filed_date": filed_date,
            "primary_filename": primary,
            "frozen_expected_sha256": expected_match.group(1) if expected_match else None,
            "frozen_actual_sha256": actual_match.group(1) if actual_match else None,
            "frozen_expected_bytes": int(expected_bytes_match.group(1)) if expected_bytes_match else None,
            "frozen_actual_bytes": int(actual_bytes_match.group(1)) if actual_bytes_match else None,
            "frozen_error": error,
            "current_primary": None,
            "daily_feed": None,
            "comparison_classification": "UNRESOLVED",
            "identity_validated": False,
            "source_vintage_proven": False,
        }
        if (
            not expected_match
            or expected_match.group(1) != SAMPLE_EXPECTED_HASHES[record_key]
            or not actual_match
            or not expected_bytes_match
            or not actual_bytes_match
            or not primary_match
            or primary_match.group(1) != primary
        ):
            sample["sample_error"] = "FROZEN_RECEIPT_SAMPLE_PIN_MISMATCH"
            completed = False
            result["samples"].append(sample)
            continue

        accession_dir = accession.replace("-", "")
        base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_dir}"
        current = _bounded_get(f"{base}/{primary}", MAX_CURRENT_PRIMARY_BYTES, budget)
        sample["current_primary"] = {k: v for k, v in current.items() if k != "body"}
        if current.get("status") != "FETCHED" or current.get("http_status") != 200:
            sample["sample_error"] = "CURRENT_PRIMARY_FETCH_NOT_SUCCESSFUL"
            completed = False
            result["samples"].append(sample)
            continue
        current_sha = str(current["response_sha256"])
        sample["current_primary"]["matches_frozen_receipt_actual_sha256"] = current_sha == sample["frozen_actual_sha256"]
        sample["current_primary"]["matches_frozen_receipt_actual_bytes"] = current["response_bytes"] == sample["frozen_actual_bytes"]

        feed_url = daily_feed_url(filed_date)
        feed = _bounded_get(feed_url, MAX_FEED_ARCHIVE_BYTES, budget)
        sample["daily_feed"] = {k: v for k, v in feed.items() if k != "body"}
        if feed.get("status") != "FETCHED" or feed.get("http_status") != 200:
            sample["sample_error"] = "DAILY_FEED_FETCH_NOT_SUCCESSFUL_OR_OVER_LIMIT"
            completed = False
            result["samples"].append(sample)
            continue
        scan = scan_daily_feed(
            feed["body"],
            accession,
            primary,
            max_scan_bytes=MAX_TAR_SCAN_BYTES,
            max_member_bytes=MAX_PRIMARY_MEMBER_BYTES,
        )
        sample["daily_feed"].update({k: v for k, v in scan.items() if k != "primary"})
        sample["daily_feed"]["primary"] = scan.get("primary")
        header = scan.get("submission_header") or {}
        header_checks = {
            "accession_matches": header.get("accession") == accession,
            "filer_cik_matches_company_cik": header.get("filer_cik") == cik,
            "form_matches": str(header.get("form") or "").upper() == form,
            "filing_date_matches": header.get("filed_date_iso") == filed_date,
            "acceptance_datetime_present": bool(header.get("acceptance_datetime")),
        }
        sample["daily_feed"]["submission_header_checks"] = header_checks
        sample["identity_validated"] = bool(
            scan.get("original_member_name")
            and scan.get("primary", {}).get("found") is True
            and scan.get("scan_complete") is True
            and all(header_checks.values())
        )
        primary_result = scan.get("primary") or {}
        variants = primary_result.get("body_hash_variants") if primary_result.get("found") else None
        sample["comparison_classification"] = compare_hash_origin(
            str(sample["frozen_expected_sha256"]),
            current_sha,
            variants,
        )
        sample["source_vintage_proven"] = bool(
            sample["identity_validated"]
            and variants
            and any(isinstance(info, dict) and info.get("sha256") == sample["frozen_expected_sha256"] for info in variants.values())
            and current_sha != sample["frozen_expected_sha256"]
        )
        sample["comparison_complete"] = bool(
            sample["identity_validated"]
            and current["http_status"] == 200
            and feed["http_status"] == 200
            and scan.get("primary", {}).get("found") is True
            and scan.get("scan_complete") is True
        )
        if not sample["comparison_complete"]:
            sample["sample_error"] = scan.get("scan_error") or "ORIGINAL_FEED_COMPARISON_INCOMPLETE"
            completed = False
        result["samples"].append(sample)

    result["source_sample_count"] = len(result["samples"])
    result["completed_sample_count"] = sum(x.get("comparison_complete") is True for x in result["samples"])
    result["original_feed_hash_match_count"] = sum(x.get("source_vintage_proven") is True for x in result["samples"])
    result["current_archive_hash_match_count"] = sum(
        x.get("current_primary", {}).get("response_sha256") == x.get("frozen_expected_sha256")
        for x in result["samples"]
    )
    result["source_download_bytes"] = budget.used
    result["status"] = "FORENSIC_COMPARISON_COMPLETE" if completed and result["completed_sample_count"] == MAX_SAMPLE_COUNT else "FORENSIC_COMPARISON_INCOMPLETE"
    if result["status"] == "FORENSIC_COMPARISON_COMPLETE":
        result["next_gate"] = (
            "use the frozen original-feed matches to design a separately reviewed Q220 source-vintage correction; "
            "do not edit frozen hashes or reopen the compiler gate automatically"
            if result["original_feed_hash_match_count"]
            else "expected hashes were not reproduced from the original daily Feed samples; inspect historical extraction/provenance; compiler stays blocked"
        )
    _write_receipt(output_path, result)
    return result


def _write_receipt(output_path: Path, receipt: dict[str, Any]) -> None:
    unsigned = dict(receipt)
    unsigned.pop("receipt_fingerprint", None)
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    receipt["receipt_fingerprint"] = sha256(canonical)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = run(args.request, args.receipt, args.output)
    except Exception as exc:
        receipt = {
            "schema_version": 1,
            "record_type": "q220_original_sec_feed_primary_hash_forensics_followup",
            "candidate_id": "Q220",
            "workpack_id": WORKPACK_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FORENSIC_RUN_ERROR",
            "error": f"{type(exc).__name__}: {exc}"[:700],
            "gate_positive": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "promotion": False,
            "live_execution": False,
            "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
        }
        _write_receipt(args.output, receipt)
    print(json.dumps({
        "status": receipt.get("status"),
        "candidate_id": receipt.get("candidate_id"),
        "source_sample_count": receipt.get("source_sample_count"),
        "completed_sample_count": receipt.get("completed_sample_count"),
        "original_feed_hash_match_count": receipt.get("original_feed_hash_match_count"),
        "source_download_bytes": receipt.get("source_download_bytes"),
        "receipt_fingerprint": receipt.get("receipt_fingerprint"),
        "performance_authorization": False,
        "gate_positive": False,
    }, sort_keys=True))
    return 0 if receipt.get("status") == "FORENSIC_COMPARISON_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
