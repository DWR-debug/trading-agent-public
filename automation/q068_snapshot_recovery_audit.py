from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from automation.q068_fresh_coverage import _coverage_snapshot_spec
from data.canonical_snapshot import snapshot_from_preregistration

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research/preregistrations/q068_fixed_mechanism_freeze_2026_09_28.json"
COVERAGE = ROOT / "research/evidence/q068_coverage_result.json"
OUT = ROOT / "research/evidence/q068_snapshot_recovery_audit.json"


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
    authoritative_fp = coverage.get("snapshot_fingerprint")
    audit = {
        "schema_version": "1.0",
        "trial_id": "T-2026-09-28-068-SNAPSHOT-AUDIT",
        "status": "RECONSTRUCTION_PENDING",
        "authoritative_snapshot_fingerprint": authoritative_fp,
        "authoritative_coverage_result_fingerprint": coverage.get("result_fingerprint"),
        "authoritative_common_calendar_count": coverage.get("common_calendar_count"),
        "authoritative_symbols": coverage.get("symbols"),
        "performance_trial_authorized": False,
        "selection_used": False,
        "observed_snapshot_fingerprint": None,
        "observed_common_calendar_count": None,
        "observed_status": None,
        "reconstruction_error": None,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    try:
        with tempfile.TemporaryDirectory(prefix="q068-snapshot-audit-") as tmp:
            rebuilt = snapshot_from_preregistration(
                _coverage_snapshot_spec(prereg),
                output_root=Path(tmp),
            )
            audit["observed_snapshot_fingerprint"] = rebuilt.get("snapshot_fingerprint")
            audit["observed_common_calendar_count"] = rebuilt.get("coverage", {}).get("common_calendar_count")
            audit["observed_status"] = rebuilt.get("status")
            if rebuilt.get("snapshot_fingerprint") == authoritative_fp:
                audit["status"] = "SNAPSHOT_REPRODUCTION_EXACT"
            else:
                audit["status"] = "SNAPSHOT_REPRODUCTION_MISMATCH"
    except Exception as exc:
        audit["status"] = "SNAPSHOT_RECONSTRUCTION_UNAVAILABLE"
        audit["reconstruction_error"] = f"{type(exc).__name__}: {exc}"
    audit["audit_fingerprint"] = _fp(audit)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print("Q068 SNAPSHOT AUDIT:", audit["status"])
    print("Q068 AUTHORITATIVE:", authoritative_fp)
    print("Q068 OBSERVED:", audit["observed_snapshot_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
