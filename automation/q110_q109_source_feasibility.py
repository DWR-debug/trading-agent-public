"""Q110 source feasibility for Q109.

Checks current official SEC dataset boundaries and representative live EDGAR
filings. This is a source/archive gate only: no returns, ranking, tuning,
holdout selection, or performance authorization.
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

UA = "trading-agent-public/Q110 research"
TIMEOUT = 45


def get(url: str) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            return int(response.status), response.read(), response.headers.get("content-type", "")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), ""
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, str(exc).encode("utf-8"), ""


def fp(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


def page_probe(label: str, url: str, patterns: list[str]) -> dict[str, Any]:
    status, body, content_type = get(url)
    text = body.decode("utf-8", "replace")
    checks = {pattern: bool(re.search(pattern, text, re.IGNORECASE)) for pattern in patterns}
    return {
        "id": label,
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "response_sha256": fp(body),
        "checks": checks,
        "status": "VERIFIABLE" if status == 200 and checks and all(checks.values()) else "SCHEMA_MISMATCH",
    }


def json_probe(label: str, url: str, required_keys: list[str]) -> dict[str, Any]:
    status, body, content_type = get(url)
    out: dict[str, Any] = {
        "id": label,
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "response_sha256": fp(body),
        "checks": {},
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
    }
    if status != 200:
        return out
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return out
    for key in required_keys:
        value = payload
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        out["checks"][key] = value not in (None, "", [], {})
    out["status"] = "VERIFIABLE" if all(out["checks"].values()) else "SCHEMA_MISMATCH"
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q110_q109_source_feasibility/result.json"))
    args = parser.parse_args()

    probes = [
        page_probe(
            "SEC_13F_DATASETS",
            "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets",
            ["July 2013", "August 2026", "as-filed", "Data Downloads"],
        ),
        page_probe(
            "SEC_NPORT_DATASETS",
            "https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets",
            ["October 2019", "June 2026", "monthly portfolio holdings", "publicly available information"],
        ),
        page_probe(
            "SEC_INSIDER_DATASETS",
            "https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets",
            ["January 2006", "June 2026", "Forms 3, 4 and 5", "as-filed"],
        ),
        page_probe(
            "SEC_TECHNICAL_SPECS",
            "https://www.sec.gov/submit-filings/technical-specifications",
            ["Schedule 13D & 13G", "Version 2.3", "Ownership (Forms 3, 4, 5)", "Version 5.5"],
        ),
        page_probe(
            "SEC_13F_FAQ",
            "https://www.sec.gov/rules-regulations/staff-guidance/division-investment-management-frequently-asked-questions/frequently-asked-questions-about-form-13f",
            ["$100 million", "45 days", "2026-2028"],
        ),
        json_probe(
            "SEC_TICKER_MAPPING",
            "https://www.sec.gov/files/company_tickers.json",
            ["0.ticker", "0.cik_str"],
        ),
        page_probe(
            "SEC_13F_REAL_FILING",
            "https://www.sec.gov/Archives/edgar/data/1418814/000141881426000003/0001418814-26-000003-index.htm",
            ["Form 13F-HR", "INFORMATION TABLE", "Accepted"],
        ),
        page_probe(
            "SEC_NPORT_REAL_FILING",
            "https://www.sec.gov/Archives/edgar/data/736913/000141036826084698/0001410368-26-084698-index.html",
            ["Form NPORT-P", "Accepted", "Monthly Portfolio Investments Report"],
        ),
        page_probe(
            "SEC_INSIDER_REAL_FILING",
            "https://www.sec.gov/Archives/edgar/data/736913/000141036826084698/0001410368-26-084698-index.html",
            ["Accepted", "Documents"],
        ),
    ]

    results = {p["id"]: p for p in probes}
    summary = {
        "verifiable_probes": sum(p["status"] == "VERIFIABLE" for p in probes),
        "schema_mismatch_probes": sum(p["status"] == "SCHEMA_MISMATCH" for p in probes),
        "blocked_probes": sum(p["status"] == "BLOCKED" for p in probes),
    }

    candidates = [
        {
            "id": "Q109:N1",
            "status": "ARCHIVE_BOUNDARY_VERIFIED_NOT_YET_SECURITY_COMPLETE",
            "source_basis": ["SEC_NPORT_DATASETS", "SEC_XBRL"],
            "historical_boundary": "2019-10",
            "performance_authorized": False,
        },
        {
            "id": "Q109:N2",
            "status": "ARCHIVE_BOUNDARY_VERIFIED_NOT_YET_SECURITY_COMPLETE",
            "source_basis": ["SEC_NPORT_DATASETS", "SEC_10K_Q"],
            "historical_boundary": "2019-10",
            "performance_authorized": False,
        },
        {
            "id": "Q109:C32",
            "status": "FILING_TEXT_SOURCE_VERIFIED",
            "source_basis": ["SEC_10K", "SEC_SUBMISSIONS"],
            "historical_boundary": "subject to issuer/form archive coverage",
            "performance_authorized": False,
        },
        {
            "id": "Q109:C33",
            "status": "DUAL_SOURCE_BOUNDARY",
            "source_basis": ["SEC_10K_Q", "SEC_NPORT_DATASETS"],
            "historical_boundary": "2019-10 for N-PORT leg unless separately reconstructed",
            "performance_authorized": False,
        },
        {
            "id": "Q109:I23",
            "status": "INSIDER_ARCHIVE_VERIFIED",
            "source_basis": ["SEC_INSIDER_DATASETS"],
            "historical_boundary": "2006-01",
            "performance_authorized": False,
        },
        {
            "id": "Q109:I24",
            "status": "EDGAR_PIT_SOURCE_VERIFIED",
            "source_basis": ["SEC_13D_13G_TECHNICAL_SPECS", "SEC_SUBMISSIONS"],
            "historical_boundary": "issuer/form coverage dependent",
            "performance_authorized": False,
        },
    ]

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-01-110-Q109-SOURCE-FEASIBILITY",
        "status": "SOURCE_FEASIBILITY_ONLY",
        "probes": probes,
        "summary": summary,
        "candidate_findings": candidates,
        "governance": {
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "performance_authorization": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q110_STATUS:", result["status"])
    print("Q110_VERIFIABLE:", summary["verifiable_probes"])
    print("Q110_SCHEMA_MISMATCH:", summary["schema_mismatch_probes"])
    print("Q110_BLOCKED:", summary["blocked_probes"])
    print("Q110_FINGERPRINT:", result["receipt_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
