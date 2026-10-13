"""Compare one frozen Q220 primary hash against official complete SEC submission text.

This is a bounded, read-only provenance diagnostic. It never changes the frozen
hash population or any PIT/performance gate and never persists downloaded bytes.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlparse

from automation import q220_primary_source_vintage_forensics as forensic

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DEFAULT = ROOT / "research/run_requests/q220_submission_text_provenance.trigger"
SOURCE_DEFAULT = ROOT / "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json"
SINGLE_SUMMARY_DEFAULT = ROOT / "research/evidence/q220_single_feed_boundary_validation_2026_10_13_summary.json"
OUTPUT_DEFAULT = ROOT / "research/runs/q220-submission-text-provenance/latest/receipt.json"

FROZEN = {
    "RUN_Q220_SUBMISSION_TEXT_PROVENANCE": "true",
    "REASON": "COMPARE_FROZEN_Q220_HASH_WITH_COMPLETE_SEC_SUBMISSION_TEXT",
    "SOURCE_RECEIPT_PATH": "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json",
    "SOURCE_RECEIPT_GIT_BLOB_SHA": "2a3abbff6c6950e4f11d85dba92cb9c57a5c7ee0",
    "SOURCE_RECEIPT_FINGERPRINT": "c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075",
    "SOURCE_POPULATION_RECEIPT_FINGERPRINT": "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543",
    "SOURCE_HASH_FAILURE_COUNT": "55",
    "SINGLE_SUMMARY_PATH": "research/evidence/q220_single_feed_boundary_validation_2026_10_13_summary.json",
    "SINGLE_SUMMARY_GIT_BLOB_SHA": "807f6796a0f84b27ab04160e944bdfdaec85525b",
    "SINGLE_SUMMARY_UPSTREAM_RECEIPT_FINGERPRINT": "fe98cecb579d15ecf6e48c3b84a3a699345bf840745e9be0c7cfcd972aebf03a",
    "TARGET_RECORD_KEY": "0000064040|0000064040-19-000059|10-K|2019-02-13",
    "EXPECTED_SHA256": "27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83",
    "EXPECTED_BYTES": "4774458",
    "FROZEN_CAPTURED_SHA256": "08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb",
    "FROZEN_CAPTURED_BYTES": "4774458",
    "SINGLE_FEED_RAW_BODY_SHA256": "aa1f89efdf13029de9dd8f7eb020502dd518d4350513d4ef041ba67d902ef368",
    "SINGLE_FEED_RAW_BODY_BYTES": "4774237",
    "PRIMARY_FILENAME": "spgi-20181231x10k.htm",
    "SUBMISSION_FILENAME": "0000064040-19-000059.txt",
    "FILING_DATE": "2019-02-13",
    "INDEX_PRIMARY_EXPECTED_BYTES": "4774347",
    "INDEX_SUBMISSION_EXPECTED_BYTES": "26429931",
    "MAX_INDEX_PAGE_BYTES": "250000",
    "MAX_SUBMISSION_TEXT_BYTES": "30000000",
    "MAX_CURRENT_PRIMARY_BYTES": "8000000",
    "MAX_EXTRACTED_PRIMARY_BYTES": "8000000",
    "MAX_TOTAL_DOWNLOAD_BYTES": "80000000",
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN) | {"REQUEST_SEQUENCE"}


class BoundedProvenanceError(ValueError):
    """A frozen Q220 source pin or bounded source comparison is invalid."""


def canonical_receipt_fingerprint(receipt: dict[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_fingerprint", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return forensic.sha256(encoded)


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise BoundedProvenanceError(f"REQUEST_LINE_INVALID:{line_number}")
        key, value = line.split("=", 1)
        if key in values:
            raise BoundedProvenanceError(f"REQUEST_DUPLICATE_KEY:{key}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise BoundedProvenanceError("REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN.items():
        if values[key] != expected:
            raise BoundedProvenanceError(f"REQUEST_PIN_MISMATCH:{key}")
    sequence = values["REQUEST_SEQUENCE"]
    if not re.fullmatch(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ", sequence):
        raise BoundedProvenanceError("REQUEST_SEQUENCE_INVALID")
    datetime.fromisoformat(sequence.replace("Z", "+00:00"))
    return values


def _load_pinned_json(path: Path, expected_blob_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    actual_blob_sha = forensic.git_blob_sha1(raw)
    if actual_blob_sha != expected_blob_sha:
        raise BoundedProvenanceError(f"GIT_BLOB_SHA_MISMATCH:{actual_blob_sha}")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise BoundedProvenanceError("PINNED_JSON_NOT_OBJECT")
    return value


def validate_sources(
    source_path: Path,
    summary_path: Path,
    request: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = _load_pinned_json(source_path, request["SOURCE_RECEIPT_GIT_BLOB_SHA"])
    if canonical_receipt_fingerprint(receipt) != request["SOURCE_RECEIPT_FINGERPRINT"]:
        raise BoundedProvenanceError("SOURCE_RECEIPT_FINGERPRINT_MISMATCH")
    if (
        receipt.get("candidate_id") != "Q220"
        or receipt.get("status") != "Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED"
        or receipt.get("gate_positive") is not False
        or receipt.get("source_hash_failure_count") != int(request["SOURCE_HASH_FAILURE_COUNT"])
        or receipt.get("source_population_receipt_fingerprint") != request["SOURCE_POPULATION_RECEIPT_FINGERPRINT"]
    ):
        raise BoundedProvenanceError("SOURCE_RECEIPT_STATE_OR_POPULATION_MISMATCH")
    failures = receipt.get("source_hash_failures")
    if not isinstance(failures, list) or len(failures) != int(request["SOURCE_HASH_FAILURE_COUNT"]):
        raise BoundedProvenanceError("SOURCE_FAILURE_ROWS_MISMATCH")
    key = request["TARGET_RECORD_KEY"]
    matching = [row for row in failures if row.get("record_key") == key]
    if len(matching) != 1:
        raise BoundedProvenanceError("TARGET_FAILURE_ROW_NOT_UNIQUE")
    err = str(matching[0].get("error") or "")
    pins = {
        "expected_sha256": (r"(?:^|:)expected=([0-9a-f]{64})(?:$|:)", "EXPECTED_SHA256"),
        "captured_sha256": (r"(?:^|:)actual=([0-9a-f]{64})(?:$|:)", "FROZEN_CAPTURED_SHA256"),
        "expected_bytes": (r"(?:^|:)expected_bytes=([0-9]+)(?:$|:)", "EXPECTED_BYTES"),
        "captured_bytes": (r"(?:^|:)actual_bytes=([0-9]+)(?:$|:)", "FROZEN_CAPTURED_BYTES"),
        "primary": (r"(?:^|:)primary=([^:]+)(?:$|:)", "PRIMARY_FILENAME"),
    }
    for label, (pattern, request_key) in pins.items():
        match = re.search(pattern, err)
        if not match or match.group(1) != request[request_key]:
            raise BoundedProvenanceError(f"TARGET_FAILURE_PIN_MISMATCH:{label}")

    summary = _load_pinned_json(summary_path, request["SINGLE_SUMMARY_GIT_BLOB_SHA"])
    if (
        summary.get("record_type") != "q220_single_feed_boundary_validation_summary"
        or summary.get("status") != "SINGLE_FEED_BOUNDARY_COMPARISON_COMPLETE"
        or summary.get("upstream_receipt_fingerprint") != request["SINGLE_SUMMARY_UPSTREAM_RECEIPT_FINGERPRINT"]
        or summary.get("source_population_fingerprint") != request["SOURCE_POPULATION_RECEIPT_FINGERPRINT"]
        or summary.get("target_record_key") != key
    ):
        raise BoundedProvenanceError("SINGLE_FEED_SUMMARY_PIN_MISMATCH")
    extraction = summary.get("extraction") or {}
    if (
        extraction.get("raw_text_block_sha256") != request["SINGLE_FEED_RAW_BODY_SHA256"]
        or extraction.get("raw_text_block_bytes") != int(request["SINGLE_FEED_RAW_BODY_BYTES"])
    ):
        raise BoundedProvenanceError("SINGLE_FEED_EXTRACTION_PIN_MISMATCH")
    return receipt, summary


def _metadata(response: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in response.items() if key != "body"}


def _plain_text(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _row_hrefs(row: str) -> list[tuple[str, str]]:
    return [
        (unquote(urlparse(unescape(href.strip())).path.rsplit("/", 1)[-1]), _plain_text(label))
        for href, label in re.findall(
            r"""<a\b[^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""",
            row,
            flags=re.IGNORECASE | re.DOTALL,
        )
    ]


def parse_filing_index(
    body: bytes,
    primary_filename: str,
    submission_filename: str,
) -> dict[str, Any]:
    """Resolve unique primary/submission rows and their official index byte counts."""
    text = body.decode("utf-8", errors="replace")
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", text, flags=re.IGNORECASE | re.DOTALL)
    primary_matches: list[dict[str, Any]] = []
    submission_matches: list[dict[str, Any]] = []
    for row in rows:
        cell_html = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row, flags=re.IGNORECASE | re.DOTALL)
        if not cell_html:
            continue
        cells = [_plain_text(cell) for cell in cell_html]
        row_text = " ".join(cells)
        href_names = {name for name, _label in _row_hrefs(row) if name}
        last_cell = cells[-1]
        size = int(last_cell.replace(",", "")) if re.fullmatch(r"[0-9][0-9,]*", last_cell) else None
        record = {"row_text": row_text[:500], "index_size_bytes": size, "cells": cells[:8]}
        if primary_filename in href_names or any(primary_filename == cell for cell in cells):
            primary_matches.append(record)
        if submission_filename in href_names and "complete submission text file" in row_text.lower():
            submission_matches.append(record)
    return {
        "row_count": len(rows),
        "primary_match_count": len(primary_matches),
        "submission_match_count": len(submission_matches),
        "primary": primary_matches[0] if len(primary_matches) == 1 else None,
        "submission": submission_matches[0] if len(submission_matches) == 1 else None,
        "unique_target_rows": len(primary_matches) == 1 and len(submission_matches) == 1,
    }


def run(
    request_path: Path,
    source_path: Path,
    summary_path: Path,
    output_path: Path,
    fetcher: Callable[..., dict[str, Any]] = forensic._bounded_get_with_retry,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q220_complete_submission_text_provenance",
        "candidate_id": "Q220",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NOT_STARTED",
        "request_validation_passed": False,
        "source_receipt_fingerprint": None,
        "source_population_receipt_fingerprint": None,
        "single_feed_upstream_receipt_fingerprint": None,
        "target_record_key": FROZEN["TARGET_RECORD_KEY"],
        "max_index_page_bytes": int(FROZEN["MAX_INDEX_PAGE_BYTES"]),
        "max_submission_text_bytes": int(FROZEN["MAX_SUBMISSION_TEXT_BYTES"]),
        "max_current_primary_bytes": int(FROZEN["MAX_CURRENT_PRIMARY_BYTES"]),
        "max_total_download_bytes": int(FROZEN["MAX_TOTAL_DOWNLOAD_BYTES"]),
        "source_download_bytes": 0,
        "comparison": None,
        "gate_positive": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "historical_first_public_observation_proven": False,
        "source_vintage_proven": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "next_gate": "A complete submission text comparison is one-accession provenance evidence only; it cannot clear the frozen 55-row Q220 source/PIT gate.",
    }
    try:
        request = read_request(request_path)
        source_receipt, summary = validate_sources(source_path, summary_path, request)
        result.update({
            "request_validation_passed": True,
            "request_sequence": request["REQUEST_SEQUENCE"],
            "source_receipt_fingerprint": source_receipt["receipt_fingerprint"],
            "source_population_receipt_fingerprint": source_receipt["source_population_receipt_fingerprint"],
            "single_feed_upstream_receipt_fingerprint": summary["upstream_receipt_fingerprint"],
            "frozen_expected_sha256": request["EXPECTED_SHA256"],
            "frozen_expected_bytes": int(request["EXPECTED_BYTES"]),
            "frozen_captured_sha256": request["FROZEN_CAPTURED_SHA256"],
            "frozen_captured_bytes": int(request["FROZEN_CAPTURED_BYTES"]),
            "prior_single_feed_body_sha256": request["SINGLE_FEED_RAW_BODY_SHA256"],
            "prior_single_feed_body_bytes": int(request["SINGLE_FEED_RAW_BODY_BYTES"]),
        })
    except Exception as exc:
        result.update({
            "status": "REQUEST_REJECTED",
            "error": f"{type(exc).__name__}: {exc}"[:700],
        })
        forensic._write_receipt(output_path, result)
        return result

    budget = forensic.DownloadBudget(int(request["MAX_TOTAL_DOWNLOAD_BYTES"]))
    cik, accession, form, filing_date = request["TARGET_RECORD_KEY"].split("|")
    accession_dir = accession.replace("-", "")
    root_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_dir}"
    index_url = f"{root_url}/{accession}-index.html"
    submission_url = f"{root_url}/{request['SUBMISSION_FILENAME']}"
    current_url = f"{root_url}/{request['PRIMARY_FILENAME']}"

    try:
        index_response = fetcher(index_url, int(request["MAX_INDEX_PAGE_BYTES"]), budget)
        result["filing_index_response"] = _metadata(index_response)
        if index_response.get("status") != "FETCHED" or index_response.get("http_status") != 200:
            result.update({
                "status": "COMPLETE_SUBMISSION_TEXT_COMPARISON_INCOMPLETE",
                "error": "FILING_INDEX_FETCH_NOT_SUCCESSFUL_OR_OVER_LIMIT",
                "source_download_bytes": budget.used,
            })
            forensic._write_receipt(output_path, result)
            return result

        index = parse_filing_index(index_response["body"], request["PRIMARY_FILENAME"], request["SUBMISSION_FILENAME"])
        index["pinned_primary_size_matches"] = (
            index.get("primary") is not None
            and index["primary"].get("index_size_bytes") == int(request["INDEX_PRIMARY_EXPECTED_BYTES"])
        )
        index["pinned_submission_size_matches"] = (
            index.get("submission") is not None
            and index["submission"].get("index_size_bytes") == int(request["INDEX_SUBMISSION_EXPECTED_BYTES"])
        )
        result["filing_index"] = index

        submission_response = fetcher(submission_url, int(request["MAX_SUBMISSION_TEXT_BYTES"]), budget)
        result["complete_submission_response"] = _metadata(submission_response)
        if submission_response.get("status") != "FETCHED" or submission_response.get("http_status") != 200:
            result.update({
                "status": "COMPLETE_SUBMISSION_TEXT_COMPARISON_INCOMPLETE",
                "error": "COMPLETE_SUBMISSION_TEXT_FETCH_NOT_SUCCESSFUL_OR_OVER_LIMIT",
                "source_download_bytes": budget.used,
            })
            forensic._write_receipt(output_path, result)
            return result

        current_response = fetcher(current_url, int(request["MAX_CURRENT_PRIMARY_BYTES"]), budget)
        result["current_primary_response"] = _metadata(current_response)
        if current_response.get("status") != "FETCHED" or current_response.get("http_status") != 200:
            result.update({
                "status": "COMPLETE_SUBMISSION_TEXT_COMPARISON_INCOMPLETE",
                "error": "CURRENT_PRIMARY_FETCH_NOT_SUCCESSFUL_OR_OVER_LIMIT",
                "source_download_bytes": budget.used,
            })
            forensic._write_receipt(output_path, result)
            return result

        header = forensic.parse_submission_header(submission_response["body"])
        primary = forensic.extract_primary_document(
            submission_response["body"],
            request["PRIMARY_FILENAME"],
            max_primary_bytes=int(request["MAX_EXTRACTED_PRIMARY_BYTES"]),
        )
        header_checks = {
            "accession_matches": header.get("accession") == accession,
            "filer_cik_matches_company_cik": header.get("filer_cik") == cik,
            "form_matches": str(header.get("form") or "").upper() == form,
            "filing_date_matches": header.get("filed_date_iso") == filing_date,
            "exact_primary_filename_extracted": primary.get("found") is True
                and str(primary.get("filename") or "").lower() == request["PRIMARY_FILENAME"].lower(),
        }
        index_valid = (
            index.get("unique_target_rows") is True
            and isinstance((index.get("primary") or {}).get("index_size_bytes"), int)
            and isinstance((index.get("submission") or {}).get("index_size_bytes"), int)
        )
        identity_valid = all(header_checks.values()) and index_valid
        variants = primary.get("body_hash_variants") if primary.get("found") is True else {}
        expected_sha = request["EXPECTED_SHA256"]
        summary_extraction = summary.get("extraction") or {}
        current_sha = current_response.get("response_sha256")
        expected_variant_matches = sorted(
            name for name, info in (variants or {}).items()
            if isinstance(info, dict) and info.get("sha256") == expected_sha
        )
        captured_variant_matches = sorted(
            name for name, info in (variants or {}).items()
            if isinstance(info, dict) and info.get("sha256") == request["FROZEN_CAPTURED_SHA256"]
        )
        prior_feed_variant_matches = sorted(
            name for name, info in (variants or {}).items()
            if isinstance(info, dict) and info.get("sha256") == request["SINGLE_FEED_RAW_BODY_SHA256"]
        )
        comparison_complete = (
            identity_valid
            and index_response.get("status") == "FETCHED"
            and submission_response.get("status") == "FETCHED"
            and current_response.get("status") == "FETCHED"
        )
        result["comparison"] = {
            "filing_index": {
                "response_sha256": index_response.get("response_sha256"),
                "response_bytes": index_response.get("response_bytes"),
                "last_modified": index_response.get("last_modified"),
                "target_rows_unique": index.get("unique_target_rows"),
                "primary_index_size_bytes": (index.get("primary") or {}).get("index_size_bytes"),
                "submission_index_size_bytes": (index.get("submission") or {}).get("index_size_bytes"),
                "primary_pinned_size_matches": index.get("pinned_primary_size_matches"),
                "submission_pinned_size_matches": index.get("pinned_submission_size_matches"),
            },
            "complete_submission_text": {
                "response_bytes": submission_response.get("response_bytes"),
                "response_sha256": submission_response.get("response_sha256"),
                "last_modified": submission_response.get("last_modified"),
                "header": header,
                "header_checks": header_checks,
                "identity_validated": identity_valid,
                "primary": primary,
                "frozen_expected_sha256_match_variants": expected_variant_matches,
                "frozen_captured_sha256_match_variants": captured_variant_matches,
                "prior_single_feed_sha256_match_variants": prior_feed_variant_matches,
                "matches_frozen_expected_bytes": primary.get("raw_text_block_bytes") == int(request["EXPECTED_BYTES"]),
                "matches_frozen_captured_bytes": primary.get("raw_text_block_bytes") == int(request["FROZEN_CAPTURED_BYTES"]),
                "matches_prior_single_feed_body_bytes": primary.get("raw_text_block_bytes") == int(request["SINGLE_FEED_RAW_BODY_BYTES"]),
                "prior_single_feed_body_sha256": summary_extraction.get("raw_text_block_sha256"),
                "prior_single_feed_body_bytes": summary_extraction.get("raw_text_block_bytes"),
            },
            "current_primary": {
                "response_bytes": current_response.get("response_bytes"),
                "response_sha256": current_sha,
                "last_modified": current_response.get("last_modified"),
                "matches_frozen_expected_sha256": current_sha == expected_sha,
                "matches_frozen_captured_sha256": current_sha == request["FROZEN_CAPTURED_SHA256"],
                "matches_prior_single_feed_body_sha256": current_sha == request["SINGLE_FEED_RAW_BODY_SHA256"],
                "matches_filing_index_primary_size": current_response.get("response_bytes") == (index.get("primary") or {}).get("index_size_bytes"),
            },
            "source_download_bytes": budget.used,
            "max_total_download_bytes": int(request["MAX_TOTAL_DOWNLOAD_BYTES"]),
            "meaning": "A complete comparison provides one-accession provenance evidence only. It does not authorize hash replacement, unblock the frozen 55-row compiler, or establish first public observation time.",
        }
        result["status"] = "COMPLETE_SUBMISSION_TEXT_COMPARISON_COMPLETE" if comparison_complete else "COMPLETE_SUBMISSION_TEXT_COMPARISON_INCOMPLETE"
        result["source_download_bytes"] = budget.used
        result["next_gate"] = (
            "Review a complete-submission exact hash match as one accession only; do not amend the frozen 55-row hash set or clear Q220."
            if expected_variant_matches
            else "Compare complete-submission bytes against the pinned compiler extraction provenance; keep all frozen hashes and Q220 gates unchanged."
        )
    except Exception as exc:
        result.update({
            "status": "COMPLETE_SUBMISSION_TEXT_COMPARISON_ERROR",
            "error": f"{type(exc).__name__}: {exc}"[:700],
            "source_download_bytes": budget.used,
        })
    forensic._write_receipt(output_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, default=REQUEST_DEFAULT)
    parser.add_argument("--source-receipt", type=Path, default=SOURCE_DEFAULT)
    parser.add_argument("--single-summary", type=Path, default=SINGLE_SUMMARY_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    receipt = run(args.request, args.source_receipt, args.single_summary, args.output)
    print(json.dumps({
        "candidate_id": receipt.get("candidate_id"),
        "status": receipt.get("status"),
        "request_validation_passed": receipt.get("request_validation_passed"),
        "source_download_bytes": receipt.get("source_download_bytes"),
        "max_total_download_bytes": receipt.get("max_total_download_bytes"),
        "expected_hash_match_count": len(
            ((receipt.get("comparison") or {}).get("complete_submission_text") or {}).get("frozen_expected_sha256_match_variants", [])
        ),
        "gate_positive": False,
        "performance_authorization": False,
        "live_execution": False,
        "receipt_fingerprint": receipt.get("receipt_fingerprint"),
    }, sort_keys=True))
    return 0 if receipt.get("status") == "COMPLETE_SUBMISSION_TEXT_COMPARISON_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
