"""Q079 fresh symbol-disjoint coverage runner.

Coverage only. Uses the frozen Q079 preregistration and the canonical snapshot
builder. No performance, holdout selection, ranking or promotion is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from data.canonical_snapshot import snapshot_from_preregistration
from research.asset_universes import list_universes

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research" / "evidence" / "trial_ledger.json"
FROZEN_SYMBOLS = ("HAL", "LRCX", "OXY", "COF", "FIS", "FISV", "GM", "LHX")
COVERAGE_TRIAL_ID = "T-2026-09-28-079-COVERAGE"


def _coverage_snapshot_spec(prereg: dict) -> dict:
    """Route the frozen snapshot under the execution receipt identity, not the design-freeze identity."""
    scoped = dict(prereg)
    scoped["trial_id"] = COVERAGE_TRIAL_ID
    return scoped


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


def _used_symbols(*, exclude_universe: str | None = None) -> set[str]:
    used: set[str] = set()
    payload = json.loads(LEDGER.read_text(encoding="utf-8"))
    for trial in payload.get("trials", []):
        if not isinstance(trial, dict):
            continue
        scope = trial.get("data_scope", {})
        if not isinstance(scope, dict):
            continue
        for key in (
            "symbols",
            "trend_symbols",
            "cross_sectional_symbols",
            "requested_symbols",
            "universe_symbols",
        ):
            values = scope.get(key)
            if isinstance(values, list):
                used.update(str(value) for value in values)
    for universe in list_universes():
        if exclude_universe is not None and universe.name == exclude_universe:
            continue
        used.update(str(symbol) for symbol in universe.symbols)
    return used


def run(preregistration: Path, output_root: Path, result_path: Path) -> dict:
    prereg = json.loads(preregistration.read_text(encoding="utf-8"))
    if prereg.get("trial_id") != "Q-2026-09-28-079-DESIGN-FREEZE":
        raise ValueError("Q079 design-freeze identity mismatch")
    symbols = tuple(prereg["symbols"])
    if symbols != FROZEN_SYMBOLS:
        raise ValueError("Q079 frozen symbol order mismatch")

    overlap = sorted(
        set(symbols) & _used_symbols(exclude_universe=str(prereg["universe"]))
    )
    if overlap:
        raise RuntimeError(f"Q079 fresh-universe overlap detected: {overlap}")

    coverage = snapshot_from_preregistration(_coverage_snapshot_spec(prereg), output_root=output_root)
    result = {
        "schema_version": "1.0",
        "trial_id": COVERAGE_TRIAL_ID,
        "research_family": "q079_fresh_e1_e2_coverage",
        "status": (
            "COVERAGE_PASSED"
            if coverage["status"] == "COVERAGE_PASSED"
            else "DATA_INVALID"
        ),
        "symbols": list(symbols),
        "requested_candles": int(prereg["requested_candles"]),
        "target_common_candles": int(prereg["target_common_candles"]),
        "study_window": prereg["study_window"],
        "common_calendar_count": coverage["coverage"]["common_calendar_count"],
        "snapshot_fingerprint": coverage.get("snapshot_fingerprint"),
        "coverage_errors": coverage["coverage"]["errors"],
        "overlap_with_registered_state": overlap,
        "source_discovery": prereg["source_discovery"],
        "selection_used": False,
        "performance_evaluation": False,
        "oos_evaluation": False,
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
    print("Q079_COVERAGE_STATUS:", result["status"])
    print("Q079_COVERAGE_FINGERPRINT:", result["result_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    run(
        Path(args.preregistration),
        Path(args.output_root),
        Path(args.result),
    )
