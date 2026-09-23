"""Verify that a rolling-control run archived the exact raw research inputs.

This is a fail-closed integrity check. It does not fetch data or run research.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from data.market_store import MarketDataStore
from research.protocol import dataset_fingerprint


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(
    manifest_path: str | Path,
    data_dir: str | Path = "data/market_data",
    expected_count: int = 5000,
    expected_symbols: tuple[str, ...] = ("IWM", "QQQ", "SPY"),
) -> dict:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    if manifest.get("source") != "yahoo_chart":
        raise ValueError("Unexpected research data source in archived manifest.")
    if manifest.get("universe") != "benchmark":
        raise ValueError("Archived rolling-control input is not the benchmark universe.")
    if int(manifest.get("target_count", 0)) != expected_count:
        raise ValueError("Archived rolling-control target count mismatch.")

    datasets = manifest.get("datasets", [])
    symbols = tuple(sorted(item["symbol"] for item in datasets))
    if symbols != tuple(sorted(expected_symbols)):
        raise ValueError(
            f"Archived symbols mismatch: {symbols!r} != {tuple(sorted(expected_symbols))!r}"
        )

    store = MarketDataStore(base_dir=data_dir)
    archived_files = []
    for item in datasets:
        symbol = item["symbol"]
        interval = item["interval"]
        path = store.path_for(symbol, interval)
        if not path.exists():
            raise FileNotFoundError(f"Missing archived raw data: {path}")
        candles = tuple(store.load(symbol, interval))
        if len(candles) != expected_count:
            raise ValueError(
                f"{symbol}: {len(candles)} candles found; expected {expected_count}."
            )
        actual_fp = dataset_fingerprint(candles)
        expected_fp = item["fingerprint"]
        if actual_fp != expected_fp:
            raise ValueError(
                f"{symbol}: dataset fingerprint mismatch: {actual_fp} != {expected_fp}"
            )
        archived_files.append(
            {
                "symbol": symbol,
                "interval": interval,
                "relative_path": str(path),
                "byte_sha256": _sha256_file(path),
                "dataset_fingerprint": actual_fp,
                "candle_count": len(candles),
                "data_start": candles[0].timestamp.isoformat(),
                "data_end": candles[-1].timestamp.isoformat(),
            }
        )

    return {
        "schema_version": 1,
        "manifest_path": str(manifest_path),
        "manifest_fingerprint": manifest.get("manifest_fingerprint"),
        "universe": manifest["universe"],
        "target_count": expected_count,
        "datasets": archived_files,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--data-dir", default="data/market_data")
    parser.add_argument(
        "--output",
        default="research/rolling_geometry_control/raw_archive_manifest.json",
    )
    parser.add_argument("--expected-count", type=int, default=5000)
    args = parser.parse_args()

    result = verify(
        args.manifest,
        data_dir=args.data_dir,
        expected_count=args.expected_count,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    print("ROLLING_RAW_ARCHIVE: VERIFIED")
    print("DATASETS:", len(result["datasets"]))
    print("TARGET_COUNT:", result["target_count"])
    print("MANIFEST_FINGERPRINT:", result["manifest_fingerprint"])
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", result["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
