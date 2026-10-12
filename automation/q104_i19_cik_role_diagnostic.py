"""Read-only, pinned Q104:I19 CIK-role lineage diagnostic for one frozen 13F accession.

This diagnostic separates the bulk archive's CIK field, accession-prefix CIK,
EDGAR filing-header CIK and CIK values embedded in the filed document. It never
reinterprets one namespace as another or changes the candidate's identity gates.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import xml.etree.ElementTree as ET

from automation import q104_i19_13f_historical_identity_census as census
from automation.q104_i19_residual_source_lineage_diagnostic import (
    DownloadBudget,
    fetch_bounded,
    parse_header_observation,
    sha256,
)
from automation.q104_i19_13f_historical_identity_census_merge import canonical_fingerprint

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN_ID = "38168441086"
SOURCE_SHARD = "2024-2025-09"
SOURCE_SHARD_RECEIPT_FINGERPRINT = "2500f2ee3f07258a9525cd6e7018fd67f380cf0244028c5948866d55c835794e"
SOURCE_PAGE_SHA256 = "b2c4083c3615ce6646764d8e80dc18c2f5484a25c417281be580bdc650817b46"
ACCESSION = "0001493152-24-018939"
EXPECTED_FAILURE = "FILER_CIK_MISMATCH"
ARCHIVE_URL = "https://www.sec.gov/files/structureddata/data/form-13f-data-sets/01mar2024-31may2024_form13f.zip"
ARCHIVE_SHA256 = "fe723ad7d3e58f7e5f0bb3d5e46158c4c3bacc8a23a69b2d6eef3c97782d5cf8"
ARCHIVE_BYTES = 78_174_865
MAX_SOURCE_ARCHIVE_BYTES = 90_000_000
MAX_HEADER_RESPONSE_BYTES = 262_144
MAX_FULL_SUBMISSION_BYTES = 1_000_000
MAX_TOTAL_DOWNLOAD_BYTES = 150_000_000
REQUEST_GAP_SECONDS = 1.0
USER_AGENT = census.UA
# Both CIKs were independently visible in official SEC filing-index / submission
# results for this accession. They are route candidates only, not asserted roles.
OBSERVED_SEC_CIK_CANDIDATES = ("0002094379", "0001960050")
DEFAULT_REQUEST_PATH = ROOT / "research/run_requests/q104_i19_cik_role_diagnostic.trigger"
DEFAULT_RECEIPT_PATH = ROOT / "research/evidence/q104_i19_cik_role_diagnostic_latest.json"

FROZEN_REQUEST_VALUES = {
    "RUN_Q104_I19_CIK_ROLE_DIAGNOSTIC": "true",
    "REASON": "READ_ONLY_RECONCILE_ONE_FROZEN_CIK_MISMATCH_ACROSS_SEC_SOURCE_NAMESPACES",
    "SOURCE_RUN_ID": SOURCE_RUN_ID,
    "SOURCE_SHARD": SOURCE_SHARD,
    "SOURCE_SHARD_RECEIPT_FINGERPRINT": SOURCE_SHARD_RECEIPT_FINGERPRINT,
    "SOURCE_PAGE_SHA256": SOURCE_PAGE_SHA256,
    "ACCESSION": ACCESSION,
    "EXPECTED_FAILURE": EXPECTED_FAILURE,
    "ARCHIVE_URL": ARCHIVE_URL,
    "ARCHIVE_SHA256": ARCHIVE_SHA256,
    "ARCHIVE_BYTES": str(ARCHIVE_BYTES),
    "MAX_SOURCE_ARCHIVE_BYTES": str(MAX_SOURCE_ARCHIVE_BYTES),
    "MAX_HEADER_RESPONSE_BYTES": str(MAX_HEADER_RESPONSE_BYTES),
    "MAX_FULL_SUBMISSION_BYTES": str(MAX_FULL_SUBMISSION_BYTES),
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
OBSERVATION_STATUSES = {"FETCHED", "FETCHED_PREFIX", "HTTP_ERROR"}


class DiagnosticError(ValueError):
    """A frozen input or bounded CIK-role observation did not validate."""


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise DiagnosticError(f"Q104_CIK_ROLE_REQUEST_INVALID_LINE:{number}")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value or key in values:
            raise DiagnosticError(f"Q104_CIK_ROLE_REQUEST_INVALID_KEY_VALUE:{number}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise DiagnosticError("Q104_CIK_ROLE_REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise DiagnosticError("Q104_CIK_ROLE_REQUEST_VALUE_MISMATCH:" + key)
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise DiagnosticError("Q104_CIK_ROLE_REQUEST_SEQUENCE_INVALID")
    return values


def validate_frozen_shard_receipt(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not path.is_file():
        raise DiagnosticError("Q104_CIK_ROLE_SOURCE_SHARD_RECEIPT_MISSING")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    fingerprint = receipt.get("receipt_fingerprint")
    if fingerprint != SOURCE_SHARD_RECEIPT_FINGERPRINT:
        raise DiagnosticError("Q104_CIK_ROLE_SOURCE_SHARD_RECEIPT_FINGERPRINT_MISMATCH")
    if canonical_fingerprint(receipt) != fingerprint:
        raise DiagnosticError("Q104_CIK_ROLE_SOURCE_SHARD_RECEIPT_CANONICAL_FINGERPRINT_MISMATCH")
    if (
        receipt.get("shard") != SOURCE_SHARD
        or receipt.get("source_page_sha256") != SOURCE_PAGE_SHA256
        or receipt.get("task_id") != "Q-2026-10-06-104-I19-13F-HISTORICAL-ID-CENSUS-2024-2025-09"
    ):
        raise DiagnosticError("Q104_CIK_ROLE_SOURCE_SHARD_RECEIPT_IDENTITY_MISMATCH")
    matching = [
        item for item in receipt.get("archives", [])
        if isinstance(item, dict) and item.get("archive", {}).get("url") == ARCHIVE_URL
    ]
    if len(matching) != 1:
        raise DiagnosticError("Q104_CIK_ROLE_PINNED_ARCHIVE_RECEIPT_ROW_COUNT_INVALID")
    item = matching[0]
    if (
        item.get("archive_sha256") != ARCHIVE_SHA256
        or item.get("archive_bytes") != ARCHIVE_BYTES
        or item.get("acceptance_failures", {}).get(ACCESSION) != EXPECTED_FAILURE
    ):
        raise DiagnosticError("Q104_CIK_ROLE_PINNED_ARCHIVE_RECEIPT_FIELDS_MISMATCH")
    return receipt, item


def read_exact_submission_row(archive_body: bytes, accession: str = ACCESSION) -> dict[str, str]:
    """Read the unique frozen SUBMISSION.tsv row without substituting CIK namespaces."""
    try:
        with zipfile.ZipFile(__import__("io").BytesIO(archive_body)) as zf:
            rows = [
                row for row in census.tsv(zf, "submission.tsv")
                if census.field(row, "ACCESSION_NUMBER").strip() == accession
            ]
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        raise DiagnosticError(f"Q104_CIK_ROLE_PINNED_ARCHIVE_ZIP_INVALID:{type(exc).__name__}") from exc
    if len(rows) != 1:
        raise DiagnosticError(f"Q104_CIK_ROLE_SOURCE_ROW_COUNT_INVALID:{len(rows)}")
    row = rows[0]
    raw_cik = census.field(row, "CIK").strip()
    if not re.fullmatch(r"\d{1,10}", raw_cik):
        raise DiagnosticError("Q104_CIK_ROLE_SOURCE_ROW_CIK_INVALID")
    form = census.field(row, "SUBMISSIONTYPE").strip()
    raw_date = census.field(row, "FILING_DATE").strip()
    if not form or not raw_date:
        raise DiagnosticError("Q104_CIK_ROLE_SOURCE_ROW_IDENTITY_FIELDS_MISSING")
    try:
        normalized_date = census.parse_date(raw_date).isoformat()
    except ValueError as exc:
        raise DiagnosticError("Q104_CIK_ROLE_SOURCE_ROW_FILING_DATE_INVALID") from exc
    normalized_cik = raw_cik.zfill(10)
    return {
        "accession": accession,
        "source_cik_raw": raw_cik,
        "source_cik_normalized": normalized_cik,
        "form": form,
        "filing_date_raw": raw_date,
        "filing_date_iso": normalized_date,
        "period_of_report": census.field(row, "PERIODOFREPORT").strip(),
    }


def build_cik_candidates(source_cik: str, accession: str = ACCESSION) -> list[dict[str, str]]:
    """Return distinct route candidates while preserving each observed CIK's sources."""
    raw_candidates = [
        ("submission_tsv_cik", str(source_cik).zfill(10)),
        ("accession_prefix_cik", accession.split("-", 1)[0].zfill(10)),
        ("official_sec_result_candidate", OBSERVED_SEC_CIK_CANDIDATES[0]),
        ("official_sec_result_candidate", OBSERVED_SEC_CIK_CANDIDATES[1]),
    ]
    grouped: dict[str, list[str]] = {}
    for role_hint, cik in raw_candidates:
        if not re.fullmatch(r"\d{10}", cik):
            raise DiagnosticError("Q104_CIK_ROLE_CIK_CANDIDATE_INVALID")
        grouped.setdefault(cik, [])
        if role_hint not in grouped[cik]:
            grouped[cik].append(role_hint)
    return [{"cik": cik, "observed_sources": sources} for cik, sources in grouped.items()]


