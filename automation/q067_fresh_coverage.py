"""Q067 fresh, symbol-disjoint coverage runner."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from data.canonical_snapshot import snapshot_from_preregistration
from research.asset_universes import list_universes

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research" / "evidence" / "trial_ledger.json"


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        .encode("utf-8")
    ).hexdigest()


def _used_symbols() -> set[str]:
    used: set[str] = set()
    payload = json.loads(LEDGER.read_text(encoding="utf-8"))
    for trial in payload.get("trials", []):
        scope = trial.get("data_scope", {})
        for key in ("symbols", "trend_symbols", "cross_sectional_symbols", "requested_symbols", "universe_symbols"):
            values = scope.get(key)
            if isinstance(values, list):
                used.update(str(value) for value in values)
    for universe in list_universes():
        used.update(str(symbol) for symbol in universe.symbols)
    return used


def run(preregistration: Path, output_root: Path, result_path: Path) -> dict:
    prereg = json.loads(preregistration.read_text(encoding="utf-8"))
    symbols = tuple(prereg["symbols"])
    used = _used_symbols()
    overlap = sorted(set(symbols) & used)
    if overlap:
        raise RuntimeError(f"Q067 fresh-universe overlap detected: {overlap}")

    coverage = snapshot_from_preregistration(prereg, output_root=output_root)
    result = {
        "schema_version": "1.0",
        "trial_id": prereg["coverage_trial_id"],
        "research_family": "q067_fresh_disjoint_coverage",
        "status": "COVERAGE_PASSED" if coverage["status"] == "COVERAGE_PASSED" else "DATA_INVALID",
        "symbols": list(symbols),
        "requested_candles": int(prereg["requested_candles"]),
        "target_common_candles": int(prereg["target_common_candles"]),
        "common_calendar_count": coverage["coverage"]["common_calendar_count"],
        "snapshot_fingerprint": coverage.get("snapshot_fingerprint"),
        "coverage_errors": coverage["coverage"]["errors"],
        "overlap_with_registered_state": overlap,
        "selection_used": False,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "performance_trial_authorized": False,
        "governance": prereg["governance"],
        "safety": prereg["safety"],
    }
    result["result_fingerprint"] = _fp(result)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("Q067_COVERAGE_STATUS:", result["status"])
    print("Q067_COVERAGE_FINGERPRINT:", result["result_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    run(Path(args.preregistration), Path(args.output_root), Path(args.result))
