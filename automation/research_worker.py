"""Legacy low-cost local research diagnostic.

This path is intentionally non-authoritative. The central reproducible
Research workflow is the supported path for research decisions and writeback.

No live trading.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from automation.backtest_runner import run_dataset
from automation.research_run import build_run_identity
from automation.research_workflow import result_fingerprint
from config.parameter_space import ParameterSpace
from data.market_store import MarketDataStore
from research.protocol import ResearchProtocol
from validation.research_gates import evaluate_research_gates


def build_output(
    result: dict,
    gates: dict,
    run_manifest: dict,
) -> dict:
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "research_type": "legacy_local_diagnostic",
        "authoritative": False,
        "research_status": gates["status"],
        "safety": result["safety"],
        "protocol": result["protocol"],
        "gates": gates,
        "run_manifest": run_manifest,
        "dataset": {
            "symbol": result["symbol"],
            "interval": result["interval"],
            "candle_count": result["candle_count"],
            "research_candle_count": result["research_candle_count"],
            "holdout_candle_count": result["holdout_candle_count"],
            "data_start": result["data_start"],
            "research_end": result["research_end"],
            "holdout_start": result["holdout_start"],
            "data_end": result["data_end"],
            "dataset_fingerprint": result["dataset_fingerprint"],
            "research_dataset_fingerprint": result["research_dataset_fingerprint"],
            "holdout_dataset_fingerprint": result["holdout_dataset_fingerprint"],
        },
        "baseline": result["baseline"],
        "walk_forward": result["walk_forward"],
        "rolling_walk_forward": result["rolling_walk_forward"],
        "holdout": result["holdout"],
        "optimization_top": result["optimization"],
    }
    output["result_fingerprint"] = result_fingerprint(output)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1h")
    args = parser.parse_args()

    store = MarketDataStore()
    protocol = ResearchProtocol()
    parameter_space = ParameterSpace()

    result = run_dataset(
        args.symbol,
        args.interval,
        store=store,
        parameter_space=parameter_space,
        protocol=protocol,
    )

    candles = tuple(
        store.load(
            args.symbol,
            args.interval,
        )
    )
    gates = evaluate_research_gates(
        result,
        candles,
        train_ratio=0.7,
    )

    run_manifest = build_run_identity(
        [(args.symbol, args.interval)],
        store,
        protocol,
        parameter_space,
    )

    output = build_output(result, gates, run_manifest)

    out_dir = Path("research/results")
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"{args.symbol}_{args.interval}_{stamp}.json"

    path.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    print(f"RESEARCH_RESULT: {path}")
    print(f"RESEARCH_STATUS: {gates['status']}")
    print(f"RESEARCH_RESULT_FINGERPRINT: {output['result_fingerprint']}")
    print(
        "RESEARCH_AUTHORITATIVE: "
        + ("YES" if output["authoritative"] else "NO")
    )

    if gates["failed_gates"]:
        print("FAILED_GATES: " + ", ".join(gates["failed_gates"]))


if __name__ == "__main__":
    main()