def extract_embedded_cik_observations(submission_body: bytes) -> list[dict[str, str]]:
    """Extract XML CIK values with element paths; do not assign legal/data roles."""
    observations: list[dict[str, str]] = []
    documents = re.finditer(rb"<DOCUMENT\b[^>]*>(.*?)</DOCUMENT>", submission_body, re.I | re.S)
    for doc_index, match in enumerate(documents, start=1):
        block = match.group(1)
        type_match = re.search(rb"<TYPE>\s*([^\r\n<]+)", block, re.I)
        filename_match = re.search(rb"<FILENAME>\s*([^\r\n<]+)", block, re.I)
        text_match = re.search(rb"<TEXT>(.*?)</TEXT>", block, re.I | re.S)
        doc_type = type_match.group(1).decode("ascii", "replace").strip() if type_match else ""
        filename = filename_match.group(1).decode("utf-8", "replace").strip() if filename_match else ""
        if not text_match:
            continue
        payload = text_match.group(1).strip()
        if not payload.startswith(b"<"):
            continue
        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            continue

        def walk(node: ET.Element, path: str) -> None:
            local = str(node.tag).split("}")[-1].split(":")[-1]
            next_path = f"{path}/{local}"
            if local.casefold() in {"cik", "centralindexkey", "centralindexkeynumber"}:
                value = (node.text or "").strip()
                if re.fullmatch(r"\d{1,10}", value):
                    observations.append({
                        "document_index": str(doc_index),
                        "document_type": doc_type,
                        "filename": filename,
                        "element_path": next_path,
                        "value_raw": value,
                        "value_normalized": value.zfill(10),
                    })
            for child in list(node):
                walk(child, next_path)

        walk(root, "")
    return observations


