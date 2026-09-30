from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

TRIAL_ID = "T-2026-09-30-C29R1-INPUT-FREEZE"
COVERAGE_TRIAL_ID = "T-2026-09-30-C29R1-COVERAGE-PIT"
COVERAGE_ARTIFACT_ID = 11111130029
COVERAGE_WORKFLOW_RUN_ID = 36741493347
SNAPSHOT_FINGERPRINT = "ca54223f855f3f11cff3868ff1287ec7a544e61036b35b6f0f3f29cab4a12e50"
COVERAGE_FINGERPRINT = "6b3acf5fb179bc93c6fac8eaaef59d71aa909326d5f171d9718a7cfbc71e22a6"
SYMBOLS = ("PPG", "GWW", "PGR", "TT", "ICE", "KLAC", "SNA", "SWK")
N = 3500


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(source_root: Path, output_root: Path, receipt_path: Path) -> dict:
    coverage_dir = source_root / "research/runs/c29r1_coverage" / COVERAGE_TRIAL_ID
    matches = list(coverage_dir.glob("coverage_preflight_*.json"))
    if len(matches) != 1:
        raise FileNotFoundError("C29R1 coverage receipt is missing or ambiguous")
    coverage = json.loads(matches[0].read_text(encoding="utf-8"))
    if coverage.get("trial_id") != COVERAGE_TRIAL_ID or coverage.get("status") != "coverage_passed":
        raise RuntimeError("C29R1 coverage prerequisite invalid")
    if coverage.get("snapshot_fingerprint") != SNAPSHOT_FINGERPRINT:
        raise RuntimeError("C29R1 snapshot fingerprint mismatch")
    if coverage.get("coverage_fingerprint") != COVERAGE_FINGERPRINT:
        raise RuntimeError("C29R1 coverage fingerprint mismatch")
    if coverage.get("performance_evaluation") is not False or coverage.get("holdout_evaluation") is not False:
        raise RuntimeError("C29R1 coverage receipt is not non-evaluative")
    datasets_root = coverage_dir / "datasets"
    bundle_root = output_root / TRIAL_ID
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)
    datasets = []
    for symbol in SYMBOLS:
        src = datasets_root / symbol / "1d.csv"
        if not src.is_file():
            raise FileNotFoundError(f"missing frozen dataset: {symbol}")
        row_count = max(0, len(src.read_text(encoding="utf-8").splitlines()) - 1)
        if row_count != N:
            raise ValueError(f"{symbol}: expected {N} rows, got {row_count}")
        target = bundle_root / symbol / "1d.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        datasets.append({
            "symbol": symbol,
            "path": f"{symbol}/1d.csv",
            "row_count": row_count,
            "sha256": _file_sha256(target),
        })
    manifest = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "source_coverage_trial_id": COVERAGE_TRIAL_ID,
        "source_coverage_workflow_run_id": COVERAGE_WORKFLOW_RUN_ID,
        "source_coverage_artifact_id": COVERAGE_ARTIFACT_ID,
        "source_snapshot_fingerprint": SNAPSHOT_FINGERPRINT,
        "source_coverage_fingerprint": COVERAGE_FINGERPRINT,
        "symbols": list(SYMBOLS),
        "target_common_candles": N,
        "performance_network_access": False,
        "datasets": datasets,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "candidate_ranking": False,
        "candidate_selection": False,
        "performance_authorized": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    manifest["bundle_fingerprint"] = _fp(manifest)
    bundle_manifest = bundle_root / "input_bundle_manifest.json"
    bundle_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "status": "INPUT_BUNDLE_FROZEN",
        "source_coverage_trial_id": COVERAGE_TRIAL_ID,
        "source_coverage_workflow_run_id": COVERAGE_WORKFLOW_RUN_ID,
        "source_coverage_artifact_id": COVERAGE_ARTIFACT_ID,
        "source_snapshot_fingerprint": SNAPSHOT_FINGERPRINT,
        "source_coverage_fingerprint": COVERAGE_FINGERPRINT,
        "bundle_fingerprint": manifest["bundle_fingerprint"],
        "symbols": list(SYMBOLS),
        "target_common_candles": N,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "performance_authorized": False,
        "safety": manifest["safety"],
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("C29R1_INPUT_FREEZE_STATUS:", receipt["status"])
    print("C29R1_INPUT_BUNDLE_FINGERPRINT:", receipt["bundle_fingerprint"])
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    run(args.source_root, args.output_root, args.receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
