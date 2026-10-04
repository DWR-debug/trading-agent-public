"""Q182 FERC self-hosted access probe.

Operational/data-QA only. A successful request does not establish PIT validity,
archive completeness, issuer mapping, performance authorization, or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

URLS = [
    "https://ferc.gov/what-elibrary",
    "https://www.ferc.gov/about/what-ferc/frequently-asked-questions-faqs/documents-and-filing/elibrary",
]
MARKERS = ["issued by FERC", "Documents received and issued by FERC", "download"]


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "trading-agent-public/Q182-access-probe/2",
            "Accept": "text/html,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()


def classify(status: int, body: bytes) -> tuple[str, list[str]]:
    text = body.decode("utf-8", errors="replace")
    missing = [marker for marker in MARKERS if marker.lower() not in text.lower()]
    if status == 200 and not missing:
        return "PASS", []
    if status in (401, 403):
        return "RUNNER_ACCESS_BLOCKED", missing
    if status == 200:
        return "REACHABLE_MARKER_MISMATCH", missing
    return "UNREACHABLE", missing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    probes = []
    for url in URLS:
        status, body = fetch(url)
        classification, missing = classify(status, body)
        probes.append({
            "url": url,
            "http_status": status,
            "classification": classification,
            "missing_markers": missing,
            "sha256": hashlib.sha256(body).hexdigest(),
        })

    result = {
        "schema_version": "1.0",
        "receipt_type": "q182_ferc_self_hosted_access_probe",
        "status": "Q182_ACCESS_PROBE_COMPLETED_NO_SCIENTIFIC_EVIDENCE",
        "runner_platform": "windows_x64_self_hosted",
        "probes": probes,
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_selection": False,
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
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "probes": probes,
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
