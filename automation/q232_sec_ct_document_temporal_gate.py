"""Q232 R1: deterministic temporal-anchor feasibility on SEC CT ORDER PDFs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from automation.q232_sec_ct_source_census import (
    END,
    START,
    REQUEST_GAP_SECONDS,
    accession_from_filename,
    archive_base,
    fetch,
    fetch_form_index,
    parse_index,
    quarter_list,
    sample_rows,
)
import time

DATE_RE = re.compile(
    r"(?:\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b"
    r"|\b\d{1,2}/\d{1,2}/\d{4}\b"
    r"|\b\d{4}-\d{2}-\d{2}\b)"
    , re.IGNORECASE,
)
STATE_RE = re.compile(r"\b(expire|expires|expiration|extended until|extended through)\b", re.IGNORECASE)
DECISION_RE = re.compile(r"\b(grant|granted|deny|denied|confidential treatment order)\b", re.IGNORECASE)
CT_DOCUMENT_RE = re.compile(
    r"<DOCUMENT>.*?<TYPE>\s*CT ORDER\b.*?<FILENAME>\s*([^\s<]+)",
    re.IGNORECASE | re.DOTALL,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def temporal_anchor_hit(text: str) -> bool:
    compact = normalize(text)
    for match in STATE_RE.finditer(compact):
        left = max(0, match.start() - 500)
        right = min(len(compact), match.end() + 500)
        if DATE_RE.search(compact[left:right]):
            return True
    return False


def extraction_version() -> str:
    proc = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True, check=False)
    raw = (proc.stderr + "\n" + proc.stdout).strip().splitlines()
    return raw[0].strip() if raw else "UNKNOWN"


def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, str]:
    binary = shutil.which("pdftotext")
    if not binary:
        raise RuntimeError("Q232_PDFTOTEXT_MISSING")
    with tempfile.TemporaryDirectory(prefix="q232-r1-") as td:
        pdf = Path(td) / "ct_order.pdf"
        txt = Path(td) / "ct_order.txt"
        pdf.write_bytes(pdf_bytes)
        proc = subprocess.run(
            [binary, "-layout", str(pdf), str(txt)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Q232_PDFTEXT_EXIT_{proc.returncode}:{proc.stderr[-500:]}")
        return txt.read_text(encoding="utf-8", errors="replace"), extraction_version()


def pdf_url_for_row(row: dict[str, str]) -> str:
    cik, accession = archive_base(row["filename"])
    submission_url = (
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{accession}.txt"
    )
    time.sleep(REQUEST_GAP_SECONDS)
    status, body = fetch(submission_url)
    if status != 200:
        raise RuntimeError(f"Q232_R1_SUBMISSION_HTTP_{status}:{accession}")
    complete = body.decode("utf-8", errors="replace")
    match = CT_DOCUMENT_RE.search(complete)
    if not match:
        raise RuntimeError(f"Q232_R1_CT_DOCUMENT_NOT_DECLARED:{accession}")
    document_name = match.group(1).strip()
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{document_name}"


def build_sample() -> list[dict[str, str]]:
    population: list[dict[str, str]] = []
    for year, quarter in quarter_list():
        body, _transport = fetch_form_index(year, quarter)
        population.extend(parse_index(body))
    unique: dict[str, dict[str, str]] = {}
    for row in population:
        accession = accession_from_filename(row["filename"])
        unique[accession] = row
    rows = sorted(unique.values(), key=lambda x: (x["filed_date"], accession_from_filename(x["filename"])))
    return sample_rows(rows)


def run(output: Path) -> dict[str, object]:
    sample = build_sample()
    version = extraction_version()
    observations: list[dict[str, object]] = []
    for row in sample:
        accession = accession_from_filename(row["filename"])
        url = pdf_url_for_row(row)
        time.sleep(REQUEST_GAP_SECONDS)
        status, pdf = fetch(url)
        if status != 200 or not pdf:
            raise RuntimeError(f"Q232_R1_PDF_HTTP_{status}:{accession}")
        text, _ = extract_pdf_text(pdf)
        compact = normalize(text)
        observations.append({
            "accession_number": accession,
            "cik": row["cik"],
            "company_name": row["company_name"],
            "filing_date": row["filed_date"],
            "pdf_url": url,
            "pdf_sha256": sha256_bytes(pdf),
            "text_sha256": sha256_bytes(text.encode("utf-8")),
            "text_characters": len(text),
            "date_token_count": len(DATE_RE.findall(compact)),
            "temporal_anchor_hit": temporal_anchor_hit(compact),
            "decision_anchor_hit": bool(DECISION_RE.search(compact)),
            "status": "PASS",
        })
    temporal_hits = sum(bool(x["temporal_anchor_hit"]) for x in observations)
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-06-232-R1-CT-DOCUMENT-TEMPORAL-ANCHOR",
        "candidate_id": "Q232",
        "status": "Q232_R1_DOCUMENT_TEMPORAL_GATE_COMPLETED",
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "sample_rule": "first/median/last per calendar year",
        "sample_size": len(observations),
        "pdf_retrieved": sum(1 for x in observations if x["status"] == "PASS"),
        "text_extraction_success": sum(1 for x in observations if x["text_characters"] > 0),
        "temporal_anchor_hits": temporal_hits,
        "temporal_anchor_fraction": temporal_hits / len(observations) if observations else 0.0,
        "decision_anchor_hits": sum(bool(x["decision_anchor_hit"]) for x in observations),
        "extraction_tool_version": version,
        "observations": observations,
        "pit_boundary": {
            "document_expiry_date_is_latent_not_public_observation_clock": True,
            "same_day_pit_safe": False,
            "public_observation_time_proven": False,
        },
        "governance": {
            "performance": False, "holdout_selection": False, "ranking": False,
            "parameter_search": False, "threshold_search": False, "horizon_search": False,
            "asset_search": False, "variant_search": False, "promotion": False,
            "performance_authorized": False, "automatic_promotion": False, "live_execution": False,
        },
        "safety": {"PAPER_ONLY":True,"LIVE_TRADING_ENABLED":False,"ORDERS_ENABLED":False,"AUTOMATIC_PROMOTION":False},
    }
    result["receipt_fingerprint"] = sha256_bytes(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.output)
    print(json.dumps({
        "status": result["status"],
        "sample_size": result["sample_size"],
        "pdf_retrieved": result["pdf_retrieved"],
        "text_extraction_success": result["text_extraction_success"],
        "temporal_anchor_hits": result["temporal_anchor_hits"],
        "temporal_anchor_fraction": result["temporal_anchor_fraction"],
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