def parse_header_routes(cik: str, budget: DownloadBudget, fetcher: Callable[..., dict[str, Any]]) -> list[dict[str, Any]]:
    accession_compact = ACCESSION.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_compact}"
    routes = (
        ("index_headers", f"{base}/{ACCESSION}-index-headers.html", None),
        ("raw_sgml_header", f"{base}/{ACCESSION}.hdr.sgml", None),
        ("complete_submission_header_prefix", f"{base}/{ACCESSION}.txt", b"</SEC-HEADER>"),
    )
    output: list[dict[str, Any]] = []
    for route_name, url, marker in routes:
        result = fetcher(url, budget, max_bytes=MAX_HEADER_RESPONSE_BYTES, prefix_marker=marker)
        raw = result.pop("_body", b"")
        probe: dict[str, Any] = {
            **result,
            "route": route_name,
            "candidate_cik_path": cik,
            "requested_url": url,
            "response_sha256": result.get("response_sha256"),
            "observed_identity": None,
        }
        if raw and result.get("status") in {"FETCHED", "FETCHED_PREFIX"}:
            probe["observed_identity"] = parse_header_observation(raw, route_name)
        output.append(probe)
    return output


def diagnostic_result(
    request: dict[str, str],
    source_row: dict[str, str],
    header_probes: list[dict[str, Any]],
    full_submission: dict[str, Any],
) -> dict[str, Any]:
    identity_observations = [
        p["observed_identity"] for p in header_probes
        if isinstance(p.get("observed_identity"), dict)
        and p["observed_identity"].get("accession") == ACCESSION
        and str(p["observed_identity"].get("form") or "").upper() == source_row["form"].upper()
        and p["observed_identity"].get("filer_cik")
    ]
    observed_header_ciks = sorted({str(x["filer_cik"]).zfill(10) for x in identity_observations})
    header_cik_consensus = observed_header_ciks[0] if len(observed_header_ciks) == 1 and identity_observations else None
    embedded = full_submission.get("embedded_cik_observations", [])
    embedded_ciks = sorted({str(x.get("value_normalized")) for x in embedded if x.get("value_normalized")})
    route_outcomes_complete = all(p.get("status") in OBSERVATION_STATUSES for p in header_probes)
    full_ok = full_submission.get("status") == "FETCHED" and full_submission.get("complete_submission_captured") is True
    diagnostic_complete = bool(
        header_probes
        and route_outcomes_complete
        and full_ok
        and identity_observations
        and header_cik_consensus
    )
    source_cik = source_row["source_cik_normalized"]
    prefix_cik = ACCESSION.split("-", 1)[0].zfill(10)
    return {
        "record_type": "q104_i19_cik_role_lineage_diagnostic",
        "candidate_id": "Q104:I19",
        "status": "CIK_ROLE_LINEAGE_OBSERVED_GATE_UNRESOLVED" if diagnostic_complete else "CIK_ROLE_DIAGNOSTIC_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "request_sequence": request["REQUEST_SEQUENCE"],
        "source_run_id": SOURCE_RUN_ID,
        "source_shard": SOURCE_SHARD,
        "source_shard_receipt_fingerprint": SOURCE_SHARD_RECEIPT_FINGERPRINT,
        "source_archive_url": ARCHIVE_URL,
        "source_archive_sha256": ARCHIVE_SHA256,
        "source_archive_bytes": ARCHIVE_BYTES,
        "sample": {
            **source_row,
            "accession_prefix_cik": prefix_cik,
            "expected_frozen_failure": EXPECTED_FAILURE,
            "candidate_ciks": build_cik_candidates(source_cik),
            "header_probes": header_probes,
            "observed_header_filer_ciks": observed_header_ciks,
            "header_filer_cik_consensus": header_cik_consensus,
            "source_cik_matches_header_filer_cik": (
                source_cik == header_cik_consensus if header_cik_consensus else None
            ),
            "accession_prefix_cik_matches_header_filer_cik": (
                prefix_cik == header_cik_consensus if header_cik_consensus else None
            ),
            "embedded_document_cik_observations": embedded,
            "embedded_document_cik_values": embedded_ciks,
            "source_cik_appears_in_embedded_document": source_cik in embedded_ciks,
            "header_filer_cik_appears_in_embedded_document": (
                header_cik_consensus in embedded_ciks if header_cik_consensus else None
            ),
        },
        "full_submission": full_submission,
        "research_boundary": {
            "identity_discrepancy_resolved": False,
            "candidate_identity_gate_cleared": False,
            "acceptance_time_gate_cleared": False,
            "historical_pit_gate_cleared": False,
            "frozen_population_changed": False,
            "next_action": (
                "review the field-role trace and decide whether a separate source-field contract is justified; do not rewrite the frozen CIK equality rule from this single sample"
                if diagnostic_complete
                else "repair or repeat only the incomplete bounded observation; retain all frozen identity gates"
            ),
        },
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def run_diagnostic(
    request_path: Path,
    shard_receipt_path: Path,
    output_path: Path,
    *,
    fetcher: Callable[..., dict[str, Any]] = fetch_bounded,
) -> dict[str, Any]:
    request = read_request(request_path)
    _, shard_archive = validate_frozen_shard_receipt(shard_receipt_path)
    budget = DownloadBudget(MAX_TOTAL_DOWNLOAD_BYTES)
    archive_result = fetcher(ARCHIVE_URL, budget, max_bytes=MAX_SOURCE_ARCHIVE_BYTES)
    archive_body = archive_result.pop("_body", b"")
    observed_archive_sha = sha256(archive_body) if archive_body else None
    archive_verified = (
        archive_result.get("status") == "FETCHED"
        and archive_result.get("http_status") == 200
        and len(archive_body) == ARCHIVE_BYTES
        and observed_archive_sha == ARCHIVE_SHA256
        and shard_archive.get("archive_sha256") == observed_archive_sha
        and shard_archive.get("archive_bytes") == len(archive_body)
    )
    archive_observation = {
        "url": ARCHIVE_URL,
        "http": archive_result,
        "expected_sha256": ARCHIVE_SHA256,
        "observed_sha256": observed_archive_sha,
        "expected_bytes": ARCHIVE_BYTES,
        "observed_bytes": len(archive_body),
        "byte_identity_verified": archive_verified,
        "source_receipt_pin_agrees": (
            shard_archive.get("archive_sha256") == ARCHIVE_SHA256
            and shard_archive.get("archive_bytes") == ARCHIVE_BYTES
        ),
    }
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q104_i19_cik_role_lineage_diagnostic",
        "candidate_id": "Q104:I19",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "request_sequence": request["REQUEST_SEQUENCE"],
        "source_run_id": SOURCE_RUN_ID,
        "source_shard_receipt_fingerprint": SOURCE_SHARD_RECEIPT_FINGERPRINT,
        "archive_observation": archive_observation,
        "status": "CIK_ROLE_DIAGNOSTIC_INCOMPLETE",
        "download_budget_bytes": MAX_TOTAL_DOWNLOAD_BYTES,
        "source_download_bytes": budget.used,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    if archive_verified:
        source_row = read_exact_submission_row(archive_body)
        candidates = build_cik_candidates(source_row["source_cik_normalized"])
        all_probes: list[dict[str, Any]] = []
        for candidate in candidates:
            all_probes.extend(parse_header_routes(candidate["cik"], budget, fetcher))

        valid_header_ciks = sorted({
            str(p["observed_identity"]["filer_cik"]).zfill(10)
            for p in all_probes
            if isinstance(p.get("observed_identity"), dict)
            and p["observed_identity"].get("accession") == ACCESSION
            and str(p["observed_identity"].get("form") or "").upper() == source_row["form"].upper()
            and p["observed_identity"].get("filer_cik")
        })
        full_submission: dict[str, Any] = {
            "requested_url": None,
            "status": "NOT_REQUESTED_NO_VALID_HEADER_FILER_CIK",
            "http_status": None,
            "response_bytes": 0,
            "response_sha256": None,
            "complete_submission_captured": False,
            "embedded_cik_observations": [],
        }
        if len(valid_header_ciks) == 1:
            cik = valid_header_ciks[0]
            url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                f"{ACCESSION.replace('-', '')}/{ACCESSION}.txt"
            )
            result = fetcher(url, budget, max_bytes=MAX_FULL_SUBMISSION_BYTES)
            raw = result.pop("_body", b"")
            full_submission = {
                **result,
                "requested_url": url,
                "complete_submission_captured": result.get("status") == "FETCHED" and bool(raw),
                "embedded_cik_observations": extract_embedded_cik_observations(raw) if raw else [],
            }
        receipt.update(diagnostic_result(request, source_row, all_probes, full_submission))
        receipt["archive_observation"] = archive_observation
        receipt["source_download_bytes"] = budget.used
        receipt["header_probe_count"] = len(all_probes)
    unsigned = dict(receipt)
    unsigned.pop("receipt_fingerprint", None)
    receipt["receipt_fingerprint"] = sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST_PATH)
    parser.add_argument("--input-shard-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_RECEIPT_PATH)
    args = parser.parse_args()
    try:
        result = run_diagnostic(args.request, args.input_shard_receipt, args.output)
    except Exception as exc:
        print(json.dumps({
            "record_type": "q104_i19_cik_role_lineage_diagnostic",
            "status": "CIK_ROLE_DIAGNOSTIC_INPUT_OR_EXECUTION_ERROR",
            "error": f"{type(exc).__name__}:{exc}"[:500],
            "gate_positive": False,
            "live_execution": False,
        }, sort_keys=True))
        return 2
    print(json.dumps({
        "record_type": result["record_type"],
        "status": result["status"],
        "receipt_fingerprint": result["receipt_fingerprint"],
        "source_download_bytes": result.get("source_download_bytes", 0),
        "header_probe_count": result.get("header_probe_count", 0),
        "scientific_evidence": False,
        "live_execution": False,
    }, sort_keys=True))
    return 0 if result["status"] == "CIK_ROLE_LINEAGE_OBSERVED_GATE_UNRESOLVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
