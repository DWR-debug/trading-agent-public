"""Read-only Q104 lineage R3 for six frozen filing-date failures in 2016 Q4.

Downloads one exact SEC quarterly 13F source archive whose SHA-256 and byte length
were recorded in the immutable census shard receipt, then captures bounded SEC header
evidence. This probe neither repairs receipts nor changes any identity or research gate.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation import q104_i19_13f_historical_identity_census as census
from automation.q104_i19_13f_historical_identity_census_merge import canonical_fingerprint

SOURCE_RUN_ID = "38168441086"
SOURCE_PAGE_SHA256 = "b2c4083c3615ce6646764d8e80dc18c2f5484a25c417281be580bdc650817b46"
SOURCE_SHARDS = {
    "2013-2016": {
        "receipt_fingerprint": "dbe0651154dd4e34ee1aac729f48cf1536c99e28d17666e70178898ab198a27f",
        "source_page_sha256": SOURCE_PAGE_SHA256,
    },
}
ARCHIVE_PINS = {
    "2016q4_form13f.zip": {
        "url": "https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2016q4_form13f.zip",
        "sha256": "40dea4a7e1e7d7ba118ffed32ab1941e365a2835d748e7ae682af8b1dc8f1be4",
        "bytes": 41801560,
        "shard": "2013-2016",
    },
}
SAMPLES = (
    {"accession": "0000950123-16-022491", "archive": "2016q4_form13f.zip", "frozen_failure": "FILING_DATE_MISMATCH"},
    {"accession": "0000950123-16-022512", "archive": "2016q4_form13f.zip", "frozen_failure": "FILING_DATE_MISMATCH"},
    {"accession": "0001138060-16-000026", "archive": "2016q4_form13f.zip", "frozen_failure": "FILING_DATE_MISMATCH"},
    {"accession": "0001144204-16-134468", "archive": "2016q4_form13f.zip", "frozen_failure": "FILING_DATE_MISMATCH"},
    {"accession": "0001144204-16-134474", "archive": "2016q4_form13f.zip", "frozen_failure": "FILING_DATE_MISMATCH"},
    {"accession": "0001352900-16-000030", "archive": "2016q4_form13f.zip", "frozen_failure": "FILING_DATE_MISMATCH"},)
MAX_SOURCE_ARCHIVE_BYTES = 100_000_000
MAX_HEADER_RESPONSE_BYTES = 262_144
MAX_TOTAL_DOWNLOAD_BYTES = 150_000_000
REQUEST_GAP_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 120
USER_AGENT = census.UA

FROZEN_REQUEST_VALUES = {
    "RUN_Q104_I19_RESIDUAL_LINEAGE_DIAGNOSTIC_R3": "true",
    "REASON": "READ_ONLY_CAPTURE_Q104_I19_HEADER_LINEAGE_FOR_FROZEN_2016Q4_FAILURES",
    "SOURCE_RUN_ID": SOURCE_RUN_ID,
    "SOURCE_PAGE_SHA256": SOURCE_PAGE_SHA256,
    "SAMPLE_COUNT": str(len(SAMPLES)),
    "MAX_SOURCE_ARCHIVE_BYTES": str(MAX_SOURCE_ARCHIVE_BYTES),
    "MAX_HEADER_RESPONSE_BYTES": str(MAX_HEADER_RESPONSE_BYTES),
    "MAX_TOTAL_DOWNLOAD_BYTES": str(MAX_TOTAL_DOWNLOAD_BYTES),
    "CENSUS_RESTART": "false",
    "REPAIR_RECEIPTS": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}


class DiagnosticError(ValueError):
    """A pinned input, source body, or bounded diagnostic invariant did not validate."""


class DownloadBudget:
    def __init__(self, maximum: int):
        self.maximum = maximum
        self.used = 0
        self.next_request_at = 0.0

    def wait(self) -> None:
        delay = self.next_request_at - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self.next_request_at = time.monotonic() + REQUEST_GAP_SECONDS

    def add(self, count: int) -> None:
        if count < 0 or self.used + count > self.maximum:
            raise DiagnosticError("Q104_LINEAGE_TOTAL_DOWNLOAD_BUDGET_EXCEEDED")
        self.used += count


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def receipt_fingerprint(payload: dict[str, Any]) -> str:
    return canonical_fingerprint(payload)


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise DiagnosticError(f"Q104_LINEAGE_REQUEST_INVALID_LINE:{number}")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value or key in values:
            raise DiagnosticError(f"Q104_LINEAGE_REQUEST_INVALID_KEY_VALUE:{number}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise DiagnosticError("Q104_LINEAGE_REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise DiagnosticError("Q104_LINEAGE_REQUEST_VALUE_MISMATCH:" + key)
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise DiagnosticError("Q104_LINEAGE_REQUEST_SEQUENCE_INVALID")
    return values


def _find_shard_receipt(path: Path) -> Path:
    if path.is_file():
        return path
    matches = sorted(path.rglob("shard_receipt.json"))
    if len(matches) != 1:
        raise DiagnosticError(f"Q104_LINEAGE_SHARD_RECEIPT_COUNT_INVALID:{path}:{len(matches)}")
    return matches[0]


def validate_frozen_inputs(
    request: dict[str, str],
    snapshot_dir: Path,
    input_dir: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    source_page = snapshot_dir / "source_page.html"
    if not source_page.is_file():
        raise DiagnosticError("Q104_LINEAGE_SOURCE_PAGE_MISSING")
    actual_page_sha = sha256(source_page.read_bytes())
    if actual_page_sha != SOURCE_PAGE_SHA256 or actual_page_sha != request["SOURCE_PAGE_SHA256"]:
        raise DiagnosticError("Q104_LINEAGE_SOURCE_PAGE_SHA256_MISMATCH:" + actual_page_sha)

    receipts: dict[str, dict[str, Any]] = {}
    shard_fingerprints: dict[str, str] = {}
    for shard, pin in SOURCE_SHARDS.items():
        receipt_path = _find_shard_receipt(input_dir / shard)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("shard") != shard:
            raise DiagnosticError("Q104_LINEAGE_SHARD_ID_MISMATCH:" + shard)
        if receipt.get("source_page_sha256") != SOURCE_PAGE_SHA256:
            raise DiagnosticError("Q104_LINEAGE_SHARD_SOURCE_PAGE_MISMATCH:" + shard)
        if receipt.get("receipt_fingerprint") != pin["receipt_fingerprint"]:
            raise DiagnosticError("Q104_LINEAGE_SHARD_RECEIPT_FINGERPRINT_MISMATCH:" + shard)
        if receipt_fingerprint(receipt) != receipt.get("receipt_fingerprint"):
            raise DiagnosticError("Q104_LINEAGE_SHARD_RECEIPT_CANONICAL_FINGERPRINT_INVALID:" + shard)
        receipts[shard] = receipt
        shard_fingerprints[shard] = str(receipt["receipt_fingerprint"])

    for archive_name, pin in ARCHIVE_PINS.items():
        shard_receipt = receipts[pin["shard"]]
        matches = [
            archive for archive in shard_receipt.get("archives", [])
            if archive.get("archive", {}).get("url") == pin["url"]
        ]
        if len(matches) != 1:
            raise DiagnosticError("Q104_LINEAGE_PINNED_ARCHIVE_RECORD_COUNT_INVALID:" + archive_name)
        archive_record = matches[0]
        if archive_record.get("archive_sha256") != pin["sha256"]:
            raise DiagnosticError("Q104_LINEAGE_RECEIPT_ARCHIVE_SHA256_MISMATCH:" + archive_name)
        if archive_record.get("archive_bytes") != pin["bytes"]:
            raise DiagnosticError("Q104_LINEAGE_RECEIPT_ARCHIVE_BYTES_MISMATCH:" + archive_name)
        frozen_failures = archive_record.get("acceptance_failures", {})
        for sample in SAMPLES:
            if sample["archive"] == archive_name:
                if frozen_failures.get(sample["accession"]) != sample["frozen_failure"]:
                    raise DiagnosticError("Q104_LINEAGE_FROZEN_FAILURE_NOT_FOUND:" + sample["accession"])
    return receipts, shard_fingerprints


def fetch_bounded(
    url: str,
    budget: DownloadBudget,
    *,
    max_bytes: int,
    prefix_marker: bytes | None = None,
) -> dict[str, Any]:
    """Capture a bounded HTTP response. Prefix mode ends only at the marker or cap."""
    budget.wait()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,text/plain,application/zip,*/*",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    metadata: dict[str, Any] = {
        "requested_url": url,
        "final_url": url,
        "http_status": None,
        "content_type": "",
        "content_length_header": None,
        "last_modified": "",
        "etag": "",
    }
    body = bytearray()
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            headers = response.headers
            length_value = headers.get("Content-Length")
            declared = int(length_value) if length_value and str(length_value).isdigit() else None
            metadata.update({
                "final_url": str(response.geturl()),
                "http_status": int(getattr(response, "status", 200)),
                "content_type": str(headers.get("Content-Type", "")),
                "content_length_header": declared,
                "last_modified": str(headers.get("Last-Modified", "")),
                "etag": str(headers.get("ETag", "")),
            })
            if prefix_marker is None and declared is not None and declared > max_bytes:
                return {
                    **metadata, "status": "SKIPPED_DECLARED_LENGTH_OVER_LIMIT",
                    "response_bytes": 0, "response_sha256": None, "_body": b"",
                }
            while len(body) < max_bytes + (1 if prefix_marker is None else 0):
                amount = min(1_048_576 if prefix_marker is None else 8192,
                             max_bytes + (1 if prefix_marker is None else 0) - len(body))
                try:
                    chunk = response.read(amount)
                except (http.client.HTTPException, urllib.error.URLError, TimeoutError, OSError) as exc:
                    return {
                        **metadata, "status": "INCOMPLETE_READ", "response_bytes": len(body),
                        "response_sha256": sha256(bytes(body)), "error": f"{type(exc).__name__}:{exc}"[:500],
                        "_body": b"",
                    }
                if not chunk:
                    break
                budget.add(len(chunk))
                body.extend(chunk)
                if prefix_marker is not None and prefix_marker.lower() in bytes(body).lower():
                    break
            raw = bytes(body)
            if prefix_marker is not None:
                marker_found = prefix_marker.lower() in raw.lower()
                status = "FETCHED_PREFIX" if marker_found else "HEADER_PREFIX_LIMIT_OR_EOF"
                return {
                    **metadata, "status": status, "prefix_marker_found": marker_found,
                    "response_bytes": len(raw), "response_sha256": sha256(raw), "_body": raw,
                }
            if len(raw) > max_bytes:
                return {
                    **metadata, "status": "SKIPPED_ACTUAL_LENGTH_OVER_LIMIT",
                    "response_bytes": len(raw), "response_sha256": sha256(raw), "_body": b"",
                }
            if declared is not None and len(raw) != declared:
                return {
                    **metadata, "status": "INCOMPLETE_CONTENT_LENGTH", "response_bytes": len(raw),
                    "response_sha256": sha256(raw),
                    "error": f"CONTENT_LENGTH_MISMATCH:declared={declared}:received={len(raw)}",
                    "_body": b"",
                }
            return {
                **metadata, "status": "FETCHED", "response_bytes": len(raw),
                "response_sha256": sha256(raw), "_body": raw,
            }
    except urllib.error.HTTPError as exc:
        headers = exc.headers or {}
        metadata.update({
            "final_url": str(getattr(exc, "url", url)),
            "http_status": int(exc.code),
            "content_type": str(headers.get("Content-Type", "")),
            "content_length_header": int(headers.get("Content-Length")) if str(headers.get("Content-Length", "")).isdigit() else None,
            "last_modified": str(headers.get("Last-Modified", "")),
            "etag": str(headers.get("ETag", "")),
        })
        return {**metadata, "status": "HTTP_ERROR", "response_bytes": 0, "response_sha256": None, "error": f"HTTP_{exc.code}", "_body": b""}
    except (urllib.error.URLError, TimeoutError, OSError, DiagnosticError) as exc:
        return {
            **metadata, "status": "FETCH_ERROR", "response_bytes": len(body),
            "response_sha256": sha256(bytes(body)) if body else None,
            "error": f"{type(exc).__name__}:{exc}"[:500], "_body": b"",
        }


def read_source_rows(archive_body: bytes, accession_keys: set[str]) -> dict[str, dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    try:
        with zipfile.ZipFile(io.BytesIO(archive_body)) as zf:
            rows = census.tsv(zf, "submission.tsv")
            for row in rows:
                accession = census.field(row, "ACCESSION_NUMBER")
                if accession not in accession_keys:
                    continue
                if accession in found:
                    raise DiagnosticError("Q104_LINEAGE_DUPLICATE_SUBMISSION_TSV_ACCESSION:" + accession)
                raw_date = census.field(row, "FILING_DATE")
                try:
                    normalized_date = census.parse_date(raw_date).isoformat() if raw_date else None
                except ValueError:
                    normalized_date = None
                cik = census.field(row, "CIK").strip()
                form = census.field(row, "SUBMISSIONTYPE").strip()
                if not re.fullmatch(r"\d{1,10}", cik):
                    raise DiagnosticError("Q104_LINEAGE_SOURCE_ARCHIVE_CIK_INVALID:" + accession)
                if not form or not raw_date:
                    raise DiagnosticError("Q104_LINEAGE_SOURCE_ARCHIVE_IDENTITY_FIELDS_MISSING:" + accession)
                found[accession] = {
                    "accession": accession,
                    "filer_cik": cik.zfill(10),
                    "form": form,
                    "filing_date_raw": raw_date,
                    "filing_date_iso": normalized_date,
                    "period_of_report": census.field(row, "PERIODOFREPORT"),
                }
    except (zipfile.BadZipFile, OSError) as exc:
        raise DiagnosticError(f"Q104_LINEAGE_SOURCE_ARCHIVE_ZIP_INVALID:{type(exc).__name__}") from exc
    return found


def parse_header_observation(body: bytes, source_type: str) -> dict[str, str | None]:
    """Extract observed fields for comparison; never declare the identity valid."""
    pre_document = body.split(b"<DOCUMENT>", 1)[0]
    def capture(patterns: tuple[bytes, ...]) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, pre_document, re.I | re.S)
            if match:
                value = match.group(1).decode("utf-8", "replace").strip()
                if value:
                    return value.split()[0].strip()
        return None
    accession = capture((
        rb"<ACCESSION-NUMBER>\s*([0-9]{10}-[0-9]{2}-[0-9]{6})",
        rb"ACCESSION NUMBER:\s*([0-9]{10}-[0-9]{2}-[0-9]{6})",
    ))
    filer = re.search(rb"<FILER\b[^>]*>(.*?)</FILER>", pre_document, re.I | re.S)
    cik = None
    if filer:
        cik_match = re.search(rb"<CIK>\s*([0-9]{1,10})", filer.group(1), re.I)
        if cik_match:
            cik = cik_match.group(1).decode("ascii").zfill(10)
    if cik is None:
        cik = capture((rb"CENTRAL INDEX KEY:\s*([0-9]{1,10})",))
        if cik:
            cik = cik.zfill(10)
    form = capture((
        rb"CONFORMED SUBMISSION TYPE:\s*([^\s<]+)",
        rb"<TYPE>\s*([^\r\n<]+)",
    ))
    filed = capture((
        rb"<FILING-DATE>\s*([0-9]{8})",
        rb"FILED AS OF DATE:\s*([0-9]{8})",
    ))
    if filed and re.fullmatch(r"\d{8}", filed):
        filed = f"{filed[:4]}-{filed[4:6]}-{filed[6:8]}"
    accepted = capture((rb"<ACCEPTANCE-DATETIME>\s*([0-9]{14})",))
    if accepted and re.fullmatch(r"\d{14}", accepted):
        accepted = f"{accepted[:4]}-{accepted[4:6]}-{accepted[6:8]}T{accepted[8:10]}:{accepted[10:12]}:{accepted[12:14]}"
    return {
        "source_type": source_type,
        "accession": accession,
        "filer_cik": cik,
        "form": form,
        "filing_date": filed,
        "acceptance_datetime": accepted,
    }


def compare_observed_to_archive(source_row: dict[str, str], observed: dict[str, str | None]) -> dict[str, Any]:
    return {
        "accession_matches": observed.get("accession") == source_row["accession"],
        "filer_cik_matches": observed.get("filer_cik") == source_row["filer_cik"] if observed.get("filer_cik") else None,
        "form_matches": str(observed.get("form") or "").upper() == source_row["form"].upper() if observed.get("form") else None,
        "filing_date_matches": observed.get("filing_date") == source_row["filing_date_iso"] if observed.get("filing_date") else None,
    }


def run_diagnostic(
    request: dict[str, str],
    *,
    snapshot_dir: Path,
    input_dir: Path,
    output: Path,
) -> dict[str, Any]:
    _, shard_fingerprints = validate_frozen_inputs(request, snapshot_dir, input_dir)
    budget = DownloadBudget(MAX_TOTAL_DOWNLOAD_BYTES)
    archive_results: dict[str, dict[str, Any]] = {}
    sample_rows: dict[str, dict[str, str]] = {}
    errors: list[str] = []

    # Each source archive is fetched once and used only if its byte fingerprint matches
    # the exact source-vintage fingerprint recorded in the frozen census receipt.
    for archive_name, pin in ARCHIVE_PINS.items():
        result = fetch_bounded(pin["url"], budget, max_bytes=MAX_SOURCE_ARCHIVE_BYTES)
        body = result.pop("_body", b"")
        record = {
            "url": pin["url"],
            "expected_sha256": pin["sha256"],
            "expected_bytes": pin["bytes"],
            "http": result,
        }
        observed_sha = sha256(body) if body else None
        record["observed_sha256"] = observed_sha
        record["observed_bytes"] = len(body)
        record["archive_bytes_match"] = len(body) == pin["bytes"]
        record["archive_sha256_match"] = observed_sha == pin["sha256"]
        record["archive_verified"] = (
            result.get("status") == "FETCHED"
            and record["archive_bytes_match"]
            and record["archive_sha256_match"]
        )
        if not record["archive_verified"]:
            errors.append("Q104_LINEAGE_ARCHIVE_NOT_BYTE_IDENTICAL:" + archive_name)
            archive_results[archive_name] = record
            continue
        requested = {sample["accession"] for sample in SAMPLES if sample["archive"] == archive_name}
        rows = read_source_rows(body, requested)
        missing = sorted(requested - set(rows))
        record["requested_accessions"] = sorted(requested)
        record["source_rows_found"] = sorted(rows)
        record["source_rows_missing"] = missing
        if missing:
            errors.extend("Q104_LINEAGE_SOURCE_ROW_MISSING:" + key for key in missing)
        archive_results[archive_name] = record
        sample_rows.update(rows)

    sample_results: list[dict[str, Any]] = []
    all_probe_observations_collected = True
    for sample in SAMPLES:
        accession = sample["accession"]
        pin = ARCHIVE_PINS[sample["archive"]]
        archive_record = archive_results[sample["archive"]]
        source_row = sample_rows.get(accession)
        item: dict[str, Any] = {
            "accession": accession,
            "archive_name": sample["archive"],
            "frozen_failure": sample["frozen_failure"],
            "archive_sha256_match": archive_record.get("archive_sha256_match", False),
            "source_row": source_row,
            "probes": [],
        }
        if not archive_record.get("archive_verified") or source_row is None:
            item["status"] = "SOURCE_LINEAGE_NOT_VERIFIED"
            sample_results.append(item)
            all_probe_observations_collected = False
            continue
        cik = source_row["filer_cik"]
        normalized_accession = accession.replace("-", "")
        base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{normalized_accession}"
        routes = (
            ("index_headers", f"{base}/{accession}-index-headers.html", None),
            ("raw_sgml_header", f"{base}/{accession}.hdr.sgml", None),
            ("complete_submission_header_prefix", f"{base}/{accession}.txt", b"</SEC-HEADER>"),
        )
        for route_name, url, prefix_marker in routes:
            result = fetch_bounded(url, budget, max_bytes=MAX_HEADER_RESPONSE_BYTES, prefix_marker=prefix_marker)
            raw = result.pop("_body", b"")
            probe = {key: value for key, value in result.items() if key not in {"error"} or value is not None}
            probe["route"] = route_name
            probe["response_error"] = result.get("error")
            probe["response_sha256"] = result.get("response_sha256")
            if raw and result.get("status") in {"FETCHED", "FETCHED_PREFIX"}:
                observed = parse_header_observation(raw, route_name)
                probe["observed_identity"] = observed
                probe["comparison_to_frozen_archive_row"] = compare_observed_to_archive(source_row, observed)
            else:
                probe["observed_identity"] = None
                probe["comparison_to_frozen_archive_row"] = None
            item["probes"].append(probe)
            # HTTP 404 is an observed source fact. Network errors, incomplete reads,
            # truncated prefixes, and size caps mean the diagnostic is not complete.
            acceptable = {"FETCHED", "FETCHED_PREFIX", "HTTP_ERROR"}
            if result.get("status") not in acceptable:
                all_probe_observations_collected = False
        item["status"] = "OBSERVED" if len(item["probes"]) == 3 else "PROBE_INCOMPLETE"
        sample_results.append(item)

    all_archives_verified = all(x.get("archive_verified") for x in archive_results.values()) and len(archive_results) == len(ARCHIVE_PINS)
    all_rows_found = len(sample_rows) == len(SAMPLES)
    status = "LINEAGE_DIAGNOSTIC_COMPLETE" if all_archives_verified and all_rows_found and all_probe_observations_collected else "LINEAGE_DIAGNOSTIC_INCOMPLETE"
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q104_i19_residual_source_lineage_diagnostic_r3",
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "request_sequence": request["REQUEST_SEQUENCE"],
        "source_run_id": SOURCE_RUN_ID,
        "source_page_sha256": SOURCE_PAGE_SHA256,
        "source_shard_receipt_fingerprints": shard_fingerprints,
        "pinned_archives": archive_results,
        "samples": sample_results,
        "summary": {
            "sample_count": len(SAMPLES),
            "source_archives_pinned": len(ARCHIVE_PINS),
            "source_archives_verified": sum(1 for x in archive_results.values() if x.get("archive_verified")),
            "probes_expected": len(SAMPLES) * 3,
            "probes_captured": sum(len(x.get("probes", [])) for x in sample_results),
            "total_download_bytes": budget.used,
            "download_budget_bytes": MAX_TOTAL_DOWNLOAD_BYTES,
            "errors": errors,
        },
        "research_boundary": {
            "identity_discrepancies_resolved": False,
            "acceptance_time_gate_cleared": False,
            "historical_archive_gate_reopened": False,
            "next_action": "Compare the six frozen 2016 Q4 failures with prior R1/R2 header observations; do not repair residual accessions or apply date-field precedence from this diagnostic alone.",
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "census_restart": False,
            "repair_receipts_modified": False,
            "performance_authorized": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    receipt["receipt_fingerprint"] = sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if status != "LINEAGE_DIAGNOSTIC_COMPLETE":
        raise DiagnosticError("Q104_LINEAGE_DIAGNOSTIC_INCOMPLETE:" + ",".join(errors))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-snapshot-dir", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = read_request(args.request)
    receipt = run_diagnostic(
        request,
        snapshot_dir=args.source_snapshot_dir,
        input_dir=args.input_dir,
        output=args.output,
    )
    print(json.dumps({
        "status": receipt["status"],
        "receipt_fingerprint": receipt["receipt_fingerprint"],
        "probes_captured": receipt["summary"]["probes_captured"],
        "total_download_bytes": receipt["summary"]["total_download_bytes"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
