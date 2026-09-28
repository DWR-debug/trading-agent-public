"""RCCSM observational feasibility on a frozen Q089 snapshot.

No returns-as-targets, P&L, holdout outcomes, optimization, or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from automation.q069_candidate_bank import CANDIDATES
from automation.rccsm_disagreement import disagreement_at
from automation.rccsm_state import state_at
from data.canonical_snapshot import load_frozen_snapshot

ROOT = Path(__file__).resolve().parents[1]
Q089_COVERAGE_ID = "T-2026-09-28-089-COVERAGE"
Q089_MANIFEST = ROOT / "research" / "runs" / "q089_coverage" / Q089_COVERAGE_ID / "snapshot_manifest.json"
Q089_RECEIPT = ROOT / "research" / "evidence" / "q089_coverage_result.json"

def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()

def _mutate_future(assets: dict, index: int, factor: float) -> dict:
    return {
        symbol: tuple(
            bar if i <= index else type(bar)(
                timestamp=bar.timestamp,
                open=bar.open * factor,
                high=bar.high * factor,
                low=bar.low * factor,
                close=bar.close * factor,
                volume=bar.volume,
            )
            for i, bar in enumerate(bars)
        )
        for symbol, bars in assets.items()
    }

def _sample_indices(length: int) -> tuple[int, ...]:
    candidates = (273, 400, 631, 862, 1093, 1324, 1555, 1786, 2017, 2248, 2479, 2710, 2941, 3172, 3403)
    return tuple(i for i in candidates if i < length)

def run(
    *,
    manifest_path: Path = Q089_MANIFEST,
    receipt_path: Path = Q089_RECEIPT,
    output_path: Path = ROOT / "research" / "runs" / "rccsm_observational" / "q089_rccsm_observational_feasibility.json",
) -> dict[str, Any]:
    if not manifest_path.is_file():
        raise RuntimeError(f"Q089 snapshot manifest missing: {manifest_path}")
    if not receipt_path.is_file():
        raise RuntimeError(f"Q089 coverage receipt missing: {receipt_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("trial_id") != Q089_COVERAGE_ID:
        raise RuntimeError("Q089 coverage receipt trial identity mismatch")
    if receipt.get("status") != "COVERAGE_PASSED":
        raise RuntimeError("Q089 coverage is not passed")
    if receipt.get("snapshot_fingerprint") != manifest.get("snapshot_fingerprint"):
        raise RuntimeError("Q089 receipt/snapshot fingerprint mismatch")
    if manifest.get("status") != "COVERAGE_PASSED":
        raise RuntimeError("Q089 snapshot is not frozen/passed")

    assets = load_frozen_snapshot(manifest_path)
    symbols = tuple(manifest["symbols"])
    if tuple(assets) != symbols:
        raise RuntimeError("Q089 symbol ordering mismatch")
    if len(symbols) != 8 or len(set(symbols)) != 8:
        raise RuntimeError("Q089 observational feasibility requires exactly eight unique frozen symbols")
    row_counts = {len(values) for values in assets.values()}
    if row_counts != {int(manifest["target_common_candles"])}:
        raise RuntimeError("Q089 snapshot geometry mismatch")

    observations = []
    for index in _sample_indices(len(next(iter(assets.values())))):
        state = state_at(assets, index, symbols=symbols)
        disagreement = disagreement_at(assets, index, symbols=symbols)
        mutated = _mutate_future(assets, index, 11.0)
        if state_at(mutated, index, symbols=symbols) != state:
            raise AssertionError(f"future mutation changed state at index {index}")
        if disagreement_at(mutated, index, symbols=symbols) != disagreement:
            raise AssertionError(f"future mutation changed disagreement at index {index}")
        observations.append({
            "index": index,
            "state_fingerprint": state["provenance_fingerprint"],
            "disagreement_fingerprint": disagreement["provenance_fingerprint"],
            "trend_coherence": state["trend_coherence"],
            "breadth": state["breadth"],
            "dispersion_percentile": state["dispersion_percentile"],
            "shock_density": state["shock_density"],
            "mechanism_disagreement": disagreement["mechanism_disagreement"],
            "future_mutation_invariant": True,
        })

    result = {
        "schema_version": 1,
        "component": "RCCSM-OBSERVATIONAL-FEASIBILITY",
        "source_trial_id": Q089_COVERAGE_ID,
        "source_snapshot_fingerprint": manifest["snapshot_fingerprint"],
        "symbols": list(symbols),
        "candidate_ids": list(CANDIDATES),
        "sample_count": len(observations),
        "observations": observations,
        "state_topology": {
            "uses_future_bars": False,
            "uses_returns_as_targets": False,
            "uses_holdout": False,
            "uses_optimizer": False,
            "uses_performance_labels": False,
        },
        "governance": {
            "performance_evaluation": False,
            "holdout_used": False,
            "selection_used": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "status": "OBSERVATIONAL_FEASIBILITY_PASSED",
    }
    result["fingerprint"] = _fp(result)
    output_path = output_path if output_path.is_absolute() else ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "sample_count": result["sample_count"], "fingerprint": result["fingerprint"]}, sort_keys=True))
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(Q089_MANIFEST))
    parser.add_argument("--receipt", default=str(Q089_RECEIPT))
    parser.add_argument("--output", default=str(ROOT / "research" / "runs" / "rccsm_observational" / "q089_rccsm_observational_feasibility.json"))
    args = parser.parse_args()
    raise SystemExit(0 if run(manifest_path=Path(args.manifest), receipt_path=Path(args.receipt), output_path=Path(args.output))["status"] == "OBSERVATIONAL_FEASIBILITY_PASSED" else 1)
