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

def _common_timestamps(
    candles_by_key: dict[tuple[str, str], tuple],
) -> tuple:
    if not candles_by_key:
        raise ValueError("Mindestens ein Asset muss für die Kalenderausrichtung vorhanden sein.")

    timestamp_sets = [
        {candle.timestamp for candle in candles}
        for candles in candles_by_key.values()
    ]
    common = set.intersection(*timestamp_sets)
    return tuple(sorted(common))


def _trim_to_common_calendar(
    store: MarketDataStore,
    prepared: list[tuple[str, str, str]],
    target_count: int,
) -> dict[str, int]:
    """Persist the last target_count timestamps shared by every asset.

    The function fails closed when the common timestamp intersection is too
    short. It never fills missing candles and never changes candle values.
    """
    if target_count < 1:
        raise ValueError("target_count muss mindestens 1 sein.")

    candles_by_key = {
        (symbol, interval): tuple(store.load(symbol, interval))
        for symbol, interval, _source in prepared
    }
    common = _common_timestamps(candles_by_key)

    if len(common) < target_count:
        raise ValueError(
            f"Zu wenig gemeinsame Kalender-Candles: {len(common)} statt mindestens "
            f"{target_count}."
        )

    selected = common[-target_count:]
    selected_set = set(selected)

    for (symbol, interval), candles in candles_by_key.items():
        by_timestamp = {candle.timestamp: candle for candle in candles}
        aligned = tuple(by_timestamp[ts] for ts in selected)
        if len(aligned) != target_count:
            raise ValueError(
                f"{symbol} {interval}: Kalenderausrichtung ergab {len(aligned)} "
                f"Candles statt {target_count}."
            )
        store.save(symbol, interval, aligned)

    return {
        "raw_common_candle_count": len(common),
        "aligned_candle_count": target_count,
    }


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
        prepared = [
            (symbol.upper(), stock_universe.interval, "yahoo_chart")
            for symbol in stock_universe.symbols
        ]
        vendor_quality: dict[str, dict[str, int]] = {}
        acquisition_count = target_count
        alignment_attempts = 0
        max_alignment_attempts = 5

        while True:
            vendor_quality = {}
            for symbol, interval, _source in prepared:
                vendor_report: dict[str, int] = {}

                def partial_loader(
                    loader_symbol: str,
                    loader_interval: str,
                    total: int,
                    *,
                    _report=vendor_report,
                ):
                    return load_yahoo_history(
                        loader_symbol,
                        loader_interval,
                        total,
                        allow_partial=True,
                        skip_invalid_ohlc=True,
                        quality_report=_report,
                    )

                update_dataset(
                    symbol,
                    interval,
                    acquisition_count,
                    store=store,
                    loader=partial_loader,
                )
                vendor_quality[symbol] = vendor_report

            candles_by_key = {
                (symbol, interval): tuple(store.load(symbol, interval))
                for symbol, interval, _source in prepared
            }
            common_count = len(_common_timestamps(candles_by_key))
            if common_count >= target_count:
                break

            alignment_attempts += 1
            if alignment_attempts >= max_alignment_attempts:
                raise ValueError(
                    f"Gemeinsamer Kalender bleibt zu kurz: {common_count} statt "
                    f"{target_count} nach {max_alignment_attempts} Akquisitionen."
                )

            acquisition_count += target_count - common_count + 1

        alignment = _trim_to_common_calendar(
            store,
            prepared,
            target_count,
        )

    datasets = []

    for symbol, interval, source in prepared:
        candles = tuple(store.load(symbol, interval))
        validate_research_dataset(
            candles,
            interval,
            expected_count=target_count,
            now=validation_now,
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
        "calendar_alignment": (
            {
                "mode": "timestamp_intersection_tail",
                "raw_common_candle_count_before_trim": alignment["raw_common_candle_count"],
                "aligned_candle_count": alignment["aligned_candle_count"],
                "acquisition_candle_count": acquisition_count,
                "alignment_attempts": alignment_attempts,
            }
            if universe is not None
            else {
                "mode": "not_applicable",
            }
        ),
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
