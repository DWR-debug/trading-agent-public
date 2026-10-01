"""Q113 fixed-quarter SEC 13F coverage feasibility for Q107."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
from automation.q111_security_identity_contract import canonical_security_key, normalize_text

DATASET_URL = "https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/01jun2026-31aug2026_form13f.zip"
TARGETS = {
    "SPGI": {"S&P GLOBAL INC", "SP GLOBAL INC"},
    "NDAQ": {"NASDAQ INC", "NASDAQ INCORPORATED"},
    "AMP": {"AMERIPRISE FINANCIAL INC"},
    "RJF": {"RAYMOND JAMES FINANCIAL INC"},
    "WMB": {"WILLIAMS COMPANIES INC", "WILLIAMS COMPANIES INC."},
    "VLO": {"VALERO ENERGY CORP", "VALERO ENERGY CORPORATION"},
    "DVN": {"DEVON ENERGY CORP", "DEVON ENERGY CORPORATION"},
    "EMN": {"EASTMAN CHEMICAL CO", "EASTMAN CHEMICAL COMPANY"},
}
UA = "trading-agent-public/Q113 research"

def norm_issuer(value: str) -> str:
    return normalize_text(value).replace(" CORPORATION", " CORP").replace(" COMPANY", " CO")

ALIASES = {s: {norm_issuer(a) for a in aliases} for s, aliases in TARGETS.items()}

def find_target(issuer: str) -> str | None:
    n = norm_issuer(issuer)
    for symbol, aliases in ALIASES.items():
        if n in aliases:
            return symbol
    return None

def download() -> bytes:
    req = urllib.request.Request(DATASET_URL, headers={"User-Agent": UA, "Accept": "application/zip"})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()

def read_member(zf: zipfile.ZipFile, suffix: str) -> list[dict[str, str]]:
    names = [n for n in zf.namelist() if n.lower().endswith(suffix.lower())]
    if not names:
        raise ValueError("Q113_MEMBER_NOT_FOUND:" + suffix)
    with zf.open(names[0]) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), delimiter="	"))

def scan(archive: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        submissions = read_member(zf, "submission.tsv")
        infos = read_member(zf, "infotable.tsv")
    by_accession = {r["ACCESSION_NUMBER"]: r for r in submissions}
    out = {s: {"matched_rows": 0, "security_keys": [], "cusips": [], "figis": [],
               "manager_ciks": [], "accessions": [], "periods": [], "submission_types": []} for s in TARGETS}
    for row in infos:
        symbol = find_target(row.get("NAMEOFISSUER", ""))
        if symbol is None:
            continue
        acc = row["ACCESSION_NUMBER"]
        sub = by_accession.get(acc)
        if sub is None:
            raise ValueError("Q113_ORPHAN_INFOTABLE_ACCESSION:" + acc)
        adapted = {"name_of_issuer": row.get("NAMEOFISSUER", ""),
                   "title_of_class": row.get("TITLEOFCLASS", ""),
                   "cusip": row.get("CUSIP"), "figi": row.get("FIGI")}
        out[symbol]["matched_rows"] += 1
        out[symbol]["security_keys"].append(canonical_security_key(adapted))
        if row.get("CUSIP"): out[symbol]["cusips"].append(row["CUSIP"])
        if row.get("FIGI"): out[symbol]["figis"].append(row["FIGI"])
        out[symbol]["manager_ciks"].append(sub["CIK"])
        out[symbol]["accessions"].append(acc)
        out[symbol]["periods"].append(sub["PERIODOFREPORT"])
        out[symbol]["submission_types"].append(sub["SUBMISSIONTYPE"])
    for symbol, row in out.items():
        for field in ("security_keys", "cusips", "figis", "manager_ciks", "accessions", "periods", "submission_types"):
            row[field] = sorted(set(x for x in row[field] if x))
        row["coverage_status"] = "FOUND" if row["matched_rows"] else "NOT_FOUND"
    return out

def synthetic_contract() -> dict[str, bool]:
    submission = b"ACCESSION_NUMBER\tFILING_DATE\tSUBMISSIONTYPE\tCIK\tPERIODOFREPORT\n000X-26-000001\t01-JUL-2026\t13F-HR\t0000123456\t30-JUN-2026\n"
    info = b"ACCESSION_NUMBER\tINFOTABLE_SK\tNAMEOFISSUER\tTITLEOFCLASS\tCUSIP\tFIGI\n000X-26-000001\t1\tDEVON ENERGY CORP\tCommon Stock\t25179M103\tBBG000K6VSB5\n"
    blob = io.BytesIO()
    with zipfile.ZipFile(blob, "w") as zf:
        zf.writestr("SUBMISSION.tsv", submission)
        zf.writestr("INFOTABLE.tsv", info)
    got = scan(blob.getvalue())["DVN"]
    return {
        "manager_join": got["manager_ciks"] == ["0000123456"],
        "identity": got["security_keys"] == ["CUSIP:25179M103"],
        "lineage": got["accessions"] == ["000X-26-000001"],
    }

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("research/runs/q113_13f_q107_coverage/result.json"))
    args = p.parse_args()
    archive = download()
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-01-113-13F-Q107-COVERAGE",
        "status": "13F_COVERAGE_FEASIBILITY_ONLY",
        "dataset_url": DATASET_URL,
        "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "archive_bytes": len(archive),
        "synthetic": synthetic_contract(),
        "coverage": scan(archive),
        "governance": {"performance": False, "holdout": False, "selection": False, "ranking": False, "parameter_search": False, "performance_authorized": False},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    result["receipt_fingerprint"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q113_STATUS:", result["status"])
    print("Q113_ARCHIVE_BYTES:", len(archive))
    print("Q113_SYNTHETIC_ALL_PASS:", all(result["synthetic"].values()))
    for symbol, row in result["coverage"].items():
        print("Q113_TARGET:", symbol, row["coverage_status"], row["matched_rows"], len(row["manager_ciks"]), len(row["cusips"]))
    print("Q113_FINGERPRINT:", result["receipt_fingerprint"])
    return 0 if all(result["synthetic"].values()) else 2

if __name__ == "__main__":
    raise SystemExit(main())
