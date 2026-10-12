"""Read-only, bounded EDGAR-header evidence for three frozen Q220 sample keys.

This probe does not retrieve daily Feed archives or primary documents. It tests whether
the official filing-header routes expose the acceptance timestamp absent from the Feed's
original-submission wrappers. Source hash and research gates remain blocked.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SOURCE_RUN_ID = "38254139755"
SOURCE_ARTIFACT_ID = "11749259509"
SOURCE_ARTIFACT_NAME = "q220-primary-source-vintage-forensics-38254139755-1"
SOURCE_RECEIPT_GIT_BLOB_SHA = "4976ded2b7e9ca78c746d2b016d948713cb6659a"
SOURCE_RECEIPT_SHA256 = "4b690fd6c310393b2ef3b18ab57c85fc5763912ed7fe9ec5a7f46d347b99baab"
SOURCE_RECEIPT_FINGERPRINT = "840f280cbcb1fdbe4b2fbaa88f8d7f02edf447799e13fe0171d37fcd57f3221b"
SOURCE_LINEAGE_RECEIPT_FINGERPRINT = "c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075"
SOURCE_POPULATION_RECEIPT_FINGERPRINT = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
EXPECTED_HASH_FAILURE_COUNT = 55
MAX_HEADER_RESPONSE_BYTES = 262_144
MAX_TOTAL_DOWNLOAD_BYTES = 3_000_000
REQUEST_GAP_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 60
USER_AGENT = "DWR-debug/trading-agent-public Q220 header-only evidence research@example.invalid"
SAMPLE_PINS = (
    {
        "record_key": "0000064040|0000064040-19-000059|10-K|2019-02-13",
        "accession": "0000064040-19-000059",
        "cik": "0000064040",
        "form": "10-K",
        "filed_date": "2019-02-13",
        "primary_filename": "spgi-20181231x10k.htm",
    },
    {
        "record_key": "0001090012|0001564590-19-003382|10-K|2019-02-20",
        "accession": "0001564590-19-003382",
        "cik": "0001090012",
        "form": "10-K",
        "filed_date": "2019-02-20",
        "primary_filename": "dvn-10k_20181231.htm",
    },
    {
        "record_key": "0000064040|0000064040-25-000052|10-K|2025-02-11",
        "accession": "0000064040-25-000052",
        "cik": "0000064040",
        "form": "10-K",
        "filed_date": "2025-02-11",
        "primary_filename": "spgi-20241231.htm",
    },
)
FROZEN_REQUEST_VALUES = {
    "RUN_Q220_BOUNDED_HEADER_EVIDENCE": "true",
    "REASON": "OBSERVE_FIXED_Q220_ACCEPTANCE_HEADERS_WITHOUT_FEED_OR_PRIMARY_DOWNLOADS",
    "SOURCE_RUN_ID": SOURCE_RUN_ID,
    "SOURCE_ARTIFACT_ID": SOURCE_ARTIFACT_ID,
    "SOURCE_ARTIFACT_NAME": SOURCE_ARTIFACT_NAME,
    "SOURCE_RECEIPT_GIT_BLOB_SHA": SOURCE_RECEIPT_GIT_BLOB_SHA,
    "SOURCE_RECEIPT_SHA256": SOURCE_RECEIPT_SHA256,
    "SOURCE_RECEIPT_FINGERPRINT": SOURCE_RECEIPT_FINGERPRINT,
    "SOURCE_LINEAGE_RECEIPT_FINGERPRINT": SOURCE_LINEAGE_RECEIPT_FINGERPRINT,
    "SOURCE_POPULATION_RECEIPT_FINGERPRINT": SOURCE_POPULATION_RECEIPT_FINGERPRINT,
    "SOURCE_HASH_FAILURE_COUNT": str(EXPECTED_HASH_FAILURE_COUNT),
    "SAMPLE_COUNT": str(len(SAMPLE_PINS)),
    "MAX_HEADER_RESPONSE_BYTES": str(MAX_HEADER_RESPONSE_BYTES),
    "MAX_TOTAL_DOWNLOAD_BYTES": str(MAX_TOTAL_DOWNLOAD_BYTES),
    "NO_FEED_DOWNLOADS": "true",
    "NO_PRIMARY_DOCUMENT_DOWNLOADS": "true",
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}


class HeaderEvidenceError(ValueError):
    """A frozen input or bounded header-evidence invariant failed."""


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
            raise HeaderEvidenceError("Q220_HEADER_TOTAL_DOWNLOAD_BUDGET_EXCEEDED")
        self.used += count


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def git_blob_sha1(body: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(body)).encode("ascii") + b"\0" + body).hexdigest()


def canonical_receipt_fingerprint(payload: dict[str, Any]) -> str:
    clean = dict(payload)
    clean.pop("receipt_fingerprint", None)
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded)


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise HeaderEvidenceError(f"Q220_HEADER_REQUEST_INVALID_LINE:{line_number}")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value or key in values:
            raise HeaderEvidenceError(f"Q220_HEADER_REQUEST_INVALID_KEY_VALUE:{line_number}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise HeaderEvidenceError("Q220_HEADER_REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise HeaderEvidenceError("Q220_HEADER_REQUEST_VALUE_MISMATCH:" + key)
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise HeaderEvidenceError("Q220_HEADER_REQUEST_SEQUENCE_INVALID")
    return values


def load_frozen_run_receipt(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if git_blob_sha1(raw) != SOURCE_RECEIPT_GIT_BLOB_SHA:
        raise HeaderEvidenceError("Q220_HEADER_SOURCE_RECEIPT_BLOB_MISMATCH")
    if sha256(raw) != SOURCE_RECEIPT_SHA256:
        raise HeaderEvidenceError("Q220_HEADER_SOURCE_RECEIPT_SHA256_MISMATCH")
    receipt = json.loads(raw.decode("utf-8"))
    if receipt.get("receipt_fingerprint") != SOURCE_RECEIPT_FINGERPRINT:
        raise HeaderEvidenceError("Q220_HEADER_SOURCE_RECEIPT_FINGERPRINT_MISMATCH")
    if canonical_receipt_fingerprint(receipt) != SOURCE_RECEIPT_FINGERPRINT:
        raise HeaderEvidenceError("Q220_HEADER_SOURCE_RECEIPT_CANONICAL_FINGERPRINT_MISMATCH")
    expected = {
        "candidate_id": "Q220",
        "status": "FORENSIC_COMPARISON_INCOMPLETE",
        "source_receipt_fingerprint": SOURCE_LINEAGE_RECEIPT_FINGERPRINT,
        "source_population_receipt_fingerprint": SOURCE_POPULATION_RECEIPT_FINGERPRINT,
        "source_hash_failure_count": EXPECTED_HASH_FAILURE_COUNT,
        "completed_sample_count": 0,
        "gate_positive": False,
        "request_sequence": "2026-10-12T13:05:00Z",
        "sample_record_keys": [pin["record_key"] for pin in SAMPLE_PINS],
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise HeaderEvidenceError("Q220_HEADER_SOURCE_RECEIPT_VALUE_MISMATCH:" + key)
    if receipt.get("source_download_bytes") != 2_829_769_099:
        raise HeaderEvidenceError("Q220_HEADER_SOURCE_FEED_DOWNLOAD_COUNT_MISMATCH")
    if receipt.get("live_execution") is not False or receipt.get("orders_enabled") is not False:
        raise HeaderEvidenceError("Q220_HEADER_SOURCE_SAFETY_MISMATCH")
    samples = receipt.get("samples")
    if not isinstance(samples, list) or len(samples) != len(SAMPLE_PINS):
        raise HeaderEvidenceError("Q220_HEADER_SOURCE_SAMPLE_COUNT_MISMATCH")
    by_key = {x.get("record_key"): x for x in samples if isinstance(x, dict)}
    for pin in SAMPLE_PINS:
        sample = by_key.get(pin["record_key"])
        if sample is None:
            raise HeaderEvidenceError("Q220_HEADER_SAMPLE_KEY_MISSING:" + pin["record_key"])
        expected_sample = {
            "accession": pin["accession"],
            "cik": pin["cik"],
            "form": pin["form"],
            "filed_date": pin["filed_date"],
            "primary_filename": pin["primary_filename"],
            "identity_validated": False,
            "source_vintage_proven": False,
        }
        for key, value in expected_sample.items():
            if sample.get(key) != value:
                raise HeaderEvidenceError("Q220_HEADER_SAMPLE_VALUE_MISMATCH:" + key + ":" + pin["record_key"])
        header = sample.get("daily_feed", {}).get("submission_header", {})
        if header.get("acceptance_datetime_iso") is not None:
            raise HeaderEvidenceError("Q220_HEADER_SOURCE_EXPECTED_MISSING_ACCEPTANCE_DATETIME")
    return receipt


def parse_header_observation(body: bytes, source_type: str) -> dict[str, Any]:
    """Capture observed fields only; equality is checked by the caller."""
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
        rb"FILED AS OF DATE:\s*([0-9]{8})",
        rb"<FILING-DATE>\s*([0-9]{8})",
    ))
    if filed and re.fullmatch(r"\d{8}", filed):
        filed = f"{filed[:4]}-{filed[4:6]}-{filed[6:8]}"
    accepted = capture((rb"<ACCEPTANCE-DATETIME>\s*([0-9]{14})", rb"ACCEPTANCE-DATETIME:\s*([0-9]{14})"))
    if accepted and re.fullmatch(r"\d{14}", accepted):
        accepted = f"{accepted[:4]}-{accepted[4:6]}-{accepted[6:8]}T{accepted[8:10]}:{accepted[10:12]}:{accepted[12:14]}"
    changed = capture((rb"<DATE-OF-FILING-DATE-CHANGE>\s*([0-9]{8})", rb"DATE AS OF CHANGE:\s*([0-9]{8})"))
    if changed and re.fullmatch(r"\d{8}", changed):
        changed = f"{changed[:4]}-{changed[4:6]}-{changed[6:8]}"
    return {
        "source_type": source_type,
        "accession": accession,
        "filer_cik": cik,
        "form": form,
        "filing_date": filed,
        "acceptance_datetime": accepted,
        "filing_date_change": changed,
    }


def fetch_header(
    url: str,
    budget: DownloadBudget,
    *,
    max_bytes: int,
    prefix_marker: bytes | None = None,
) -> dict[str, Any]:
    budget.wait()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,text/plain,*/*",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    meta: dict[str, Any] = {
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
            content_length = headers.get("Content-Length")
            declared = int(content_length) if content_length and str(content_length).isdigit() else None
            meta.update({
                "final_url": str(response.geturl()),
                "http_status": int(getattr(response, "status", 200)),
                "content_type": str(headers.get("Content-Type", "")),
                "content_length_header": declared,
                "last_modified": str(headers.get("Last-Modified", "")),
                "etag": str(headers.get("ETag", "")),
            })
            if prefix_marker is None and declared is not None and declared > max_bytes:
                return {**meta, "status": "SKIPPED_DECLARED_LENGTH_OVER_LIMIT", "response_bytes": 0, "response_sha256": None, "_body": b""}
            while len(body) < max_bytes + (1 if prefix_marker is None else 0):
                wanted = max_bytes + (1 if prefix_marker is None else 0) - len(body)
                amount = min(32_768 if prefix_marker is None else 1024, wanted)
                try:
                    chunk = response.read(amount)
                except (http.client.HTTPException, urllib.error.URLError, TimeoutError, OSError) as exc:
                    raw_partial = bytes(body)
                    return {
                        **meta,
                        "status": "INCOMPLETE_READ",
                        "response_bytes": len(raw_partial),
                        "response_sha256": sha256(raw_partial) if raw_partial else None,
                        "error": f"{type(exc).__name__}:{exc}"[:500],
                        "_body": b"",
                    }
                if not chunk:
                    break
                budget.add(len(chunk))
                body.extend(chunk)
                if prefix_marker is not None and prefix_marker.lower() in bytes(body).lower():
                    break
            raw = bytes(body)
            digest = sha256(raw) if raw else None
            if prefix_marker is not None:
                marker_index = raw.lower().find(prefix_marker.lower())
                marker_found = marker_index >= 0
                header_only = raw[:marker_index + len(prefix_marker)] if marker_found else b""
                return {
                    **meta,
                    "status": "FETCHED_PREFIX" if marker_found else "HEADER_PREFIX_LIMIT_OR_EOF",
                    "prefix_marker_found": marker_found,
                    "response_bytes": len(raw),
                    "response_sha256": digest,
                    # Parse only through </SEC-HEADER>; any small chunk over-read is not retained as evidence.
                    "_body": header_only,
                }
            if len(raw) > max_bytes:
                return {**meta, "status": "SKIPPED_ACTUAL_LENGTH_OVER_LIMIT", "response_bytes": len(raw), "response_sha256": digest, "_body": b""}
            if declared is not None and len(raw) != declared:
                return {
                    **meta,
                    "status": "INCOMPLETE_CONTENT_LENGTH",
                    "response_bytes": len(raw),
                    "response_sha256": digest,
                    "error": f"CONTENT_LENGTH_MISMATCH:declared={declared}:received={len(raw)}",
                    "_body": b"",
                }
            return {**meta, "status": "FETCHED", "response_bytes": len(raw), "response_sha256": digest, "_body": raw}
    except urllib.error.HTTPError as exc:
        headers = exc.headers or {}
        meta.update({
            "final_url": str(getattr(exc, "url", url)),
            "http_status": int(exc.code),
            "content_type": str(headers.get("Content-Type", "")),
            "content_length_header": int(headers.get("Content-Length")) if str(headers.get("Content-Length", "")).isdigit() else None,
            "last_modified": str(headers.get("Last-Modified", "")),
            "etag": str(headers.get("ETag", "")),
        })
        return {**meta, "status": "HTTP_ERROR", "response_bytes": 0, "response_sha256": None, "error": f"HTTP_{exc.code}", "_body": b""}
    except (urllib.error.URLError, TimeoutError, OSError, HeaderEvidenceError) as exc:
        return {
            **meta,
            "status": "FETCH_ERROR",
            "response_bytes": len(body),
            "response_sha256": sha256(bytes(body)) if body else None,
            "error": f"{type(exc).__name__}:{exc}"[:500],
            "_body": b"",
        }


def run_probe(request: dict[str, str], source_receipt_path: Path, output: Path) -> dict[str, Any]:
    source = load_frozen_run_receipt(source_receipt_path)
    budget = DownloadBudget(MAX_TOTAL_DOWNLOAD_BYTES)
    sample_results = []
    for pin in SAMPLE_PINS:
        base = (
            f"https://www.sec.gov/Archives/edgar/data/{int(pin['cik'])}/"
            f"{pin['accession'].replace('-', '')}"
        )
        routes = (
            ("index_headers", f"{base}/{pin['accession']}-index-headers.html", None),
            ("raw_sgml_header", f"{base}/{pin['accession']}.hdr.sgml", None),
            ("complete_submission_header_prefix", f"{base}/{pin['accession']}.txt", b"</SEC-HEADER>"),
        )
        sample = {
            **pin,
            "source_feed_acceptance_datetime": None,
            "probes": [],
        }
        for route_name, url, prefix_marker in routes:
            result = fetch_header(
                url,
                budget,
                max_bytes=MAX_HEADER_RESPONSE_BYTES,
                prefix_marker=prefix_marker,
            )
            raw = result.pop("_body", b"")
            probe = {**result, "route": route_name}
            probe["observed_identity"] = parse_header_observation(raw, route_name) if raw else None
            sample["probes"].append(probe)
        sample_results.append(sample)

    status_checks = []
    for sample in sample_results:
        valid_routes = True
        timestamps = []
        for probe in sample["probes"]:
            observation = probe.get("observed_identity")
            if probe.get("status") not in {"FETCHED", "FETCHED_PREFIX"} or not observation:
                valid_routes = False
                continue
            expected = {
                "accession": sample["accession"],
                "filer_cik": sample["cik"],
                "form": sample["form"],
                "filing_date": sample["filed_date"],
            }
            if any(observation.get(key) != value for key, value in expected.items()):
                valid_routes = False
            if not observation.get("acceptance_datetime"):
                valid_routes = False
            else:
                timestamps.append(observation["acceptance_datetime"])
        timestamp_consistent = len(timestamps) == 3 and len(set(timestamps)) == 1
        item_status = "HEADER_EVIDENCE_COMPLETE" if valid_routes and timestamp_consistent else "HEADER_EVIDENCE_INCOMPLETE"
        sample["timestamp_consistent_across_routes"] = timestamp_consistent
        sample["acceptance_timestamp_observed"] = timestamps[0] if timestamp_consistent else None
        sample["identity_checks_passed"] = valid_routes
        sample["status"] = item_status
        status_checks.append(item_status == "HEADER_EVIDENCE_COMPLETE")

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q220_bounded_header_evidence",
        "status": "HEADER_EVIDENCE_COMPLETE" if all(status_checks) else "HEADER_EVIDENCE_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "request_sequence": request["REQUEST_SEQUENCE"],
        "source_run_id": SOURCE_RUN_ID,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_receipt_git_blob_sha": SOURCE_RECEIPT_GIT_BLOB_SHA,
        "source_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "source_receipt_fingerprint": SOURCE_RECEIPT_FINGERPRINT,
        "source_population_receipt_fingerprint": SOURCE_POPULATION_RECEIPT_FINGERPRINT,
        "sample_count": len(sample_results),
        "probe_count": sum(len(x["probes"]) for x in sample_results),
        "source_download_bytes": budget.used,
        "total_download_budget_bytes": MAX_TOTAL_DOWNLOAD_BYTES,
        "maximum_header_response_bytes": MAX_HEADER_RESPONSE_BYTES,
        "no_feed_downloads": True,
        "no_primary_document_downloads": True,
        "samples": sample_results,
        "research_boundary": {
            "q220_acceptance_timestamp_gate_cleared": False,
            "q220_source_hash_gate_cleared": False,
            "expected_source_hash_failure_count": EXPECTED_HASH_FAILURE_COUNT,
            "next_action": "Use these bounded header observations only as supplemental timestamp evidence; investigate all 55 frozen source-hash disagreements separately. Do not fetch daily Feed archives, rewrite expected hashes, or promote Q220 from this result.",
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "census_restart": False,
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    receipt["receipt_fingerprint"] = canonical_receipt_fingerprint(receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = read_request(args.request)
    receipt = run_probe(request, args.source_receipt, args.output)
    print(json.dumps({
        "status": receipt["status"],
        "receipt_fingerprint": receipt["receipt_fingerprint"],
        "probe_count": receipt["probe_count"],
        "source_download_bytes": receipt["source_download_bytes"],
    }, sort_keys=True))
    if receipt["status"] != "HEADER_EVIDENCE_COMPLETE":
        raise HeaderEvidenceError("Q220_HEADER_EVIDENCE_INCOMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
