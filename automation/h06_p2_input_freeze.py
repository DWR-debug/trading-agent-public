"""Freeze H06-P2 adjusted-close inputs against the exact frozen OHLCV snapshot.

Upstream-only step. No forward return, P&L, holdout evaluation, selection or
performance authorization is performed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from backtesting.models import Candle
from research.protocol import dataset_fingerprint

BUNDLE_ID = "T-2026-10-01-H06P2-INPUT-FREEZE"
SOURCE_TRIAL_ID = "H06-REPAIR-2026-09-25"
EXPECTED_SNAPSHOT_FINGERPRINT = "e80e63eebbc94a32043dcf9c38aa86d2f7dc88eb7c2a172de24dfd9b269e55c6"
EXPECTED_SYMBOLS = (
    "TXN","ADI","AMAT","MDT","SYK","BDX","ETN","ITW","GD",
    "CL","KMB","GIS","AEP","XEL","DTE",
)
UA = "trading-agent-public/H06P2-input-freeze/1.0"
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def _load_candles(csv_path: Path) -> tuple[Candle, ...]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return tuple(
        Candle(
            timestamp=datetime.fromisoformat(row["timestamp"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )
        for row in rows
    )


def verify_snapshot(coverage_root: Path) -> tuple[dict, dict[str, list[str]]]:
    manifest = json.loads((coverage_root / "snapshot_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("universe") != "validation_2026_09_25_sector_neutral_residual_momentum_repair":
        raise RuntimeError("H06-P2 snapshot universe mismatch")
    if manifest.get("snapshot_fingerprint") != EXPECTED_SNAPSHOT_FINGERPRINT:
        raise RuntimeError("H06-P2 snapshot fingerprint mismatch")
    if tuple(manifest.get("symbols", ())) != EXPECTED_SYMBOLS:
        raise RuntimeError("H06-P2 symbol contract mismatch")
    if int(manifest.get("target_common_candles", 0)) != 3500:
        raise RuntimeError("H06-P2 snapshot geometry mismatch")

    timestamps: dict[str, list[str]] = {}
    for symbol in EXPECTED_SYMBOLS:
        path = coverage_root / symbol / "1d.csv"
        if not path.is_file():
            raise RuntimeError(f"H06-P2 missing frozen OHLCV: {symbol}")
        candles = _load_candles(path)
        if len(candles) != 3500:
            raise RuntimeError(f"H06-P2 {symbol}: expected 3500 OHLCV rows, got {len(candles)}")
        declared = next(x for x in manifest["datasets"] if x["symbol"] == symbol)
        actual_fp = dataset_fingerprint(candles)
        if actual_fp != declared["fingerprint"]:
            raise RuntimeError(f"H06-P2 {symbol}: OHLCV fingerprint mismatch")
        timestamps[symbol] = [c.timestamp.isoformat() for c in candles]

    reference = timestamps[EXPECTED_SYMBOLS[0]]
    if any(timestamps[s] != reference for s in EXPECTED_SYMBOLS[1:]):
        raise RuntimeError("H06-P2 frozen OHLCV timestamps are not aligned")
    return manifest, timestamps


def fetch_adjusted_close(symbol: str, timestamps: list[str]) -> list[tuple[str, float]]:
    parsed = [datetime.fromisoformat(x) for x in timestamps]
    p1 = int(min(parsed).timestamp()) - 7 * 86400
    p2 = int(max(parsed).timestamp()) + 7 * 86400
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(symbol, safe="")
        + "?"
        + urllib.parse.urlencode({
            "period1": p1,
            "period2": p2,
            "interval": "1d",
            "events": "div,splits",
            "includePrePost": "false",
        })
    )

    last_error: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result = payload["chart"]["result"][0]
            raw_ts = result["timestamp"]
            raw_adj = result["indicators"]["adjclose"][0]["adjclose"]
            values = {
                datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat(): float(value)
                for ts, value in zip(raw_ts, raw_adj)
                if value is not None
            }
            selected = []
            missing = []
            for target in timestamps:
                value = values.get(target)
                if value is None:
                    missing.append(target)
                else:
                    selected.append((target, value))
            if missing:
                raise RuntimeError(
                    f"{symbol}: {len(missing)} frozen timestamps missing from adjusted-close source"
                )
            return selected
        except (
            urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            KeyError, IndexError, TypeError, ValueError, RuntimeError
        ) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"{symbol}: adjusted-close fetch failed: {last_error}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coverage-root", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    args = ap.parse_args()

    manifest, timestamps = verify_snapshot(args.coverage_root)
    args.output_root.mkdir(parents=True, exist_ok=True)

    datasets = []
    for symbol in EXPECTED_SYMBOLS:
        values = fetch_adjusted_close(symbol, timestamps[symbol])
        rel = Path(symbol) / "adjusted_close.csv"
        dest = args.output_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "adjusted_close"])
            writer.writerows(values)
        datasets.append({
            "symbol": symbol,
            "path": rel.as_posix(),
            "row_count": len(values),
            "first_timestamp": values[0][0],
            "last_timestamp": values[-1][0],
            "fingerprint": fp(values),
        })

    bundle = {
        "schema_version": "1.0",
        "trial_id": BUNDLE_ID,
        "source_trial_id": SOURCE_TRIAL_ID,
        "source_snapshot_fingerprint": manifest["snapshot_fingerprint"],
        "symbols": list(EXPECTED_SYMBOLS),
        "datasets": datasets,
        "performance_network_access": False,
        "selection_used": False,
        "parameter_search": False,
        "threshold_search": False,
        "asset_search": False,
        "horizon_search": False,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "holdout_used_for_selection": False,
        "governance": {"performance_authorized": False},
        "safety": SAFETY,
    }
    bundle["bundle_fingerprint"] = fp(bundle)

    manifest_path = args.output_root / "input_bundle_manifest.json"
    manifest_path.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    result = {
        "schema_version": "1.0",
        "trial_id": BUNDLE_ID,
        "status": "INPUT_BUNDLE_FROZEN",
        "source_trial_id": SOURCE_TRIAL_ID,
        "source_snapshot_fingerprint": manifest["snapshot_fingerprint"],
        "bundle_fingerprint": bundle["bundle_fingerprint"],
        "dataset_count": len(datasets),
        "datasets": datasets,
        "performance_network_access": False,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "performance_authorized": False,
        "safety": SAFETY,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("H06_P2_INPUT_FREEZE_STATUS:", result["status"])
    print("H06_P2_INPUT_BUNDLE_FINGERPRINT:", result["bundle_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
