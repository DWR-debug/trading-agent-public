"""Prepare and validate reproducible historical research data."""

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from data.market_updater import update_all, update_dataset
from data.market_store import MarketDataStore
from data.yahoo_loader import load_yahoo_history
from research.asset_universes import get_universe
from research.data_quality import validate_research_dataset
from research.protocol import dataset_fingerprint


DEFAULT_DATASETS = (
    ("BTCUSDT", "1h"),
    ("BTCUSDT", "15m"),
    ("ETHUSDT", "1h"),
    ("ETHUSDT", "15m"),
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _hash(value: object) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()



def manifest_fingerprint(manifest: dict) -> str:
    payload = dict(manifest)
    payload.pop("manifest_fingerprint", None)
    return _hash(payload)

def workflow_provenance() -> dict[str, str | None]:
    """Capture immutable workflow context without adding credentials."""

    return {
        "commit_sha": os.getenv("GITHUB_SHA"),
        "workflow": os.getenv("GITHUB_WORKFLOW"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "event_name": os.getenv("GITHUB_EVENT_NAME"),
        "ref_name": os.getenv("GITHUB_REF_NAME"),
    }


def prepare(
    target_count: int | None = None,
    *,
    output_path: str | Path = "research/data_manifest.json",
    universe: str | None = None,
    minimum_count: int = 1000,
):
    if target_count is not None and target_count < 500:
        raise ValueError("target_count muss mindestens 500 sein.")
    if minimum_count < 500:
        raise ValueError("minimum_count muss mindestens 500 sein.")

    store = MarketDataStore()
    validation_now = datetime.now(timezone.utc)

    if universe is None:
        target_count = target_count or 10000
        update_results = update_all(
            [
                (symbol, interval, target_count)
                for symbol, interval in DEFAULT_DATASETS
            ],
            store=store,
        )
        prepared = [
            (result.symbol, result.interval, "binance_public_klines")
            for result in update_results
        ]
    else:
        stock_universe = get_universe(universe)
        target_count = target_count or stock_universe.target_count
        prepared = []
        vendor_quality: dict[str, dict[str, int]] = {}
        for symbol in stock_universe.symbols:
            vendor_report: dict[str, int] = {}

            def partial_loader(symbol: str, interval: str, total: int):
                return load_yahoo_history(
                    symbol,
                    interval,
                    total,
                    allow_partial=True,
                    skip_invalid_ohlc=True,
                    quality_report=vendor_report,
                )

            result = update_dataset(
                symbol,
                stock_universe.interval,
                target_count,
                store=store,
                loader=partial_loader,
            )
            vendor_quality[result.symbol] = vendor_report
            prepared.append(
                (result.symbol, result.interval, "yahoo_chart")
            )

    datasets = []

    for symbol, interval, source in prepared:
        candles = tuple(store.load(symbol, interval))
        validate_research_dataset(
            candles,
            interval,
            expected_count=target_count if universe is None else None,
            now=validation_now,
        )
        if universe is not None and len(candles) < minimum_count:
            raise ValueError(
                f"Zu wenig Historie für {symbol}: {len(candles)} statt mindestens {minimum_count} Candles."
            )

        datasets.append(
            {
                "symbol": symbol,
                "interval": interval,
                "candle_count": len(candles),
                "data_start": candles[0].timestamp.isoformat(),
                "data_end": candles[-1].timestamp.isoformat(),
                "fingerprint": dataset_fingerprint(candles),
                "source": source,
                **(
                    {"vendor_quality": vendor_quality[symbol]}
                    if universe is not None
                    else {}
                ),
            }
        )

    manifest = {
        "generated_at": validation_now.isoformat(),
        "source": "binance_public_klines" if universe is None else "yahoo_chart",
        "universe": universe,
        "target_count": target_count,
        "minimum_count": minimum_count if universe is not None else None,
        "provenance": workflow_provenance(),
        "datasets": datasets,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    manifest["manifest_fingerprint"] = manifest_fingerprint(manifest)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    return manifest, path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target-count",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--universe",
        default=None,
        help="Aktienuniversum aus research.asset_universes",
    )
    parser.add_argument(
        "--output",
        default="research/data_manifest.json",
    )
    args = parser.parse_args()

    manifest, path = prepare(
        args.target_count,
        output_path=args.output,
        universe=args.universe,
        minimum_count=1000,
    )

    for dataset in manifest["datasets"]:
        print(
            f"{dataset['symbol']} {dataset['interval']}: "
            f"{dataset['candle_count']} Candles | "
            f"{dataset['data_start']} -> {dataset['data_end']}"
        )

    print(f"DATA_MANIFEST: {path}")


if __name__ == "__main__":
    main()
