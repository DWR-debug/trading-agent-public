"""Fail-closed audit for durability of source-feasibility readiness.

A live endpoint probe/content hash is useful operational telemetry, but it is
not a durable historical source snapshot. This guard marks such readiness as
PROVISIONAL until an immutable dated snapshot/vintage or explicitly frozen
historical artifact is bound to the receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RULE_VERSION = "GROK-PRINCIPLE-2026-10-04-V1"

RECEIPTS = {
    "Q185-Q186": ROOT / "research/evidence/q185_q186_source_feasibility_latest.json",
    "Q187-Q192": ROOT / "research/evidence/q187_q192_source_feasibility_latest.json",
    "Q193-Q196": ROOT / "research/evidence/q193_q196_source_feasibility_latest.json",
    "Q197-Q198": ROOT / "research/evidence/q197_q198_source_feasibility_latest.json",
    "Q199-Q201": ROOT / "research/evidence/q199_q201_source_feasibility_latest.json",
}

DURABLE_KEYS = (
    "immutable_historical_snapshot",
    "immutable_snapshot",
    "dated_snapshot",
    "snapshot_sha256",
    "historical_snapshot_sha256",
    "vintage_sha256",
    "archive_fingerprint",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_durable_binding(receipt: dict[str, Any]) -> bool:
    for key in DURABLE_KEYS:
        value = receipt.get(key)
        if value:
            return True
    archive = receipt.get("archive_contract")
    if isinstance(archive, dict):
        for key in DURABLE_KEYS:
            if archive.get(key):
                return True
    return False


def classify(receipt: dict[str, Any]) -> str:
    if receipt.get("status") not in {
        "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "SOURCE_COMPONENT_READY",
        "HISTORICAL_SOURCE_COMPONENT_READY",
    }:
        return "NON_SOURCE_READY_STATE"
    return "DURABLE_HISTORICAL_BOUND" if has_durable_binding(receipt) else "PROVISIONAL_LIVE_PROBE_ONLY"


def audit() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for scope, path in RECEIPTS.items():
        if not path.is_file():
            entries.append({"scope": scope, "status": "MISSING_RECEIPT", "path": str(path.relative_to(ROOT))})
            continue
        receipt = load(path)
        entries.append({
            "scope": scope,
            "receipt_status": receipt.get("status"),
            "durability_class": classify(receipt),
            "receipt_fingerprint": receipt.get("receipt_fingerprint"),
            "receipt_file_sha256": sha256_file(path),
            "scientific_boundary": receipt.get("scientific_boundary", {}),
        })
    provisional = [x["scope"] for x in entries if x.get("durability_class") == "PROVISIONAL_LIVE_PROBE_ONLY"]
    out = {
        "schema_version": "1.0",
        "receipt_type": "source_readiness_snapshot_durability_guard",
        "rule_version": RULE_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PROVISIONAL_SOURCE_READINESS_REQUIRES_IMMUTABLE_HISTORICAL_BINDING" if provisional else "ALL_SOURCE_READINESS_DURABLE",
        "entries": entries,
        "provisional_live_probe_only_scopes": provisional,
        "formal_pit_allowed_from_this_audit": False,
        "performance_authorized": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    }
    out["audit_fingerprint"] = hashlib.sha256(
        json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "provisional": result["provisional_live_probe_only_scopes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
