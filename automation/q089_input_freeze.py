"""Q089 immutable performance-input bundle freeze."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from automation.q079_input_freeze import fetch_adjusted_close

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ID = "T-2026-09-28-089-INPUT-FREEZE"
COVERAGE_ID = "T-2026-09-28-089-COVERAGE"
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


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


def freeze(coverage_root: Path, output_root: Path, result_path: Path) -> dict:
    manifest_path = coverage_root / "snapshot_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # The canonical snapshot manifest intentionally carries no trial_id. Bind
    # identity through the dedicated Q089 coverage receipt and the immutable
    # snapshot fingerprint instead of overloading the generic snapshot schema.
    coverage_receipt_path = ROOT / "research" / "evidence" / "q089_coverage_result.json"
    if not coverage_receipt_path.is_file():
        raise RuntimeError("Q089 coverage receipt is missing")
    coverage_receipt = json.loads(coverage_receipt_path.read_text(encoding="utf-8"))
    if coverage_receipt.get("trial_id") != COVERAGE_ID:
        raise RuntimeError("Q089 coverage receipt identity mismatch")
    if coverage_receipt.get("status") != "COVERAGE_PASSED":
        raise RuntimeError("Q089 coverage receipt is not passed")
    if coverage_receipt.get("snapshot_fingerprint") != manifest.get("snapshot_fingerprint"):
        raise RuntimeError("Q089 coverage snapshot fingerprint mismatch")

    symbols = list(manifest["symbols"])
    datasets = []
    output_root.mkdir(parents=True, exist_ok=True)

    for symbol in symbols:
        csv_path = coverage_root / "datasets" / symbol / "1d.csv"
        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        timestamps = [str(row["timestamp"]) for row in rows]
        if len(timestamps) != int(manifest["target_common_candles"]):
            raise RuntimeError(
                f"{symbol}: expected {manifest['target_common_candles']} OHLCV rows, got {len(timestamps)}"
            )

        values = fetch_adjusted_close(symbol, timestamps)
        relative = Path(symbol) / "adjusted_close.csv"
        target = output_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["timestamp", "adjusted_close"])
            writer.writerows(values)

        datasets.append(
            {
                "symbol": symbol,
                "path": relative.as_posix(),
                "row_count": len(values),
                "first_timestamp": values[0][0],
                "last_timestamp": values[-1][0],
                "fingerprint": _fp(values),
            }
        )

    bundle = {
        "schema_version": "1.0",
        "trial_id": BUNDLE_ID,
        "source_snapshot_manifest": manifest_path.as_posix(),
        "source_snapshot_fingerprint": manifest["snapshot_fingerprint"],
        "symbols": symbols,
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
        "trial_id": BUNDLE_ID,
        "status": "INPUT_BUNDLE_FROZEN",
        "source_snapshot_fingerprint": manifest["snapshot_fingerprint"],
        "bundle_fingerprint": bundle["bundle_fingerprint"],
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
    print("Q089_INPUT_FREEZE_STATUS:", result["status"])
    print("Q089_INPUT_BUNDLE_FINGERPRINT:", result["bundle_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    raise SystemExit(
        freeze(
            Path(args.coverage_root),
            Path(args.output_root),
            Path(args.result),
        )
        and 0
    )
