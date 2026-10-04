"""Q179-Q184 historical PIT census R2.

Discovery/PIT only. Uses fixed public URLs and bounded archive samples to determine
historical-addressability and clock prerequisites. It never reads returns or
selects candidates/assets/parameters and never authorizes performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from pypdf import PdfReader


UA = "trading-agent-public/Q179-Q184-PIT-census-R2/1"


def fetch(url: str, *, headers: dict[str, str] | None = None, limit: int | None = 2_000_000) -> tuple[int, dict[str, str], bytes]:
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            data = response.read() if limit is None else response.read(limit)
            return int(getattr(response, "status", 200)), {k.lower(): v for k, v in response.headers.items()}, data
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(limit or 2_000_000)
        except Exception:
            body = b""
        return int(exc.code), {k.lower(): v for k, v in exc.headers.items()}, body
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, {}, f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def html_probe(url: str, markers: list[str]) -> dict[str, Any]:
    status, headers, body = fetch(url, limit=1_000_000)
    text = body.decode("utf-8", errors="replace")
    missing = [m for m in markers if m.lower() not in text.lower()]
    return {
        "url": url,
        "http_status": status,
        "markers_present": status == 200 and not missing,
        "missing_markers": missing,
        "content_sha256": sha(body),
        "content_length_header": headers.get("content-length"),
        "last_modified_header": headers.get("last-modified"),
    }


def archive_range_probe(url: str, *, expected_magic: bytes = b"PK") -> dict[str, Any]:
    status, headers, body = fetch(
        url, headers={"Range": "bytes=0-63", "Accept": "application/zip,application/octet-stream,*/*"}, limit=512
    )
    return {
        "url": url,
        "http_status": status,
        "range_status_accepted": status in (200, 206),
        "content_length_header": headers.get("content-length"),
        "content_range": headers.get("content-range"),
        "accept_ranges": headers.get("accept-ranges"),
        "zip_magic_present": body.startswith(expected_magic),
        "body_prefix_sha256": sha(body),
        "body_bytes": len(body),
        "content_type": headers.get("content-type"),
    }


def pdf_text_probe(url: str, markers: list[str]) -> dict[str, Any]:
    status, headers, body = fetch(
        url,
        headers={"Accept": "application/pdf,*/*"},
        limit=2_000_000,
    )
    text = ""
    extraction_error = None
    if status == 200:
        try:
            reader = PdfReader(__import__("io").BytesIO(body))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:
            extraction_error = f"{type(exc).__name__}:{exc}"
    missing = [m for m in markers if m.lower() not in text.lower()]
    return {
        "url": url,
        "http_status": status,
        "markers_present": status == 200 and not missing,
        "missing_markers": missing,
        "content_sha256": sha(body),
        "content_type": headers.get("content-type"),
        "pdf_pages": len(PdfReader(__import__("io").BytesIO(body)).pages) if status == 200 and not extraction_error else None,
        "extraction_error": extraction_error,
    }


def clinical_history_probe() -> dict[str, Any]:
    fixed = [
        "https://clinicaltrials.gov/study/NCT02520245?tab=history",
        "https://clinicaltrials.gov/study/NCT00148746?tab=history",
        "https://clinicaltrials.gov/study/NCT02530307?tab=history",
    ]
    studies = []
    for url in fixed:
        status, _, body = fetch(url, limit=1_200_000)
        text = body.decode("utf-8", errors="replace")
        versions = re.findall(r">\s*(\d+)\s*</(?:td|a)>\s*<", text)
        dates = sorted(set(re.findall(r"20\d{2}-\d{2}-\d{2}", text)))
        studies.append(
            {
                "url": url,
                "http_status": status,
                "version_tokens_found": sorted(set(versions), key=int),
                "submitted_date_tokens": dates[:20],
                "archive_sample_reconstructable": status == 200 and bool(dates),
                "content_sha256": sha(body),
            }
        )
    return {
        "studies": studies,
        "all_samples_reachable": all(x["http_status"] == 200 for x in studies),
        "historical_version_tokens_seen": all(x["archive_sample_reconstructable"] for x in studies),
        "pit_caveat": "Record history exposes submitted-date versions; this does not by itself prove exact intraday public-availability time."
    }


def q180_probe() -> dict[str, Any]:
    docs = html_probe(
        "https://www.nhtsa.gov/nhtsa-datasets-and-apis",
        [
            "FLAT_RCL_POST_2010.zip",
            "RCL_FROM_2020_2024.zip",
            "RCL_FROM_2025_2026.zip",
            "published",
        ],
    )
    archives = [
        archive_range_probe("https://static.nhtsa.gov/odi/ffdd/rcl/RCL_FROM_2020_2024.zip"),
        archive_range_probe("https://static.nhtsa.gov/odi/ffdd/rcl/RCL_FROM_2025_2026.zip"),
    ]
    return {
        "documentation": docs,
        "historical_archive_samples": archives,
        "archive_sample_reconstructable": all(x["zip_magic_present"] for x in archives),
        "pit_caveat": "Current archives are historical data containers, not immutable snapshots of what NHTSA had published on each past trading day; publication/revision lineage remains required.",
    }


def q181_probe() -> dict[str, Any]:
    docs = html_probe(
        "https://catalog.data.gov/dataset/dol-enforcement-data-inspection",
        ["accessLevel", "public", "accrualPeriodicity", "R/P1D"],
    )
    return {
        "documentation": docs,
        "daily_publication_contract_seen": docs["markers_present"],
        "historical_archive_reconstructable": False,
        "pit_caveat": "Public daily accrual does not prove an intraday first-public-observation clock or an immutable historical refresh prefix.",
    }


def q182_probe() -> dict[str, Any]:
    probes = [
        html_probe("https://ferc.gov/what-elibrary", ["issued by FERC", "Documents received and issued by FERC"]),
        html_probe("https://www.ferc.gov/about/what-ferc/frequently-asked-questions-faqs/documents-and-filing/elibrary", ["Documents received and issued by FERC"]),
    ]
    return {
        "probes": probes,
        "access_blocked": any(x["http_status"] in (401, 403) for x in probes),
        "historical_archive_reconstructable": False,
        "pit_caveat": "No extraction is attempted while the official route is access-blocked in the current runner.",
    }


def q183_probe() -> dict[str, Any]:
    docs = html_probe(
        "https://www.ntsb.gov/safety/data/Pages/Data_Stats.aspx",
        ["PRE1982.zip", "avall.zip", "daily and pending aviation publication report"],
    )
    directory = html_probe("https://data.ntsb.gov/avdata", ["avall.zip", "up01OCT.zip", "up22SEP.zip"])
    archive = archive_range_probe(
        "https://data.ntsb.gov/avdata/FileDirectory/DownloadFile?fileID=C%3A%5Cavdata%5Cavall.zip"
    )
    return {
        "documentation": docs,
        "download_directory": directory,
        "historical_archive_sample": archive,
        "archive_sample_reconstructable": archive["zip_magic_present"],
        "pit_caveat": "The current avall archive is historically broad and the publication report exists, but exact historical publication-state lineage must still be reconstructed for candidate use.",
    }


def q184_probe() -> dict[str, Any]:
    docs = html_probe(
        "https://opendata.fcc.gov/Wireless/FCC-Universal-Licensing-System-ULS-/x28i-i4z4",
        ["daily transaction files", "weekly transaction files", "Public Domain"],
    )
    legacy = pdf_text_probe(
        "https://wireless.fcc.gov/uls/releases/da992205.pdf",
        ["daily transaction files", "5:00 am eastern time", "previous day"],
    )
    return {
        "documentation": docs,
        "clock_notice": legacy,
        "daily_transaction_semantics_proven": docs["markers_present"] and legacy["markers_present"],
        "historical_archive_reconstructable": False,
        "pit_caveat": "The documented daily-file convention gives a strong public dissemination clock, but candidate-specific historical transaction lineage and issuer mapping still require a frozen sample/replay.",
    }


def run(output: Path) -> dict[str, Any]:
    q179 = clinical_history_probe()
    q180 = q180_probe()
    q181 = q181_probe()
    q182 = q182_probe()
    q183 = q183_probe()
    q184 = q184_probe()

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "receipt_type": "q179_q184_pit_census_r2",
        "wave_id": "Q179-Q184-PIT-CENSUS-R2-2026-10-04",
        "status": "PIT_HISTORICAL_CENSUS_COMPLETED_NO_PERFORMANCE",
        "candidate_results": {
            "Q179": {
                "status": "ARCHIVE_SAMPLE_RECONSTRUCTABLE_CLOCK_UNRESOLVED"
                if q179["historical_version_tokens_seen"]
                else "ARCHIVE_SAMPLE_UNRESOLVED",
                "details": q179,
                "next_gate": "prove public-availability boundary and frozen sponsor-to-issuer mapping",
            },
            "Q180": {
                "status": "HISTORICAL_ARCHIVE_SAMPLE_RECONSTRUCTABLE_CLOCK_AND_REVISION_PENDING"
                if q180["archive_sample_reconstructable"]
                else "ARCHIVE_SAMPLE_UNRESOLVED",
                "details": q180,
                "next_gate": "reconstruct fixed historical publication states and revision lineage; then freeze issuer mapping",
            },
            "Q181": {
                "status": "PUBLIC_DAILY_DATA_CLOCK_ONLY",
                "details": q181,
                "next_gate": "historical refresh archive + intraday/public-boundary proof + issuer mapping",
            },
            "Q182": {
                "status": "RUNNER_ACCESS_BLOCKED",
                "details": q182,
                "next_gate": "independent accessible official route; do not retry blocked route blindly",
            },
            "Q183": {
                "status": "HISTORICAL_ARCHIVE_SAMPLE_RECONSTRUCTABLE_PUBLICATION_LINEAGE_PENDING"
                if q183["archive_sample_reconstructable"]
                else "ARCHIVE_SAMPLE_UNRESOLVED",
                "details": q183,
                "next_gate": "candidate-specific publication-state replay + fixed operator/issuer mapping",
            },
            "Q184": {
                "status": "PUBLIC_DAILY_DISSEMINATION_CLOCK_CONFIRMED_ARCHIVE_REPLAY_PENDING"
                if q184["daily_transaction_semantics_proven"]
                else "CLOCK_PROBE_UNRESOLVED",
                "details": q184,
                "next_gate": "freeze historical daily transaction sample and reconstruct amendment lineage + issuer mapping",
            },
        },
        "cross_wave_checks": {
            "performance_evaluated": False,
            "holdout_used": False,
            "candidate_ranked_by_returns": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "PAPER_ONLY": True,
            "LIVE_TRADING_ENABLED": False,
            "ORDERS_ENABLED": False,
            "AUTOMATIC_PROMOTION": False,
        },
    }
    result["receipt_fingerprint"] = sha(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output)
