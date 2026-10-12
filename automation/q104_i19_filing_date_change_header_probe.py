"""Header-only follow-up to inspect DATE-OF-FILING-DATE-CHANGE for frozen Q104:I19 samples.

Uses the immutable R1 and R2 diagnostic artifacts. It performs no archive
downloads and does not choose or apply field precedence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

R1_RUN_ID = "38255701998"
R1_FINGERPRINT = "c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7"
R2_RUN_ID = "38301876992"
R2_FINGERPRINT = "d85ad092296b38f29fa25147537f52804f9a32d9969051c7f9e9cadff283fe04"
USER_AGENT = "DWR-debug/trading-agent-public Q104 filing-date-change header probe/1.0"
MAX_RESPONSE_BYTES = 262_144
MAX_TOTAL_BYTES = 8_000_000
REQUEST_GAP_SECONDS = 1.0
TIMEOUT_SECONDS = 30
ROUTES = ("index_headers", "raw_sgml_header", "complete_submission_header_prefix")
EXPECTED = {
    "0000950123-15-003104": {"cik": "0001226779", "form": "13F-HR", "bulk_filing_date": "2015-02-18", "r1": True},
    "0000950123-15-003463": {"cik": "0000707179", "form": "13F-HR", "bulk_filing_date": "2015-02-18", "r1": True},
    "0001800724-20-000002": {"cik": "0001800724", "form": "13F-HR", "bulk_filing_date": "2020-08-10", "r1": True},
    "0001800724-20-000003": {"cik": "0001648101", "form": "13F-HR", "bulk_filing_date": "2020-08-10", "r1": True},
    "0000950123-17-002537": {"cik": "0001276144", "form": "13F-HR", "bulk_filing_date": "2017-02-15", "r1": False},
    "0000950123-17-002540": {"cik": "0001418333", "form": "13F-HR", "bulk_filing_date": "2017-02-15", "r1": False},
    "0000895421-25-000499": {"cik": "0000895421", "form": "13F-HR", "bulk_filing_date": "2025-08-15", "r1": False},
    "0001102578-25-000024": {"cik": "0001102578", "form": "13F-HR", "bulk_filing_date": "2025-08-15", "r1": False},
}
FROZEN_REQUEST_VALUES = {
    "RUN_Q104_I19_FILING_DATE_CHANGE_HEADER_PROBE": "true",
    "REASON": "READ_ONLY_CAPTURE_DATE_OF_FILING_DATE_CHANGE_FOR_FROZEN_R1_R2_SAMPLE",
    "R1_RUN_ID": R1_RUN_ID,
    "R1_RECEIPT_FINGERPRINT": R1_FINGERPRINT,
    "R2_RUN_ID": R2_RUN_ID,
    "R2_RECEIPT_FINGERPRINT": R2_FINGERPRINT,
    "SAMPLE_COUNT": "8",
    "PROBE_COUNT": "24",
    "MAX_RESPONSE_BYTES": str(MAX_RESPONSE_BYTES),
    "MAX_TOTAL_BYTES": str(MAX_TOTAL_BYTES),
    "ARCHIVE_DOWNLOADS": "0",
    "CENSUS_RESTART": "false",
    "REPAIR_RECEIPTS": "false",
    "FIELD_PRECEDENCE_APPLIED": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}


class ProbeError(ValueError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_fingerprint(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("receipt_fingerprint", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(raw)


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise ProbeError(f"Q104_DATE_CHANGE_REQUEST_INVALID_LINE:{number}")
        key, value = line.split("=", 1)
        if not key or not value or key in values:
            raise ProbeError(f"Q104_DATE_CHANGE_REQUEST_INVALID_KEY_VALUE:{number}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise ProbeError("Q104_DATE_CHANGE_REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise ProbeError("Q104_DATE_CHANGE_REQUEST_VALUE_MISMATCH:" + key)
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise ProbeError("Q104_DATE_CHANGE_REQUEST_SEQUENCE_INVALID")
    return values


def find_receipt(root: Path) -> Path:
    if root.is_file():
        return root
    found = sorted(root.rglob("receipt.json"))
    if len(found) != 1:
        raise ProbeError("Q104_DATE_CHANGE_RECEIPT_COUNT_INVALID:" + str(root))
    return found[0]


def validate_receipt(path: Path, run_id: str, expected_fp: str, expected_accessions: set[str]) -> dict[str, Any]:
    receipt = json.loads(find_receipt(path).read_text(encoding="utf-8"))
    if receipt.get("status") != "LINEAGE_DIAGNOSTIC_COMPLETE":
        raise ProbeError("Q104_DATE_CHANGE_SOURCE_RECEIPT_NOT_COMPLETE:" + run_id)
    if receipt.get("source_run_id") != "38168441086":
        raise ProbeError("Q104_DATE_CHANGE_SOURCE_CENSUS_RUN_MISMATCH:" + run_id)
    if receipt.get("receipt_fingerprint") != expected_fp or canonical_fingerprint(receipt) != expected_fp:
        raise ProbeError("Q104_DATE_CHANGE_SOURCE_RECEIPT_FINGERPRINT_INVALID:" + run_id)
    if receipt.get("summary", {}).get("source_archives_verified") != 2:
        raise ProbeError("Q104_DATE_CHANGE_SOURCE_ARCHIVE_VERIFICATION_INCOMPLETE:" + run_id)
    samples = receipt.get("samples", [])
    if {x.get("accession") for x in samples} != expected_accessions or len(samples) != len(expected_accessions):
        raise ProbeError("Q104_DATE_CHANGE_SAMPLE_KEY_SET_MISMATCH:" + run_id)
    for sample in samples:
        exp = EXPECTED[sample["accession"]]
        row = sample.get("source_row") or {}
        if sample.get("status") != "OBSERVED" or len(sample.get("probes", [])) != 3:
            raise ProbeError("Q104_DATE_CHANGE_SAMPLE_OBSERVATION_INCOMPLETE:" + sample["accession"])
        if row.get("filer_cik") != exp["cik"] or row.get("form") != exp["form"] or row.get("filing_date_iso") != exp["bulk_filing_date"]:
            raise ProbeError("Q104_DATE_CHANGE_FROZEN_SOURCE_ROW_MISMATCH:" + sample["accession"])
    return receipt


class Budget:
    def __init__(self):
        self.used = 0
        self.next_request_at = 0.0

    def wait(self):
        delay = self.next_request_at - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self.next_request_at = time.monotonic() + REQUEST_GAP_SECONDS

    def add(self, size: int):
        if size < 0 or self.used + size > MAX_TOTAL_BYTES:
            raise ProbeError("Q104_DATE_CHANGE_TOTAL_RESPONSE_BUDGET_EXCEEDED")
        self.used += size


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    return value or None


def parse_header_fields(raw: bytes, route: str) -> dict[str, str | None]:
    text = raw.decode("utf-8", errors="replace")
    def first(pattern: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else None
    accession = first(r"<ACCESSION-NUMBER>\s*([0-9-]{18,25})") or first(r"ACCESSION NUMBER:\s*([0-9-]{18,25})")
    filer_block = re.search(r"<FILER>.*?<CIK>\s*(\d{1,10})", text, re.IGNORECASE | re.DOTALL)
    cik = filer_block.group(1) if filer_block else (first(r"<CIK>\s*(\d{1,10})") or first(r"CENTRAL INDEX KEY:\s*(\d{1,10})"))
    form = first(r"<CONFORMED-SUBMISSION-TYPE>\s*([A-Z0-9/-]+)") or first(r"CONFORMED SUBMISSION TYPE:\s*([A-Z0-9/-]+)")
    filing = first(r"<FILING-DATE>\s*(\d{8})") or first(r"FILED AS OF DATE:\s*(\d{8})") or first(r"FILING DATE:\s*(\d{4}-\d{2}-\d{2})")
    change = first(r"<DATE-OF-FILING-DATE-CHANGE>\s*(\d{8})")
    acceptance = first(r"<ACCEPTANCE-DATETIME>\s*(\d{14})")
    if not acceptance:
        date_part = first(r"<ACCEPTANCE-DATE>\s*(\d{8})")
        time_part = first(r"<ACCEPTANCE-TIME>\s*(\d{6})")
        if date_part and time_part:
            acceptance = date_part + time_part
    if acceptance and re.fullmatch(r"\d{14}", acceptance):
        acceptance = f"{acceptance[:4]}-{acceptance[4:6]}-{acceptance[6:8]}T{acceptance[8:10]}:{acceptance[10:12]}:{acceptance[12:14]}"
    return {
        "source_type": route,
        "accession": accession,
        "filer_cik": cik.zfill(10) if cik else None,
        "form": form.upper() if form else None,
        "filing_date": normalize_date(filing),
        "date_of_filing_date_change": normalize_date(change),
        "acceptance_datetime": acceptance,
    }


def fetch_header(url: str, route: str, budget: Budget, prefix_marker: bytes | None = None) -> dict[str, Any]:
    budget.wait()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,*/*", "Accept-Encoding": "identity", "Connection": "close"},
        method="GET",
    )
    result: dict[str, Any] = {"route": route, "requested_url": url, "http_status": None, "content_type": "", "response_bytes": 0, "response_sha256": None}
    body = bytearray()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            result.update({"http_status": int(getattr(response, "status", 200)), "content_type": str(response.headers.get("Content-Type", "")), "last_modified": str(response.headers.get("Last-Modified", "")), "etag": str(response.headers.get("ETag", ""))})
            while len(body) <= MAX_RESPONSE_BYTES:
                amount = min(8192, MAX_RESPONSE_BYTES + 1 - len(body))
                chunk = response.read(amount)
                if not chunk:
                    break
                body.extend(chunk)
                if prefix_marker and prefix_marker in body:
                    break
            if len(body) > MAX_RESPONSE_BYTES:
                result["status"] = "RESPONSE_OVER_LIMIT"
                return result
            budget.add(len(body))
            raw = bytes(body)
            result.update({"status": "FETCHED_PREFIX" if prefix_marker and prefix_marker in raw else "FETCHED", "response_bytes": len(raw), "response_sha256": sha256(raw), "observed_fields": parse_header_fields(raw, route)})
            if prefix_marker and prefix_marker not in raw:
                result["status"] = "PREFIX_MARKER_NOT_FOUND"
            return result
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            result["status"] = "HTTP_ERROR_BODY_OVER_LIMIT"
            return result
        budget.add(len(raw))
        result.update({"status": "HTTP_ERROR", "http_status": int(exc.code), "content_type": str(exc.headers.get("Content-Type", "")), "response_bytes": len(raw), "response_sha256": sha256(raw), "observed_fields": parse_header_fields(raw, route), "error_excerpt": " ".join(raw.decode("utf-8", errors="replace").split())[:200]})
        return result
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.update({"status": "TRANSPORT_ERROR", "error_type": type(exc).__name__})
        return result


def run_probe(request: dict[str, str], r1_path: Path, r2_path: Path, output: Path) -> dict[str, Any]:
    r1_keys = {key for key, value in EXPECTED.items() if value["r1"]}
    r2_keys = set(EXPECTED) - r1_keys
    r1 = validate_receipt(r1_path, R1_RUN_ID, R1_FINGERPRINT, r1_keys)
    r2 = validate_receipt(r2_path, R2_RUN_ID, R2_FINGERPRINT, r2_keys)
    budget = Budget()
    samples = []
    complete = True
    for accession, exp in EXPECTED.items():
        cik = exp["cik"]
        base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}"
        routes = (
            ("index_headers", f"{base}/{accession}-index-headers.html", None),
            ("raw_sgml_header", f"{base}/{accession}.hdr.sgml", None),
            ("complete_submission_header_prefix", f"{base}/{accession}.txt", b"</SEC-HEADER>"),
        )
        item = {"accession": accession, **exp, "probes": []}
        for route, url, marker in routes:
            observation = fetch_header(url, route, budget, marker)
            if observation.get("status") not in {"FETCHED", "FETCHED_PREFIX", "HTTP_ERROR"}:
                complete = False
            item["probes"].append(observation)
        changes = [p.get("observed_fields", {}).get("date_of_filing_date_change") for p in item["probes"] if p.get("observed_fields", {}).get("date_of_filing_date_change")]
        item["date_of_filing_date_change_observations"] = changes
        item["date_change_field_observed"] = bool(changes)
        item["interpretation"] = "DATE_CHANGE_FIELD_OBSERVED" if changes else "NO_DATE_CHANGE_FIELD_OBSERVED_IN_CAPTURED_HEADERS_NOT_PROOF_OF_ABSENCE"
        samples.append(item)
    receipt = {
        "schema_version": 1,
        "record_type": "q104_i19_filing_date_change_header_probe",
        "status": "DATE_CHANGE_HEADER_PROBE_COMPLETE" if complete and len(samples) == 8 else "DATE_CHANGE_HEADER_PROBE_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "request_sequence": request["REQUEST_SEQUENCE"],
        "source_r1_run_id": R1_RUN_ID,
        "source_r1_receipt_fingerprint": R1_FINGERPRINT,
        "source_r2_run_id": R2_RUN_ID,
        "source_r2_receipt_fingerprint": R2_FINGERPRINT,
        "sample_count": len(samples),
        "probe_count_expected": 24,
        "probe_count_captured": sum(len(x["probes"]) for x in samples),
        "date_change_field_observed_accessions": [x["accession"] for x in samples if x["date_change_field_observed"]],
        "response_bytes": budget.used,
        "response_budget_bytes": MAX_TOTAL_BYTES,
        "samples": samples,
        "source_precedence_decided": False,
        "acceptance_time_gate_cleared": False,
        "historical_archive_gate_cleared": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "next_gate": "Review date-change field observations and official filing-detail evidence before any separate field-precedence decision; no date arithmetic or blanket override.",
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt_fingerprint": receipt["receipt_fingerprint"], "probe_count_captured": receipt["probe_count_captured"], "date_change_field_observed_accessions": receipt["date_change_field_observed_accessions"], "response_bytes": receipt["response_bytes"]}, sort_keys=True))
    if receipt["status"] != "DATE_CHANGE_HEADER_PROBE_COMPLETE":
        raise ProbeError("Q104_DATE_CHANGE_HEADER_PROBE_INCOMPLETE")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--r1", type=Path, required=True)
    parser.add_argument("--r2", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = read_request(args.request)
    run_probe(request, args.r1, args.r2, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
