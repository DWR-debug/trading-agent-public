"""Verify pinned Q129 historical options source assets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

EXPECTED = {
    "SPY_options.parquet": (
        "https://github.com/lambdaclass/options_portfolio_backtester/releases/download/data-v1/SPY_options.parquet",
        631738559,
        "a7152991b45b81f090f970e945bf88def8093b8ecb9b250e9891cb6d88041f0a",
    ),
    "QQQ_options.parquet": (
        "https://github.com/lambdaclass/options_portfolio_backtester/releases/download/data-v1/QQQ_options.parquet",
        387476183,
        "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734",
    ),
    "IWM_options.parquet": (
        "https://github.com/lambdaclass/options_portfolio_backtester/releases/download/data-v1/IWM_options.parquet",
        308766441,
        "d16a728116f8095c97c39ed66e75000bf66a0ab422b678002eb9f6086fd10ee5",
    ),
}
EXPECTED_COLUMNS = {
    "contract_id",
    "symbol",
    "expiration",
    "strike",
    "type",
    "bid",
    "ask",
    "volume",
    "open_interest",
    "date",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, path: Path) -> None:
    request = Request(
        url,
        headers={"User-Agent": "trading-agent-public/Q129-source-feasibility/1"},
    )
    with urlopen(request, timeout=90) as response, path.open("wb") as output:
        while True:
            chunk = response.read(4 * 1024 * 1024)
            if not chunk:
                break
            output.write(chunk)


def inspect_parquet(path: Path) -> dict[str, object]:
    with path.open("rb") as handle:
        head = handle.read(4)
        handle.seek(-4, 2)
        tail = handle.read(4)
    result: dict[str, object] = {
        "valid_parquet_magic": head == b"PAR1" and tail == b"PAR1"
    }
    try:
        import pyarrow.parquet as pq

        metadata = pq.ParquetFile(path).metadata
        schema = pq.read_schema(path)
        names = set(schema.names)
        result.update(
            {
                "pyarrow": True,
                "rows": metadata.num_rows,
                "row_groups": metadata.num_row_groups,
                "columns": sorted(names),
                "expected_columns_present": EXPECTED_COLUMNS.issubset(names),
            }
        )
    except Exception as exc:
        result.update(
            {
                "pyarrow": False,
                "metadata_error": type(exc).__name__,
                "expected_columns_present": False,
            }
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.workdir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, object]] = {}

    for name, (url, size, expected_hash) in EXPECTED.items():
        target = args.workdir / name
        download(url, target)
        observed_hash = sha256_file(target)
        parquet = inspect_parquet(target)
        results[name] = {
            "url": url,
            "expected_size": size,
            "observed_size": target.stat().st_size,
            "size_match": target.stat().st_size == size,
            "expected_sha256": expected_hash,
            "observed_sha256": observed_hash,
            "sha256_match": observed_hash == expected_hash,
            "parquet": parquet,
        }

    ok = all(
        item["size_match"]
        and item["sha256_match"]
        and item["parquet"]["valid_parquet_magic"]
        and item["parquet"]["expected_columns_present"]
        for item in results.values()
    )

    receipt = {
        "schema_version": "1.0",
        "candidate_id": "Q129",
        "status": "Q129_SOURCE_ASSETS_VERIFIED"
        if ok
        else "Q129_SOURCE_ASSET_VERIFICATION_FAILED",
        "same_day_decision_use_allowed": False,
        "assets": results,
        "scientific_boundary": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    receipt["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "receipt_fingerprint": receipt["receipt_fingerprint"],
                "rows": {
                    name: value["parquet"].get("rows")
                    for name, value in results.items()
                },
            },
            sort_keys=True,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
