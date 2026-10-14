"""Bounded Q220 audit of the SEC complete-submission .txt representation.

Only three preregistered accessions are requested. Complete .txt response bodies
are never written to disk; the artifact retains only a bounded pre-document
header prefix and the exact selected primary <DOCUMENT> block for offline replay.
This is diagnostic-only and cannot change Q220 source hashes or research gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from automation import q220_primary_source_vintage_forensics as forensic

ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = "research/run_requests/q220_complete_submission_representation_audit.trigger"
PREREG_PATH = "research/preregistrations/q220_complete_submission_representation_audit_2026_10_14.json"
POPULATION_PATH = "research/evidence/q220_as_filed_xbrl_population_latest.json"
POPULATION_BLOB_SHA1 = "4a1abe7f4633a5c8ee810e6e0f7208dc75103ad2"
POPULATION_FP = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
POPULATION_GATE_CODE_SHA256 = "2a455f02835b2d85308ac2c178777999fc059312218275a697204313de8cab0d"
POPULATION_CONTRACT_SHA256 = "5014eb888a4e66502cb30c9ec5208caec1de65425dad3c1bd3feb8b17a29ac88"
COMPILER_PATH = "research/evidence/q220_historical_representation_pit_latest.json"
COMPILER_FP = "b394356b05c0c3e512f750174ffd501aafd9de8809da2266115b57c21d5bb93e"
SOURCE_FIXTURE_PATH = "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json"
SOURCE_FIXTURE_BLOB_SHA1 = "2a3abbff6c6950e4f11d85dba92cb9c57a5c7ee0"
SOURCE_FIXTURE_FP = "c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075"
FORENSICS_RUN_ID = 38254139755
FORENSICS_ARTIFACT_ID = 11749259509
FORENSICS_FP = "840f280cbcb1fdbe4b2fbaa88f8d7f02edf447799e13fe0171d37fcd57f3221b"
REQUEST_SEQUENCE = "2026-10-14T18:43:14Z"

MAX_SAMPLE_COUNT = 3
MAX_COMPLETE_SUBMISSION_BYTES = 45_000_000
MAX_TOTAL_DOWNLOAD_BYTES = 120_000_000
MAX_HEADER_PREFIX_BYTES = 2_000_000
MAX_PRIMARY_DOCUMENT_BLOCK_BYTES = 16_000_000
REQUEST_TIMEOUT_SECONDS = 180
REQUEST_GAP_SECONDS = 1.0
# Reuse the repository's already established SEC research User-Agent; do not
# invent an address or vary request profiles in this experiment.
USER_AGENT = forensic.USER_AGENT

SAMPLES: tuple[dict[str, Any], ...] = (
    {
        "record_key": "0000064040|0000064040-19-000059|10-K|2019-02-13",
        "cik": "0000064040",
        "accession": "0000064040-19-000059",
        "form": "10-K",
        "filed_date": "2019-02-13",
        "acceptance_datetime": "2019-02-12T18:15:22",
        "primary_filename": "spgi-20181231x10k.htm",
        "expected_sha256": "27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83",
        "expected_bytes": 4774458,
        "feed_text_sha256": "aa1f89efdf13029de9dd8f7eb020502dd518d4350513d4ef041ba67d902ef368",
        "feed_text_bytes": 4774237,
        "feed_submission_member_sha256": "e73d211f2bb02f099d9a8559735fb627678d7db0e3b11ae491eb80ae2b45fa54",
        "feed_submission_member_bytes": 26429640,
        "prior_current_primary_sha256": "08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb",
        "prior_current_primary_bytes": 4774458,
    },
    {
        "record_key": "0001090012|0001564590-19-003382|10-K|2019-02-20",
        "cik": "0001090012",
        "accession": "0001564590-19-003382",
        "form": "10-K",
        "filed_date": "2019-02-20",
        "acceptance_datetime": "2019-02-20T12:18:53",
        "primary_filename": "dvn-10k_20181231.htm",
        "expected_sha256": "b024964aa602547d102af1f9cd51c61a3d723ab25b21ef5686b02ac8d4f40dd1",
        "expected_bytes": 10558506,
        "feed_text_sha256": "e72d769d3ebcd9fddee3732785dd94d530f6d81a03c94c7f9343fb5bda25e2cc",
        "feed_text_bytes": 10558411,
        "feed_submission_member_sha256": "7dc11f4ecefd080e17daf09f508db575fe0fef823b07d5f3e435ef078b48815b",
        "feed_submission_member_bytes": 37864414,
        "prior_current_primary_sha256": "5dfdcb52a74efa233ca0c65bf58b2caad44d859f4ecd23e618142c71b2d25a59",
        "prior_current_primary_bytes": 10558506,
    },
    {
        "record_key": "0000064040|0000064040-25-000052|10-K|2025-02-11",
        "cik": "0000064040",
        "accession": "0000064040-25-000052",
        "form": "10-K",
        "filed_date": "2025-02-11",
        "acceptance_datetime": "2025-02-11T17:29:21",
        "primary_filename": "spgi-20241231.htm",
        "expected_sha256": "afe05282d5d5af7f3068287cceaa679db962264d5d704d2d32ac19e2c4d3531d",
        "expected_bytes": 4133816,
        "feed_text_sha256": "4446f768a1dc88f7dae9c67abf55694393425e441712fbf1fafe0d0a30523393",
        "feed_text_bytes": 4133721,
        "feed_submission_member_sha256": "53e774ec08da24e02ac18b0910fa2526421a7326be94eca7ffce2f4349543f13",
        "feed_submission_member_bytes": 22542746,
        "prior_current_primary_sha256": "cb84c569cef0a88fffbe6114ad30607af4a99068b10a3d0f135ebdf7242b7a55",
        "prior_current_primary_bytes": 4133816,
    },
)

REQUEST_VALUES = {
    "RUN_Q220_COMPLETE_SUBMISSION_REPRESENTATION_AUDIT": "true",
    "REASON": "COMPARE_FROZEN_PRIMARY_HASHES_WITH_THE_EXACT_PRIMARY_DOCUMENT_BLOCK_IN_THE_OFFICIAL_COMPLETE_SUBMISSION_TXT_ROUTE",
    "SOURCE_FIXTURE_PATH": SOURCE_FIXTURE_PATH,
    "SOURCE_FIXTURE_BLOB_SHA1": SOURCE_FIXTURE_BLOB_SHA1,
    "SOURCE_FIXTURE_FINGERPRINT": SOURCE_FIXTURE_FP,
    "SOURCE_POPULATION_PATH": POPULATION_PATH,
    "SOURCE_POPULATION_BLOB_SHA1": POPULATION_BLOB_SHA1,
    "SOURCE_POPULATION_FINGERPRINT": POPULATION_FP,
    "SOURCE_POPULATION_GATE_CODE_SHA256": POPULATION_GATE_CODE_SHA256,
    "SOURCE_POPULATION_CONTRACT_SHA256": POPULATION_CONTRACT_SHA256,
    "COMPILER_PATH": COMPILER_PATH,
    "COMPILER_FINGERPRINT": COMPILER_FP,
    "FORENSICS_RUN_ID": str(FORENSICS_RUN_ID),
    "FORENSICS_ARTIFACT_ID": str(FORENSICS_ARTIFACT_ID),
    "FORENSICS_RECEIPT_FINGERPRINT": FORENSICS_FP,
    "SAMPLE_COUNT": "3",
    "MAX_COMPLETE_SUBMISSION_BYTES": str(MAX_COMPLETE_SUBMISSION_BYTES),
    "MAX_TOTAL_DOWNLOAD_BYTES": str(MAX_TOTAL_DOWNLOAD_BYTES),
    "MAX_HEADER_PREFIX_BYTES": str(MAX_HEADER_PREFIX_BYTES),
    "MAX_PRIMARY_DOCUMENT_BLOCK_BYTES": str(MAX_PRIMARY_DOCUMENT_BLOCK_BYTES),
    "REQUEST_TIMEOUT_SECONDS": str(REQUEST_TIMEOUT_SECONDS),
    "RETRIES": "0",
    "FEED_ARCHIVE_DOWNLOADS": "0",
    "DIRECT_PRIMARY_HTML_REQUESTS": "0",
    "PERSIST_COMPLETE_SUBMISSION_TEXT": "false",
    "PAPER_ONLY": "true",
    "LIVE_TRADING_ENABLED": "false",
    "ORDERS_ENABLED": "false",
    "AUTOMATIC_PROMOTION": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
    "REQUEST_SEQUENCE": REQUEST_SEQUENCE,
}


class AuditError(ValueError):
    """A frozen request, source, byte boundary, identity, or artifact is invalid."""


class DownloadBudget:
    def __init__(self, maximum: int = MAX_TOTAL_DOWNLOAD_BYTES) -> None:
        self.maximum = maximum
        self.used = 0
        self.last_request_monotonic = 0.0

    def wait(self) -> None:
        delay = REQUEST_GAP_SECONDS - (time.monotonic() - self.last_request_monotonic)
        if delay > 0:
            time.sleep(delay)
        self.last_request_monotonic = time.monotonic()

    def add(self, count: int) -> None:
        if count < 0 or self.used + count > self.maximum:
            raise AuditError("Q220_COMPLETE_SUBMISSION_TOTAL_BUDGET_EXCEEDED")
        self.used += count


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def canonical_fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field, None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(encoded)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError("PINNED_JSON_UNREADABLE:" + str(path)) from exc
    if not isinstance(value, dict):
        raise AuditError("PINNED_JSON_NOT_OBJECT:" + str(path))
    return value


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw or raw.strip() != raw or "=" not in raw:
            raise AuditError(f"REQUEST_INVALID_LINE:{line_number}")
        key, value = raw.split("=", 1)
        if not key or not value or key in values:
            raise AuditError(f"REQUEST_DUPLICATE_OR_EMPTY_KEY:{key}")
        values[key] = value
    expected = {**REQUEST_VALUES, "REQUEST_SEQUENCE": REQUEST_SEQUENCE}
    if values != expected:
        raise AuditError("REQUEST_FROZEN_VALUE_OR_KEYSET_MISMATCH")
    return values


def find_receipt(root: Path) -> Path:
    if root.is_file():
        return root
    candidates = sorted(root.rglob("receipt.json"))
    if len(candidates) != 1:
        raise AuditError(f"PINNED_RECEIPT_COUNT_INVALID:{len(candidates)}")
    return candidates[0]


def parse_primary_document_block(
    submission: bytes,
    expected_filename: str,
) -> tuple[dict[str, Any], bytes, bytes]:
    """Extract the exact selected DOCUMENT block and its raw TEXT bytes."""
    matches: list[tuple[dict[str, Any], bytes, bytes]] = []
    for document_match in re.finditer(rb"<DOCUMENT>\s*(.*?)</DOCUMENT>", submission, re.I | re.S):
        block = document_match.group(1)
        filename_match = re.search(rb"<FILENAME>\s*([^\r\n<]+)", block, re.I)
        if not filename_match:
            continue
        filename = filename_match.group(1).decode("utf-8", "replace").strip()
        if filename.lower() != expected_filename.lower():
            continue
        text_start_match = re.search(rb"<TEXT\s*>", block, re.I)
        if not text_start_match:
            raise AuditError("PRIMARY_DOCUMENT_TEXT_BLOCK_MISSING")
        text_start = text_start_match.end()
        closers = list(re.finditer(rb"</TEXT\s*>", block[text_start:], re.I))
        valid = [m for m in closers if not block[text_start + m.end():].strip()]
        if len(valid) != 1:
            raise AuditError(f"PRIMARY_DOCUMENT_TEXT_BOUNDARY_NOT_UNIQUE:{len(valid)}")
        closer = valid[0]
        raw_text = block[text_start:text_start + closer.start()]
        full_block = document_match.group(0)
        if len(full_block) > MAX_PRIMARY_DOCUMENT_BLOCK_BYTES:
            raise AuditError("PRIMARY_DOCUMENT_BLOCK_OVER_LIMIT")
        variants = {
            "raw_text_block": {"sha256": sha256(raw_text), "bytes": len(raw_text)},
            "drop_one_leading_linebreak": {
                "sha256": sha256(raw_text[2:] if raw_text.startswith(b"\r\n") else raw_text[1:] if raw_text.startswith(b"\n") else raw_text),
                "bytes": len(raw_text[2:] if raw_text.startswith(b"\r\n") else raw_text[1:] if raw_text.startswith(b"\n") else raw_text),
            },
            "drop_outer_linebreaks": {
                "sha256": sha256(raw_text.strip(b"\r\n")),
                "bytes": len(raw_text.strip(b"\r\n")),
            },
        }
        info = {
            "filename": filename,
            "document_block_sha256": sha256(full_block),
            "document_block_bytes": len(full_block),
            "raw_text_block_sha256": sha256(raw_text),
            "raw_text_block_bytes": len(raw_text),
            "text_closing_tag_count": len(closers),
            "selected_text_closing_tag_offset_in_document": text_start + closer.start(),
            "body_hash_variants": variants,
        }
        matches.append((info, full_block, raw_text))
    if len(matches) != 1:
        raise AuditError(f"PRIMARY_DOCUMENT_MATCH_COUNT_INVALID:{len(matches)}")
    return matches[0]


def validate_preregistration(root: Path) -> dict[str, Any]:
    prereg = read_json(root / PREREG_PATH)
    bounds = prereg.get("bounds") or {}
    prereg_samples = prereg.get("samples")
    expected_prereg_samples = [
        {
            "record_key": sample["record_key"],
            "accession": sample["accession"],
            "cik": sample["cik"],
            "form": sample["form"],
            "filed_date": sample["filed_date"],
            "acceptance_datetime": sample["acceptance_datetime"],
            "primary_filename": sample["primary_filename"],
            "expected_sha256": sample["expected_sha256"],
            "expected_bytes": sample["expected_bytes"],
            "prior_feed_text_sha256": sample["feed_text_sha256"],
            "prior_feed_text_bytes": sample["feed_text_bytes"],
            "prior_feed_submission_member_sha256": sample["feed_submission_member_sha256"],
            "prior_feed_submission_member_bytes": sample["feed_submission_member_bytes"],
            "prior_current_primary_sha256": sample["prior_current_primary_sha256"],
            "prior_current_primary_bytes": sample["prior_current_primary_bytes"],
        }
        for sample in SAMPLES
    ]
    frozen = prereg.get("frozen_inputs") or {}
    if (
        prereg.get("candidate_id") != "Q220"
        or prereg.get("status") != "PREREGISTERED_DIAGNOSTIC_ONLY_NO_GATE_CHANGE"
        or prereg.get("request_sequence") != REQUEST_SEQUENCE
        or bounds.get("sample_count") != 3
        or prereg_samples != expected_prereg_samples
        or bounds.get("max_total_download_bytes") != MAX_TOTAL_DOWNLOAD_BYTES
        or bounds.get("max_complete_submission_bytes_each") != MAX_COMPLETE_SUBMISSION_BYTES
        or bounds.get("retry_count") != 0
        or bounds.get("persist_complete_submission_text") is not False
        or frozen.get("population_receipt_fingerprint") != POPULATION_FP
        or frozen.get("compiler_receipt_fingerprint") != COMPILER_FP
        or frozen.get("prior_feed_forensics_receipt_fingerprint") != FORENSICS_FP
        or (prereg.get("gates") or {}).get("source_complete") is not False
        or (prereg.get("gates") or {}).get("historical_pit_positive") is not False
        or prereg.get("gate_change_authorized") is not False
        or (prereg.get("safety") or {}).get("paper_only") is not True
        or (prereg.get("safety") or {}).get("live_trading_enabled") is not False
        or (prereg.get("safety") or {}).get("orders_enabled") is not False
        or (prereg.get("safety") or {}).get("automatic_promotion") is not False
    ):
        raise AuditError("PREREGISTRATION_CONTRACT_MISMATCH")
    return prereg


def validate_frozen_inputs(root: Path, forensics_artifact_dir: Path) -> dict[str, Any]:
    request = read_request(root / REQUEST_PATH)
    prereg = validate_preregistration(root)
    fixture_raw = (root / SOURCE_FIXTURE_PATH).read_bytes()
    if git_blob_sha1(fixture_raw) != SOURCE_FIXTURE_BLOB_SHA1:
        raise AuditError("SOURCE_FIXTURE_BLOB_SHA1_MISMATCH")
    fixture = json.loads(fixture_raw.decode("utf-8"))
    if canonical_fingerprint(fixture) != SOURCE_FIXTURE_FP:
        raise AuditError("SOURCE_FIXTURE_RECEIPT_FINGERPRINT_MISMATCH")
    if (
        fixture.get("candidate_id") != "Q220"
        or fixture.get("gate_positive") is not False
        or fixture.get("source_hash_failure_count") != 55
        or fixture.get("source_population_receipt_fingerprint") != POPULATION_FP
    ):
        raise AuditError("SOURCE_FIXTURE_BLOCKED_CONTRACT_MISMATCH")

    population_raw = (root / POPULATION_PATH).read_bytes()
    if git_blob_sha1(population_raw) != POPULATION_BLOB_SHA1:
        raise AuditError("POPULATION_BLOB_SHA1_MISMATCH")
    population = json.loads(population_raw.decode("utf-8"))
    if (
        population.get("receipt_fingerprint") != POPULATION_FP
        or canonical_fingerprint(population) != POPULATION_FP
        or population.get("status") != "Q220_AS_FILED_XBRL_POPULATION_COMPLETED"
        or population.get("candidate_id") != "Q220"
        or population.get("record_count") != 55
        or population.get("failure_count") != 0
        or population.get("gate_code_sha256") != POPULATION_GATE_CODE_SHA256
        or population.get("contract_sha256") != POPULATION_CONTRACT_SHA256
    ):
        raise AuditError("POPULATION_RECEIPT_PIN_OR_STATUS_MISMATCH")
    contract_raw = (root / "research/preregistrations/q220_as_filed_xbrl_population_contract_2026_10_06.json").read_bytes()
    if sha256(contract_raw) != POPULATION_CONTRACT_SHA256:
        raise AuditError("POPULATION_CONTRACT_SHA256_MISMATCH")

    compiler = read_json(root / COMPILER_PATH)
    if (
        compiler.get("receipt_fingerprint") != COMPILER_FP
        or canonical_fingerprint(compiler) != COMPILER_FP
        or compiler.get("candidate_id") != "Q220"
        or compiler.get("status") != "Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED"
        or compiler.get("source_population_receipt_fingerprint") != POPULATION_FP
        or compiler.get("source_hash_failure_count") != 55
        or len(compiler.get("source_hash_failures", [])) != 55
        or compiler.get("verified_primary_document_count") != 0
        or compiler.get("gate_positive") is not False
    ):
        raise AuditError("CURRENT_COMPILER_PIN_OR_BLOCKED_STATE_MISMATCH")

    population_records = {
        "|".join(str(row.get("canonical_key", {}).get(k) or "") for k in ("cik", "accession", "form", "filed_date")): row
        for row in population.get("records", [])
        if isinstance(row, dict)
    }
    failures = {str(row.get("record_key")): row for row in compiler.get("source_hash_failures", []) if isinstance(row, dict)}
    for sample in SAMPLES:
        source = population_records.get(sample["record_key"])
        failure = failures.get(sample["record_key"])
        if not source or not failure:
            raise AuditError("SAMPLE_NOT_PRESENT_IN_FROZEN_SOURCE:" + sample["record_key"])
        if (
            source.get("primary_document") != sample["primary_filename"]
            or source.get("primary_document_sha256") != sample["expected_sha256"]
            or source.get("primary_document_bytes") != sample["expected_bytes"]
            or source.get("primary_document_source") != "company_submissions_recent"
        ):
            raise AuditError("POPULATION_SAMPLE_PIN_MISMATCH:" + sample["record_key"])
        error = str(failure.get("error") or "")
        expected = re.search(r"(?:^|:)expected=([0-9a-f]{64})(?:$|:)", error)
        expected_bytes = re.search(r"(?:^|:)expected_bytes=([0-9]+)(?:$|:)", error)
        if not expected or expected.group(1) != sample["expected_sha256"] or not expected_bytes or int(expected_bytes.group(1)) != sample["expected_bytes"]:
            raise AuditError("COMPILER_SAMPLE_PIN_MISMATCH:" + sample["record_key"])

    forensic_receipt = read_json(find_receipt(forensics_artifact_dir))
    if (
        forensic_receipt.get("record_type") != "q220_original_sec_feed_primary_hash_forensics"
        or forensic_receipt.get("candidate_id") != "Q220"
        or forensic_receipt.get("receipt_fingerprint") != FORENSICS_FP
        or canonical_fingerprint(forensic_receipt) != FORENSICS_FP
        or forensic_receipt.get("source_receipt_fingerprint") != SOURCE_FIXTURE_FP
        or forensic_receipt.get("source_population_receipt_fingerprint") != POPULATION_FP
        or forensic_receipt.get("status") != "FORENSIC_COMPARISON_INCOMPLETE"
    ):
        raise AuditError("FORENSICS_RECEIPT_PIN_OR_STATUS_MISMATCH")
    old_samples = {str(row.get("record_key")): row for row in forensic_receipt.get("samples", []) if isinstance(row, dict)}
    for sample in SAMPLES:
        row = old_samples.get(sample["record_key"])
        feed = (row or {}).get("daily_feed", {})
        primary = feed.get("primary", {})
        raw_variant = (primary.get("body_hash_variants") or {}).get("raw_text_block", {})
        if (
            not row
            or row.get("primary_filename") != sample["primary_filename"]
            or feed.get("scan_complete") is not True
            or feed.get("original_member_name") != "./" + sample["accession"] + ".nc"
            or feed.get("original_member_sha256") != sample["feed_submission_member_sha256"]
            or feed.get("original_member_bytes") != sample["feed_submission_member_bytes"]
            or raw_variant.get("sha256") != sample["feed_text_sha256"]
            or raw_variant.get("bytes") != sample["feed_text_bytes"]
            or primary.get("found") is not True
        ):
            raise AuditError("PREVIOUS_FEED_SAMPLE_PIN_MISMATCH:" + sample["record_key"])
    return {
        "request": request,
        "preregistration": prereg,
        "population": population,
        "compiler": compiler,
        "forensics": forensic_receipt,
    }


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse redirects so every sample has one exact requested URL and no fallback."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _read_response(url: str, max_bytes: int, budget: DownloadBudget) -> dict[str, Any]:
    """Single HTTP attempt. No retry, cache-busting query, or source-route fallback."""
    budget.wait()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain,*/*",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    meta: dict[str, Any] = {
        "requested_url": url,
        "final_url": url,
        "http_status": None,
        "content_type": "",
        "content_encoding": "",
        "content_length_header": None,
        "last_modified": "",
        "etag": "",
        "status": "NOT_FETCHED",
        "response_bytes": 0,
        "response_sha256": None,
        "error": None,
        "attempt_count": 1,
    }
    try:
        opener = urllib.request.build_opener(NoRedirectHandler())
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            headers = response.headers
            raw_length = headers.get("Content-Length")
            declared = int(raw_length) if raw_length and str(raw_length).isdigit() else None
            meta.update({
                "final_url": str(response.geturl()),
                "http_status": int(getattr(response, "status", 200)),
                "content_type": str(headers.get("Content-Type", "")),
                "content_encoding": str(headers.get("Content-Encoding", "")),
                "content_length_header": declared,
                "last_modified": str(headers.get("Last-Modified", "")),
                "etag": str(headers.get("ETag", "")),
            })
            if declared is not None and declared > max_bytes:
                return {**meta, "status": "DECLARED_LENGTH_OVER_LIMIT", "error": "CONTENT_LENGTH_OVER_LIMIT"}
            pieces: list[bytes] = []
            count = 0
            while count < max_bytes + 1:
                remaining_budget = budget.maximum - budget.used
                if remaining_budget <= 0:
                    return {**meta, "status": "TOTAL_BUDGET_EXHAUSTED", "response_bytes": count, "error": "TOTAL_BUDGET_EXHAUSTED"}
                wanted = min(1_048_576, max_bytes + 1 - count, remaining_budget)
                chunk = response.read(wanted)
                if not chunk:
                    break
                budget.add(len(chunk))
                pieces.append(chunk)
                count += len(chunk)
            body = b"".join(pieces)
            meta["response_bytes"] = len(body)
            meta["response_sha256"] = sha256(body)
            if len(body) > max_bytes:
                return {**meta, "status": "ACTUAL_LENGTH_OVER_LIMIT", "body": b"", "error": "CONTENT_LENGTH_OVER_LIMIT"}
            if declared is not None and len(body) != declared:
                return {**meta, "status": "INCOMPLETE_CONTENT_LENGTH", "body": b"", "error": "CONTENT_LENGTH_MISMATCH"}
            if int(meta["http_status"] or 0) != 200:
                return {**meta, "status": "HTTP_STATUS_NOT_200", "body": b"", "error": "HTTP_STATUS_NOT_200"}
            return {**meta, "status": "FETCHED", "body": body, "budget_charged": True}
    except urllib.error.HTTPError as exc:
        return {
            **meta,
            "http_status": int(exc.code),
            "final_url": str(getattr(exc, "url", url)),
            "content_type": str((exc.headers or {}).get("Content-Type", "")),
            "last_modified": str((exc.headers or {}).get("Last-Modified", "")),
            "etag": str((exc.headers or {}).get("ETag", "")),
            "status": "HTTP_ERROR",
            "error": f"HTTP_{exc.code}",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {**meta, "status": "FETCH_ERROR", "error": f"{type(exc).__name__}:{exc}"[:300]}


def complete_submission_url(sample: dict[str, Any]) -> str:
    cik = str(int(sample["cik"]))
    accession_dir = str(sample["accession"]).replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_dir}/{sample['accession']}.txt"


def extract_sample(
    sample: dict[str, Any],
    response: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    body = response.get("body")
    record: dict[str, Any] = {
        "record_key": sample["record_key"],
        "accession": sample["accession"],
        "cik": sample["cik"],
        "form": sample["form"],
        "filed_date": sample["filed_date"],
        "acceptance_datetime_expected": sample["acceptance_datetime"],
        "primary_filename": sample["primary_filename"],
        "frozen_expected_sha256": sample["expected_sha256"],
        "frozen_expected_bytes": sample["expected_bytes"],
        "prior_feed_text_sha256": sample["feed_text_sha256"],
        "prior_feed_text_bytes": sample["feed_text_bytes"],
        "prior_feed_submission_member_sha256": sample["feed_submission_member_sha256"],
        "prior_feed_submission_member_bytes": sample["feed_submission_member_bytes"],
        "prior_current_primary_sha256": sample["prior_current_primary_sha256"],
        "prior_current_primary_bytes": sample["prior_current_primary_bytes"],
        "complete_submission": {k: v for k, v in response.items() if k not in {"body", "budget_charged"}},
        "identity_validated": False,
        "primary_document_extracted": False,
        "expected_hash_reproduced": False,
        "prior_feed_body_reproduced": False,
        "error": None,
    }
    if response.get("status") != "FETCHED" or not isinstance(body, bytes):
        record["error"] = "COMPLETE_SUBMISSION_FETCH_NOT_COMPLETE"
        return record
    header_prefix = body.split(b"<DOCUMENT>", 1)[0]
    if len(header_prefix) > MAX_HEADER_PREFIX_BYTES:
        record["error"] = "SUBMISSION_HEADER_PREFIX_OVER_LIMIT"
        return record
    try:
        header = forensic.parse_submission_header(header_prefix)
        identity_checks = {
            "accession_matches": header.get("accession") == sample["accession"],
            "filer_cik_matches": header.get("filer_cik") == sample["cik"],
            "form_matches": str(header.get("form") or "").upper() == sample["form"],
            "filing_date_matches": header.get("filed_date_iso") == sample["filed_date"],
            "acceptance_datetime_matches": header.get("acceptance_datetime_iso") == sample["acceptance_datetime"],
        }
        record["submission_header"] = header
        record["identity_checks"] = identity_checks
        if not all(identity_checks.values()):
            record["error"] = "SUBMISSION_HEADER_IDENTITY_OR_CLOCK_MISMATCH"
            return record
        info, document_block, raw_text = parse_primary_document_block(body, sample["primary_filename"])
        if len(document_block) > MAX_PRIMARY_DOCUMENT_BLOCK_BYTES:
            record["error"] = "PRIMARY_DOCUMENT_BLOCK_OVER_LIMIT"
            return record
        info["expected_hash_matches_any_body_variant"] = any(
            row.get("sha256") == sample["expected_sha256"] and row.get("bytes") == sample["expected_bytes"]
            for row in info["body_hash_variants"].values()
        )
        info["matches_prior_feed_raw_text"] = (
            info["raw_text_block_sha256"] == sample["feed_text_sha256"]
            and info["raw_text_block_bytes"] == sample["feed_text_bytes"]
        )
        info["matches_prior_current_primary"] = (
            info["raw_text_block_sha256"] == sample["prior_current_primary_sha256"]
            and info["raw_text_block_bytes"] == sample["prior_current_primary_bytes"]
        )
        record["primary_document"] = info
        record["primary_document_extracted"] = True
        record["identity_validated"] = True
        record["expected_hash_reproduced"] = info["expected_hash_matches_any_body_variant"]
        record["prior_feed_body_reproduced"] = info["matches_prior_feed_raw_text"]
        rel_header = f"submission-headers/{sample['accession']}.header"
        rel_block = f"primary-document-blocks/{sample['accession']}/{sample['primary_filename']}.sgml"
        (output_dir / rel_header).parent.mkdir(parents=True, exist_ok=True)
        (output_dir / rel_block).parent.mkdir(parents=True, exist_ok=True)
        (output_dir / rel_header).write_bytes(header_prefix)
        (output_dir / rel_block).write_bytes(document_block)
        record["submission_header_artifact_path"] = rel_header
        record["submission_header_artifact_sha256"] = sha256(header_prefix)
        record["submission_header_artifact_bytes"] = len(header_prefix)
        record["primary_document_block_artifact_path"] = rel_block
        record["primary_document_block_artifact_sha256"] = sha256(document_block)
        record["primary_document_block_artifact_bytes"] = len(document_block)
        return record
    except (AuditError, ValueError) as exc:
        record["error"] = f"{type(exc).__name__}:{exc}"[:500]
        return record


def analysis_payload(
    records: list[dict[str, Any]],
    source_download_bytes: int,
    frozen_inputs: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "record_type": "q220_complete_submission_representation_audit",
        "candidate_id": "Q220",
        "request_sequence": REQUEST_SEQUENCE,
        "source_population_receipt_fingerprint": POPULATION_FP,
        "source_population_blob_sha1": POPULATION_BLOB_SHA1,
        "compiler_receipt_fingerprint": COMPILER_FP,
        "frozen_fixture_receipt_fingerprint": SOURCE_FIXTURE_FP,
        "prior_feed_forensics_run_id": FORENSICS_RUN_ID,
        "prior_feed_forensics_artifact_id": FORENSICS_ARTIFACT_ID,
        "prior_feed_forensics_receipt_fingerprint": FORENSICS_FP,
        "sample_count": len(records),
        "source_download_bytes": source_download_bytes,
        "max_complete_submission_bytes_each": MAX_COMPLETE_SUBMISSION_BYTES,
        "max_total_download_bytes": MAX_TOTAL_DOWNLOAD_BYTES,
        "max_header_prefix_bytes": MAX_HEADER_PREFIX_BYTES,
        "max_primary_document_block_bytes": MAX_PRIMARY_DOCUMENT_BLOCK_BYTES,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "retry_count": 0,
        "complete_submission_bodies_persisted": False,
        "records": records,
        "interpretation": {
            "diagnostic_only": True,
            "source_vintage_proven": False,
            "historical_first_public_observation_proven": False,
            "frozen_hashes_changed": False,
            "population_changed": False,
            "gate_positive": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
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


def run_capture(
    root: Path,
    request_path: Path,
    forensics_artifact_dir: Path,
    output_dir: Path,
    fetcher: Callable[[str, int, DownloadBudget], dict[str, Any]] = _read_response,
) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise AuditError("OUTPUT_DIRECTORY_NOT_EMPTY")
    output_dir.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc).isoformat()
    result: dict[str, Any] = {
        "status": "NOT_STARTED",
        "generated_at_utc": start,
        "candidate_id": "Q220",
        "request_sequence": REQUEST_SEQUENCE,
        "request_validation_passed": False,
        "source_download_bytes": 0,
        "records": [],
        "gate_positive": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "historical_first_public_observation_proven": False,
        "source_vintage_proven": False,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    try:
        request = read_request(request_path)
        frozen = validate_frozen_inputs(root, forensics_artifact_dir)
        result["request_validation_passed"] = True
        budget = DownloadBudget()
        records: list[dict[str, Any]] = []
        for sample in SAMPLES:
            url = complete_submission_url(sample)
            response = fetcher(url, MAX_COMPLETE_SUBMISSION_BYTES, budget)
            # Test fetchers may supply a body without charging the shared budget.
            if isinstance(response.get("body"), bytes) and response.get("status") == "FETCHED" and response.get("budget_charged") is not True:
                budget.add(len(response["body"]))
            records.append(extract_sample(sample, response, output_dir))
        result["source_download_bytes"] = budget.used
        result["records"] = records
        complete = (
            len(records) == MAX_SAMPLE_COUNT
            and all(r.get("identity_validated") is True and r.get("primary_document_extracted") is True for r in records)
            and budget.used <= MAX_TOTAL_DOWNLOAD_BYTES
        )
        payload = analysis_payload(records, budget.used, frozen)
        result["analysis_payload"] = payload
        result["analysis_fingerprint"] = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))
        result["status"] = "Q220_COMPLETE_SUBMISSION_REPRESENTATION_DIAGNOSTIC_ONLY" if complete else "Q220_COMPLETE_SUBMISSION_REPRESENTATION_INCOMPLETE"
        result["interpretation"] = payload["interpretation"]
        result["safety"] = payload["safety"]
        result["receipt_fingerprint"] = canonical_fingerprint(result)
        out = output_dir / "receipt.json"
        out.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result
    except Exception as exc:
        result.update({
            "status": "Q220_COMPLETE_SUBMISSION_REPRESENTATION_REQUEST_REJECTED",
            "error": f"{type(exc).__name__}:{exc}"[:800],
            "gate_positive": False,
            "source_vintage_proven": False,
            "historical_first_public_observation_proven": False,
        })
        result["receipt_fingerprint"] = canonical_fingerprint(result)
        (output_dir / "receipt.json").write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result


def verify_capture(
    capture_dir: Path,
    output_dir: Path,
    expected_analysis_fingerprint: str,
    repo_root: Path = ROOT,
    forensics_artifact_dir: Path | None = None,
) -> dict[str, Any]:
    if not expected_analysis_fingerprint or not re.fullmatch(r"[0-9a-f]{64}", expected_analysis_fingerprint):
        raise AuditError("EXPECTED_ANALYSIS_FINGERPRINT_INVALID")
    if forensics_artifact_dir is None:
        raise AuditError("PINNED_FORENSICS_ARTIFACT_REQUIRED_FOR_OFFLINE_REPLAY")
    frozen = validate_frozen_inputs(repo_root, forensics_artifact_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise AuditError("VERIFY_OUTPUT_DIRECTORY_NOT_EMPTY")
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt = read_json(find_receipt(capture_dir))
    if (
        receipt.get("candidate_id") != "Q220"
        or receipt.get("status") != "Q220_COMPLETE_SUBMISSION_REPRESENTATION_DIAGNOSTIC_ONLY"
        or receipt.get("request_sequence") != REQUEST_SEQUENCE
        or receipt.get("analysis_fingerprint") != expected_analysis_fingerprint
        or canonical_fingerprint(receipt) != receipt.get("receipt_fingerprint")
    ):
        raise AuditError("CAPTURE_RECEIPT_PIN_OR_STATUS_MISMATCH")
    payload = receipt.get("analysis_payload")
    if not isinstance(payload, dict):
        raise AuditError("CAPTURE_ANALYSIS_PAYLOAD_MISSING")
    calc = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))
    if calc != expected_analysis_fingerprint:
        raise AuditError("ANALYSIS_FINGERPRINT_RECOMPUTE_MISMATCH")
    verified: list[dict[str, Any]] = []
    for sample in SAMPLES:
        record = next((r for r in payload.get("records", []) if r.get("record_key") == sample["record_key"]), None)
        if not isinstance(record, dict):
            raise AuditError("CAPTURE_SAMPLE_MISSING:" + sample["record_key"])
        if record.get("identity_validated") is not True or record.get("primary_document_extracted") is not True:
            raise AuditError("CAPTURE_SAMPLE_NOT_IDENTITY_VALIDATED:" + sample["record_key"])
        header_path = (capture_dir / str(record.get("submission_header_artifact_path") or "")).resolve()
        block_path = (capture_dir / str(record.get("primary_document_block_artifact_path") or "")).resolve()
        if capture_dir.resolve() not in header_path.parents or capture_dir.resolve() not in block_path.parents:
            raise AuditError("CAPTURE_ARTIFACT_PATH_ESCAPES_ROOT")
        header_bytes = header_path.read_bytes()
        block_bytes = block_path.read_bytes()
        if (
            len(header_bytes) != record.get("submission_header_artifact_bytes")
            or sha256(header_bytes) != record.get("submission_header_artifact_sha256")
            or len(block_bytes) != record.get("primary_document_block_artifact_bytes")
            or sha256(block_bytes) != record.get("primary_document_block_artifact_sha256")
        ):
            raise AuditError("CAPTURE_ARTIFACT_BYTE_OR_HASH_MISMATCH:" + sample["record_key"])
        header = forensic.parse_submission_header(header_bytes)
        checks = {
            "accession": header.get("accession") == sample["accession"],
            "filer_cik": header.get("filer_cik") == sample["cik"],
            "form": str(header.get("form") or "").upper() == sample["form"],
            "filed_date": header.get("filed_date_iso") == sample["filed_date"],
            "acceptance_datetime": header.get("acceptance_datetime_iso") == sample["acceptance_datetime"],
        }
        if not all(checks.values()):
            raise AuditError("CAPTURE_HEADER_REPLAY_MISMATCH:" + sample["record_key"])
        primary_info, reproduced_block, raw_text = parse_primary_document_block(header_bytes + b"\n" + block_bytes, sample["primary_filename"])
        if reproduced_block != block_bytes:
            raise AuditError("CAPTURE_PRIMARY_DOCUMENT_BLOCK_REPLAY_MISMATCH:" + sample["record_key"])
        expected_info = record.get("primary_document") or {}
        if (
            primary_info.get("document_block_sha256") != expected_info.get("document_block_sha256")
            or primary_info.get("raw_text_block_sha256") != expected_info.get("raw_text_block_sha256")
            or primary_info.get("raw_text_block_bytes") != expected_info.get("raw_text_block_bytes")
            or primary_info.get("body_hash_variants") != expected_info.get("body_hash_variants")
        ):
            raise AuditError("CAPTURE_TEXT_BODY_REPLAY_MISMATCH:" + sample["record_key"])
        verified.append({
            "record_key": sample["record_key"],
            "submission_header_sha256": sha256(header_bytes),
            "document_block_sha256": sha256(block_bytes),
            "raw_text_block_sha256": sha256(raw_text),
            "raw_text_block_bytes": len(raw_text),
            "replay_status": "PASS",
        })
    proof = {
        "schema_version": 1,
        "record_type": "q220_complete_submission_representation_offline_reproduction",
        "candidate_id": "Q220",
        "status": "Q220_COMPLETE_SUBMISSION_REPRESENTATION_REPRODUCED_OFFLINE",
        "capture_receipt_fingerprint": receipt["receipt_fingerprint"],
        "capture_analysis_fingerprint": expected_analysis_fingerprint,
        "validated_source_population_receipt_fingerprint": POPULATION_FP,
        "validated_compiler_receipt_fingerprint": COMPILER_FP,
        "validated_prior_feed_forensics_receipt_fingerprint": FORENSICS_FP,
        "verified_sample_count": len(verified),
        "samples": verified,
        "network_requests_made": 0,
        "full_submission_text_files_persisted": False,
        "source_vintage_proven": False,
        "historical_first_public_observation_proven": False,
        "gate_positive": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    proof["receipt_fingerprint"] = canonical_fingerprint(proof)
    (output_dir / "verification.json").write_text(json.dumps(proof, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return proof


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("capture", "verify"), required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--request", type=Path, default=None)
    parser.add_argument("--forensics-artifact", type=Path, default=None)
    parser.add_argument("--capture-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-analysis-fingerprint", default=None)
    args = parser.parse_args()
    if args.mode == "capture":
        if os.environ.get("GITHUB_RUN_ATTEMPT", "1") != "1":
            raise AuditError("ONE_SHOT_REQUEST_RERUN_PROHIBITED")
        if args.forensics_artifact is None:
            raise AuditError("PINNED_FORENSICS_ARTIFACT_REQUIRED")
        result = run_capture(
            args.repo_root,
            args.request or (args.repo_root / REQUEST_PATH),
            args.forensics_artifact,
            args.output_dir,
        )
        print(json.dumps({
            "status": result.get("status"),
            "analysis_fingerprint": result.get("analysis_fingerprint"),
            "receipt_fingerprint": result.get("receipt_fingerprint"),
            "source_download_bytes": result.get("source_download_bytes"),
            "successful_samples": sum(bool(r.get("identity_validated") and r.get("primary_document_extracted")) for r in result.get("records", [])),
            "gate_positive": False,
        }, sort_keys=True))
        return 0 if result.get("status") == "Q220_COMPLETE_SUBMISSION_REPRESENTATION_DIAGNOSTIC_ONLY" else 2
    if args.capture_dir is None or args.expected_analysis_fingerprint is None or args.forensics_artifact is None:
        raise AuditError("OFFLINE_CAPTURE_DIR_FORENSICS_ARTIFACT_AND_EXPECTED_FINGERPRINT_REQUIRED")
    result = verify_capture(
        args.capture_dir,
        args.output_dir,
        args.expected_analysis_fingerprint,
        repo_root=args.repo_root,
        forensics_artifact_dir=args.forensics_artifact,
    )
    print(json.dumps({"status": result["status"], "receipt_fingerprint": result["receipt_fingerprint"], "analysis_fingerprint": result["capture_analysis_fingerprint"], "verified_sample_count": result["verified_sample_count"], "network_requests_made": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
