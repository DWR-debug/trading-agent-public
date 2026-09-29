"""Q091 immutable adjusted-close input bundle freeze.

This step is upstream of performance. It consumes only the persisted Q091
common-calendar snapshot and fetches adjusted close once, then fingerprints the
result. Performance code must consume this bundle network-free.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from automation.q079_input_freeze import fetch_adjusted_close
from data.canonical_snapshot import load_frozen_snapshot

COVERAGE_ID = "T-2026-09-29-091-COVERAGE"
INPUT_ID = "T-2026-09-29-091-INPUT-FREEZE"
TARGET = 3500
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def freeze(root: Path, output_root: Path, result_path: Path) -> dict:
    coverage_path = root / "research/evidence/q091_coverage_result.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    if coverage.get("trial_id") != COVERAGE_ID or coverage.get("status") != "COVERAGE_PASSED":
        raise RuntimeError("Q091 coverage receipt is not passed")

    manifest_path = root / "research/runs/q091_coverage" / COVERAGE_ID / "snapshot_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = load_frozen_snapshot(manifest_path)
    symbols = tuple(coverage["symbols"])
    if tuple(assets) != symbols or any(len(assets[s]) != TARGET for s in symbols):
        raise RuntimeError("Q091 snapshot geometry/symbol contract mismatch")
    if coverage.get("snapshot_fingerprint") != manifest.get("snapshot_fingerprint"):
        raise RuntimeError("Q091 coverage receipt/snapshot fingerprint mismatch")

    output_root.mkdir(parents=True, exist_ok=True)
    datasets = []
    for symbol in symbols:
        timestamps = [bar.timestamp.isoformat() for bar in assets[symbol]]
        values = fetch_adjusted_close(symbol, timestamps)
        target = output_root / symbol / "adjusted_close.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(("timestamp", "adjusted_close"))
            writer.writerows(values)
        datasets.append({
            "symbol": symbol,
            "path": (Path(symbol) / "adjusted_close.csv").as_posix(),
            "row_count": len(values),
            "first_timestamp": values[0][0],
            "last_timestamp": values[-1][0],
            "fingerprint": _fp(values),
        })

    bundle = {
        "schema_version": "1.0",
        "trial_id": INPUT_ID,
        "source_snapshot_fingerprint": coverage["snapshot_fingerprint"],
        "symbols": list(symbols),
        "datasets": datasets,
        "performance_network_access": False,
        "selection_used": False,
        "performance_evaluation": False,
        "holdout_used_for_selection": False,
        "safety": SAFETY,
    }
    bundle["bundle_fingerprint"] = _fp(bundle)
    manifest_out = output_root / "input_bundle_manifest.json"
    manifest_out.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    result = {
        "schema_version": "1.0",
        "trial_id": INPUT_ID,
        "status": "INPUT_BUNDLE_FROZEN",
        "coverage_trial_id": COVERAGE_ID,
        "source_snapshot_fingerprint": coverage["snapshot_fingerprint"],
        "bundle_fingerprint": bundle["bundle_fingerprint"],
        "symbols": list(symbols),
        "datasets": datasets,
        "performance_network_access": False,
        "selection_used": False,
        "performance_evaluation": False,
        "holdout_used_for_selection": False,
        "safety": SAFETY,
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Q091_INPUT_FREEZE_STATUS:", result["status"])
    print("Q091_INPUT_BUNDLE_FINGERPRINT:", result["bundle_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    freeze(
        Path(args.repo_root),
        Path(args.output_root),
        Path(args.result),
    )
