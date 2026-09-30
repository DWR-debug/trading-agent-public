"""Q077-R1 exact performance-input freeze.

Freezes only the adjusted-close series needed by the already-preregistered
total-return-sensitivity accounting, aligned exactly to the persisted OHLCV
snapshot timestamps. No performance or selection is performed.
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
from pathlib import Path


UA = "trading-agent-public/Q077R1-input-freeze/1.0"
BUNDLE_ID = "T-2026-09-28-077R1-INPUT-FREEZE"
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def fetch_adjusted_close(symbol: str, timestamps: list[str]) -> list[tuple[str, float]]:
    if not timestamps:
        raise RuntimeError(f"{symbol}: empty target timestamp set")

    from datetime import datetime, timezone

    parsed = [datetime.fromisoformat(x) for x in timestamps]
    start = min(parsed)
    end = max(parsed)
    p1 = int(start.timestamp()) - 7 * 86400
    p2 = int(end.timestamp()) + 7 * 86400
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(symbol, safe="")
        + "?"
        + urllib.parse.urlencode(
            {
                "period1": p1,
                "period2": p2,
                "interval": "1d",
                "events": "div,splits",
                "includePrePost": "false",
            }
        )
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

            values: dict[str, float] = {}
            for ts, value in zip(raw_ts, raw_adj):
                if value is None:
                    continue
                iso = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
                values[iso] = float(value)

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
                    f"{symbol}: {len(missing)} snapshot timestamps missing from adjusted-close source"
                )
            return selected
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 ** attempt)

    raise RuntimeError(f"{symbol}: adjusted-close fetch failed: {last_error}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coverage-root", required=True)
    ap.add_argument("--output-root", required=True)
    ap.add_argument("--result", required=True)
    args = ap.parse_args()

    coverage_root = Path(args.coverage_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest_path = coverage_root / "snapshot_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    symbols = list(manifest["symbols"])
    if symbols != ["AJG", "ALGN", "AME", "AOS", "APH", "AXON", "BAH", "BALL", "BBWI", "BRO", "BWA", "CDNS"]:
        raise RuntimeError("Q077-R1 input freeze symbol contract mismatch")

    target_by_symbol: dict[str, list[str]] = {}
    for symbol in symbols:
        csv_path = coverage_root / "datasets" / symbol / "1d.csv"
        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        timestamps = [str(row["timestamp"]) for row in rows]
        if len(timestamps) != int(manifest["target_common_candles"]):
            raise RuntimeError(
                f"{symbol}: expected {manifest['target_common_candles']} rows, got {len(timestamps)}"
            )
        target_by_symbol[symbol] = timestamps

    datasets = []
    for symbol in symbols:
        values = fetch_adjusted_close(symbol, target_by_symbol[symbol])
        rel = Path(symbol) / "adjusted_close.csv"
        dest = output_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["timestamp", "adjusted_close"])
            writer.writerows(values)

        dataset = {
            "symbol": symbol,
            "path": rel.as_posix(),
            "row_count": len(values),
            "first_timestamp": values[0][0],
            "last_timestamp": values[-1][0],
            "fingerprint": fp(values),
        }
        datasets.append(dataset)

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
    bundle["bundle_fingerprint"] = fp(bundle)
    (output_root / "input_bundle_manifest.json").write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    result = {
        "schema_version": "1.0",
        "trial_id": BUNDLE_ID,
        "status": "INPUT_BUNDLE_FROZEN",
        "symbols": symbols,
        "source_snapshot_fingerprint": manifest["snapshot_fingerprint"],
        "bundle_fingerprint": bundle["bundle_fingerprint"],
        "datasets": datasets,
        "performance_network_access": False,
        "selection_used": False,
        "performance_evaluation": False,
        "holdout_used_for_selection": False,
        "safety": SAFETY,
    }
    Path(args.result).parent.mkdir(parents=True, exist_ok=True)
    Path(args.result).write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Q077R1_INPUT_FREEZE_STATUS:", result["status"])
    print("Q077R1_INPUT_BUNDLE_FINGERPRINT:", result["bundle_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
