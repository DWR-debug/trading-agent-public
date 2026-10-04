"""Q182 FERC eLibrary self-hosted access probe.

Operational/data-qa only. A successful request does not establish PIT validity,
archive completeness, issuer mapping, or any performance authorization.
"""
from __future__ import annotations
import argparse, hashlib, json, urllib.error, urllib.request
from pathlib import Path

URLS = [
    "https://ferc.gov/what-elibrary",
    "https://www.ferc.gov/about/what-ferc/frequently-asked-questions-faqs/documents-and-filing/elibrary",
]
MARKERS = ["issued by FERC", "Documents received and issued by FERC", "download"]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "trading-agent-public/Q182-access-probe/1", "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return int(getattr(r, "status", 200)), r.read()
    except urllib.error.HTTPError as e:
        return int(e.code), e.read()
    except Exception as e:
        return 599, f"FETCH_ERROR:{type(e).__name__}:{e}".encode()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", required=True); args = ap.parse_args()
    probes = []
    for url in URLS:
        status, body = fetch(url)
        text = body.decode("utf-8", "replace")
        missing = [m for m in MARKERS if m.lower() not in text.lower()]
        probes.append({
            "url": url,
            "http_status": status,
            "classification": ("PASS" if status == 200 and not missing else "RUNNER_ACCESS_BLOCKED" if status in (401, 403) else "REACHABLE_MARKER_MISMATCH" if status == 200 else "UNREACHABLE"),
            "missing_markers": missing,
            "sha256": hashlib.sha256(body).hexdigest(),
        })
    result = {
        "schema_version": "1.0",
        "receipt_type": "q182_ferc_self_hosted_access_probe",
        "status": "Q182_ACCESS_PROBE_COMPLETED_NO_SCIENTIFIC_EVIDENCE",
        "runner_platform": "windows_x64_self_hosted",
        "probes": probes,
        "scientific_boundary": {"performance": False, "holdout_selection": False, "ranking": False, "parameter_search": False, "threshold_search": False, "horizon_search": False, "asset_selection": False, "promotion": False, "live_execution": False},
        "safety": {"PAPER_ONLY": True, "LIVE_TRADING_ENABLED": False, "ORDERS_ENABLED": False, "AUTOMATIC_PROMOTION": False},
    }
    result["receipt_fingerprint"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    p = Path(args.output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "probes": probes, "receipt_fingerprint": result["receipt_fingerprint"]}, sort_keys=True))

if __name__ == "__main__":
    main()