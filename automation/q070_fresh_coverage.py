"""Q070 coverage-only selector and canonical snapshot builder.

Asset selection is fixed source-order coverage logic. No P&L or holdout
information is consulted and no candidate definition is changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation.fixed_window_candidate_discovery import run_discovery
from data.canonical_snapshot import snapshot_from_preregistration
from research.asset_universes import list_universes

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research/evidence/trial_ledger.json"
DESIGN_ID = "Q-2026-09-28-070-FIXED-CANDIDATE-VALIDATION-DESIGN"
COVERAGE_ID = "T-2026-09-28-070-COVERAGE"
PERFORMANCE_ID = "T-2026-09-28-070-PERFORMANCE"
UNIVERSE = "validation_2026_09_28_q070_fresh_ohlcv_candidates"
TARGET = 3500
REQUESTED = 4000
RAW = 5000
SELECT_COUNT = 8
SAFETY = {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False}

def _coverage_snapshot_spec(prereg: dict) -> dict:
    """Route the frozen snapshot under the coverage trial identity."""
    scoped = dict(prereg)
    scoped["trial_id"] = COVERAGE_ID
    scoped.setdefault("interval", "1d")
    scoped.setdefault("raw_fetch_candles", RAW)
    scoped.setdefault("target_common_count", TARGET)
    return scoped


def _fp(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()

def _used_symbols() -> set[str]:
    used = set()
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    for trial in ledger.get("trials", []):
        if isinstance(trial, dict):
            scope = trial.get("data_scope", {})
            if isinstance(scope, dict):
                for key in ("symbols", "trend_symbols", "cross_sectional_symbols", "requested_symbols", "universe_symbols"):
                    values = scope.get(key)
                    if isinstance(values, list): used.update(str(v) for v in values)
    for universe in list_universes(): used.update(universe.symbols)
    return used

def run(output_root: Path, result_path: Path, discovery_path: Path, asset_freeze_path: Path, performance_prereg_path: Path) -> dict:
    design = json.loads((ROOT / "research/preregistrations/q070_fixed_candidate_validation_2026_09_28.json").read_text(encoding="utf-8"))
    if design.get("task_id") != DESIGN_ID: raise ValueError("Q070 design identity mismatch")
    if design.get("status") != "PREREGISTERED_DESIGN_ONLY": raise ValueError("Q070 design status mismatch")
    discovery = run_discovery(output=discovery_path, symbol_limit=48, workers=8)
    selected = tuple(discovery.get("selected_coverage_batch", [])[:SELECT_COUNT])
    if len(selected) != SELECT_COUNT: raise RuntimeError(f"Q070 needs {SELECT_COUNT} jointly valid symbols, got {len(selected)}")
    overlap = sorted(set(selected) & _used_symbols())
    if overlap: raise RuntimeError(f"Q070 overlap detected: {overlap}")

    spec = {
        "trial_id": COVERAGE_ID, "universe": UNIVERSE, "symbols": list(selected), "interval": "1d",
        "requested_candles": REQUESTED, "raw_fetch_candles": RAW, "target_common_candles": TARGET,
        "target_common_count": TARGET, "study_window": {"start":"2011-01-01","end":"2025-09-24"},
        "governance": design["governance"], "safety": design["safety"],
    }
    coverage = snapshot_from_preregistration(spec, output_root=output_root)
    status = "COVERAGE_PASSED" if coverage["status"] == "COVERAGE_PASSED" else "DATA_INVALID"
    freeze = {
        "schema_version":"1.0","trial_id":COVERAGE_ID,"status":status,"universe":UNIVERSE,
        "symbols":list(selected),"requested_candles":REQUESTED,"raw_fetch_candles":RAW,
        "target_common_candles":TARGET,"study_window":spec["study_window"],
        "selection_rule":design["asset_selection_contract"],
        "source_discovery_fingerprint":discovery["fingerprint"],
        "source_discovery_run":discovery.get("discovery_id"),
        "snapshot_fingerprint":coverage.get("snapshot_fingerprint"),
        "performance_selection_used":False,"holdout_selection_used":False,
        "safety":SAFETY
    }
    performance_prereg = {
        "schema_version":"1.0","trial_id":PERFORMANCE_ID,"status":"PREREGISTERED_PERFORMANCE",
        "research_family":"q070_orthogonal_ohlcv_fixed_candidate_performance",
        "candidate_source":"Q069 fixed candidate bank",
        "candidates":design["source_candidate_bank"]["candidates"],"universe":UNIVERSE,
        "symbols":list(selected),"requested_candles":REQUESTED,"target_common_candles":TARGET,
        "research_periods":2798,"holdout_periods":700,"coverage_trial_id":COVERAGE_ID,"pit_trial_id":"T-2026-09-28-070-PIT",
        "selection_used":False,"holdout_used_for_selection":False,
        "governance":{**design["governance"],"performance_trial_authorized":False},
        "safety":SAFETY,
        "source_discovery_fingerprint":discovery["fingerprint"],
        "asset_freeze_fingerprint":_fp(freeze)
    }
    for path, payload in ((asset_freeze_path,freeze),(performance_prereg_path,performance_prereg),(result_path,{
        "schema_version":"1.0","trial_id":COVERAGE_ID,"research_family":"q070_fresh_coverage",
        "status":status,"symbols":list(selected),"universe":UNIVERSE,
        "requested_candles":REQUESTED,"target_common_candles":TARGET,
        "study_window":spec["study_window"],"common_calendar_count":coverage["coverage"]["common_calendar_count"],
        "snapshot_fingerprint":coverage.get("snapshot_fingerprint"),"coverage_errors":coverage["coverage"]["errors"],
        "selection_used":False,"performance_evaluation":False,"oos_evaluation":False,"holdout_evaluation":False,
        "performance_trial_authorized":False,"source_discovery":discovery,
        "asset_freeze":freeze,"governance":design["governance"],"safety":SAFETY})):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    print("Q070_COVERAGE_STATUS:", status)
    print("Q070_SYMBOLS:", ",".join(selected))
    print("Q070_SNAPSHOT_FINGERPRINT:", coverage.get("snapshot_fingerprint"))
    print("Q070_COVERAGE_FINGERPRINT:", _fp(freeze))
    return freeze

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-root",required=True); p.add_argument("--result",required=True);
    p.add_argument("--discovery",required=True); p.add_argument("--asset-freeze",required=True); p.add_argument("--performance-prereg",required=True)
    a=p.parse_args(); result=run(Path(a.output_root),Path(a.result),Path(a.discovery),Path(a.asset_freeze),Path(a.performance_prereg)); raise SystemExit(0 if result["status"]=="COVERAGE_PASSED" else 2)