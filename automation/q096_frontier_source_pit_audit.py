from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "research" / "frontier" / "candidate_inventory_2026_09_29.json"
TIMEOUT = 30
UA = "trading-agent-public/Q096-frontier-audit contact=research"

PROBES = [
    ("SEC_10K_ITEM1A", "https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm", "html", ["Item 1A", "RISK FACTORS"]),
    ("SEC_10Q_MDA", "https://www.sec.gov/Archives/edgar/data/1125345/000119312526000056/mgnx-20260630.htm", "html", ["MANAGEMENT'S DISCUSSION AND ANALYSIS", "Item 2"]),
    ("SEC_SUBMISSIONS_MSFT", "https://data.sec.gov/submissions/CIK0000789019.json", "json", []),
    ("SEC_COMPANYFACTS_MSFT", "https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json", "companyfacts", []),
    ("LSEG_RUSSELL_RECON", "https://www.lseg.com/en/ftse-russell/russell-reconstitution", "html", ["December 2026 Russell Reconstitution Calendar", "2026 June final index additions and deletions"]),
    ("CBOE_VIX_HISTORY", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv", "csv", ["DATE,OPEN,HIGH,LOW,CLOSE"]),
    ("GDELT_DAILY_ARCHIVE", "https://data.gdeltproject.org/events/20260928.export.CSV.zip", "zip", []),
]

def get(url: str) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return int(r.status), r.read(), r.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), None

def fp(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()

def probe(item):
    ident, url, kind, checks = item
    status, data, ctype = get(url)
    row = {
        "id": ident,
        "url": url,
        "http_status": status,
        "content_type": ctype,
        "response_bytes": len(data),
        "response_sha256": fp(data),
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200:
        row["reason"] = f"HTTP_{status}"
        return row
    text = data.decode("utf-8", "replace")
    if kind == "html":
        row["checks"] = {c: c.lower() in text.lower() for c in checks}
    elif kind == "json":
        try:
            payload = json.loads(data)
            filing = payload.get("filings", {}).get("recent", {})
            row["checks"] = {
                "valid_json": True,
                "has_name": bool(payload.get("name")),
                "has_recent_filings": bool(filing),
                "has_forms": bool(filing.get("form")),
                "has_accession_numbers": bool(filing.get("accessionNumber")),
            }
        except json.JSONDecodeError:
            row["checks"] = {"valid_json": False}
    elif kind == "companyfacts":
        try:
            payload = json.loads(data)
            dei = payload.get("facts", {}).get("dei", {})
            shares = dei.get("EntityCommonStockSharesOutstanding", {})
            units = shares.get("units", {})
            row["checks"] = {
                "valid_json": True,
                "has_entity_name": bool(payload.get("entityName")),
                "has_dei_namespace": bool(dei),
                "has_shares_outstanding_fact": bool(units),
                "has_instant_values": any(bool(v) for v in units.values()),
            }
        except json.JSONDecodeError:
            row["checks"] = {"valid_json": False}
    elif kind == "csv":
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        row["checks"] = {
            "has_header": bool(lines) and lines[0] == checks[0],
            "has_rows": len(lines) > 1,
            "five_columns": len(lines[1].split(",")) == 5 if len(lines) > 1 else False,
        }
    elif kind == "zip":
        try:
            with zipfile.ZipFile(BytesIO(data)) as z:
                names = z.namelist()
                row["checks"] = {
                    "valid_zip": bool(names),
                    "contains_csv": any(n.lower().endswith(".csv") for n in names),
                }
                row["zip_members"] = names[:5]
        except zipfile.BadZipFile:
            row["checks"] = {"valid_zip": False}
    row["status"] = "VERIFIABLE" if row["checks"] and all(row["checks"].values()) else "SCHEMA_MISMATCH"
    return row

def candidate_gate_matrix(candidates):
    rows = []
    for code, name, source, existing_state in candidates:
        source_l = source.lower()
        if "option" in source_l:
            source_state = "UNPROVEN_PUBLIC_HISTORICAL_SOURCE"
            archive_state = "BLOCKED_PENDING_FREE_COMPLETE_OPTION_ARCHIVE"
        elif any(k in source_l for k in ("sec form 4", "sec 13f", "sec 8-k", "sec filing", "shares outstanding", "sec +")):
            source_state = "PUBLIC_SOURCE_CHANNEL_CONFIRMED"
            archive_state = "HISTORICAL_ARCHIVE_PIT_AUDIT_PENDING"
        elif "gdelt" in source_l or "public news" in source_l:
            source_state = "PUBLIC_SOURCE_CHANNEL_CONFIRMED"
            archive_state = "HISTORICAL_ENTITY_MAPPING_AND_PIT_PENDING"
        elif "scheduled benchmark" in source_l:
            source_state = "PUBLIC_SOURCE_CHANNEL_CONFIRMED"
            archive_state = "HISTORICAL_ANNOUNCEMENT_ARCHIVE_AND_MAPPING_PENDING"
        elif any(k in source_l for k in ("alfred", "cftc", "wikimedia", "finra", "cboe")):
            source_state = "PUBLIC_SOURCE_CHANNEL_CONFIRMED"
            archive_state = "HISTORICAL_COVERAGE_ALREADY_FEASIBLE_OR_ALREADY_PROBED"
        elif any(k in source_l for k in ("ohlcv", "daily close", "market +", "calendar")):
            source_state = "CANONICAL_PROJECT_DATA_OR_DETERMINISTIC_INPUT"
            archive_state = "NO_NEW_EXTERNAL_ARCHIVE_GATE"
        else:
            source_state = "DESIGN_REVIEW_REQUIRED"
            archive_state = "EXPLICIT_SOURCE_CONTRACT_REQUIRED"
        pit_state = "MACHINE_FEASIBILITY_PRESENT" if existing_state in {
            "MACHINE_FEASIBILITY_IMPLEMENTED",
            "FEASIBILITY_CHECK_COMPLETED_NO_PERFORMANCE",
        } else "PIT_CONTRACT_REVIEW_REQUIRED"
        rows.append({
            "candidate": code,
            "name": name,
            "source": source,
            "existing_state": existing_state,
            "source_state": source_state,
            "pit_state": pit_state,
            "archive_state": archive_state,
            "performance_authorized": False,
        })
    return rows

def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    candidates = [list(row) for row in inventory["candidates"]]
    probes = [probe(item) for item in PROBES]
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-09-29-096-FRONTIER-SOURCE-PIT-AUDIT",
        "status": "SOURCE_AND_PIT_FEASIBILITY_ONLY",
        "inventory_count": len(candidates),
        "candidate_gate_matrix": candidate_gate_matrix(candidates),
        "live_source_probes": probes,
        "governance": {
            "performance_evaluation": False,
            "holdout_evaluation": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    out = ROOT / "research" / "runs" / "q096_frontier_source_pit_audit" / "result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Q096_STATUS:", result["status"])
    print("Q096_INVENTORY_COUNT:", len(candidates))
    for row in probes:
        print(row["id"], row["status"], row.get("reason", ""))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
