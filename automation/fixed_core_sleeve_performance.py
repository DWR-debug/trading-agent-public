"""Formal fixed-rule performance evaluation for T052.

The two sleeves and two universes are evaluated independently and all four
cells are reported. No ranking or selection is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from automation.cross_asset_trend_replication import _build_weight_path
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility

TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
CS_LOOKBACK = 252
CS_SKIP = 21
CS_REBALANCE = 21
CS_TOP_N = 2
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_MULTIPLIERS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)
YAHOO_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)

def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()

def _pf(value: object) -> float:
    return float("inf") if value == "inf" else float(value)

def _load_prereg(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("trial_id") != "T-2026-09-27-052" or spec.get("status") != "PREREGISTERED":
        raise ValueError("T052 preregistration mismatch")
    if spec.get("safety") != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }:
        raise RuntimeError("T052 safety contract mismatch")
    forbidden = (
        "parameter_search",
        "asset_search",
        "asset_selection_by_performance",
        "threshold_search",
        "horizon_search",
        "variant_search",
        "holdout_used_for_selection",
        "research_gate_changes",
        "promotion_decision",
        "live_execution",
        "automatic_promotion",
    )
    if any(spec["governance"].get(k) is True for k in forbidden):
        raise RuntimeError("T052 contains forbidden search/selection/promotion flag")
    validate_research_cost_compatibility(
        fee_rate=FEE_RATE,
        slippage_rate=SLIPPAGE_RATE,
    )
    return spec

def _load_assets(manifest_path: Path, expected: dict[str, object]) -> dict[str, tuple]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "COVERAGE_PASSED":
        raise ValueError("Snapshot is not coverage-passed")
    if manifest.get("universe") != expected["universe"]:
        raise ValueError("Snapshot universe mismatch")
    if tuple(manifest.get("symbols", [])) != tuple(expected["symbols"]):
        raise ValueError("Snapshot symbol set/order mismatch")
    if int(manifest.get("target_common_calendar", -1)) != TARGET_COUNT:
        raise ValueError("Snapshot target count mismatch")
    assets = load_frozen_snapshot(manifest_path)
    if tuple(assets) != tuple(expected["symbols"]):
        raise ValueError("Loaded snapshot symbols mismatch")
    if any(len(bars) != TARGET_COUNT for bars in assets.values()):
        raise ValueError("Frozen snapshot geometry mismatch")
    return assets

def _cs_weights(assets: dict[str, tuple]) -> tuple[dict[str, float], ...]:
    symbols = tuple(assets)
    n = len(next(iter(assets.values())))
    current = {s: 0.0 for s in symbols}
    output = []
    for i in range(n):
        if i % CS_REBALANCE == 0:
            if i < CS_LOOKBACK + CS_SKIP:
                current = {s: 0.0 for s in symbols}
            else:
                anchor = i - CS_SKIP
                origin = anchor - CS_LOOKBACK
                scores = {
                    s: assets[s][anchor].close / assets[s][origin].close - 1.0
                    for s in symbols
                }
                winners = set(sorted(scores, key=scores.get, reverse=True)[:CS_TOP_N])
                current = {s: (1.0 / CS_TOP_N if s in winners else 0.0) for s in symbols}
        output.append(dict(current))
    return tuple(output)

def _return_rows(assets: dict[str, tuple], weights: tuple[dict[str, float], ...]) -> list[dict]:
    symbols = tuple(assets)
    length = len(next(iter(assets.values())))
    previous = {s: 0.0 for s in symbols}
    output = []
    for decision_index in range(length - 2):
        target = weights[decision_index]
        gross = 0.0
        turnover = 0.0
        for symbol in symbols:
            bars = assets[symbol]
            market_return = bars[decision_index + 2].open / bars[decision_index + 1].open - 1.0
            weight = float(target.get(symbol, 0.0))
            gross += weight * market_return
            turnover += abs(weight - previous[symbol])
            previous[symbol] = weight
        output.append({
            "timestamp": assets[symbols[0]][decision_index + 2].timestamp.isoformat(),
            "gross_return": gross,
            "turnover": turnover,
        })
    return output

def _yahoo_adjclose(symbol: str, start: datetime, end: datetime) -> dict[datetime, float]:
    params = {
        "period1": int((start - timedelta(days=3)).timestamp()),
        "period2": int((end + timedelta(days=3)).timestamp()),
        "interval": "1d",
        "events": "div,splits",
        "includePrePost": "false",
    }
    url = f"{YAHOO_BASE_URL}/{urllib.parse.quote(symbol, safe='')}?{urllib.parse.urlencode(params)}"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "trading-agent-research/1.0"})
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result = payload["chart"]["result"][0]
            timestamps = result["timestamp"]
            values = result["indicators"]["adjclose"][0]["adjclose"]
            return {
                datetime.fromtimestamp(int(ts), tz=timezone.utc): float(v)
                for ts, v in zip(timestamps, values) if v is not None
            }
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError) as exc:
            if attempt == 3:
                raise RuntimeError(f"Adjusted close unavailable for {symbol}: {exc}") from exc
            time.sleep(2 ** attempt)
    raise RuntimeError("Unexpected adjusted-close failure")

def _stats(values: list[float], start: int, end: int) -> dict:
    segment = values[start:end]
    if not segment:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "day_count": 0,
        }
    equity = 1.0
    peak = 1.0
    drawdown = 0.0
    gain = 0.0
    loss = 0.0
    for value in segment:
        equity *= 1.0 + value
        peak = max(peak, equity)
        if peak > 0:
            drawdown = max(drawdown, 1.0 - equity / peak)
        if value > 0:
            gain += value
        elif value < 0:
            loss -= value
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": drawdown * 100.0,
        "profit_factor": gain / loss if loss > 0 else ("inf" if gain > 0 else 0.0),
        "day_count": len(segment),
    }

def _rolling(values: list[float]) -> list[dict]:
    width = RESEARCH_COUNT // 5
    out = []
    for index in range(5):
        start = index * width
        end = RESEARCH_COUNT if index == 4 else (index + 1) * width
        out.append({"window_index": index + 1, **_stats(values, start, end)})
    return out

def _total_return_rows(
    assets: dict[str, tuple],
    weights: tuple[dict[str, float], ...],
    adjusted: dict[str, dict[datetime, float]],
) -> list[float]:
    symbols = tuple(assets)
    length = len(next(iter(assets.values())))
    out = []
    for decision_index in range(length - 2):
        target = weights[decision_index]
        value = 0.0
        for symbol in symbols:
            bars = assets[symbol]
            raw_open = bars[decision_index + 2].open / bars[decision_index + 1].open - 1.0
            raw_close = bars[decision_index + 2].close / bars[decision_index + 1].close - 1.0
            previous_ts = bars[decision_index + 1].timestamp
            current_ts = bars[decision_index + 2].timestamp
            adj = adjusted[symbol][current_ts] / adjusted[symbol][previous_ts] - 1.0
            value += target.get(symbol, 0.0) * (raw_open + adj - raw_close)
        out.append(value)
    return out

def _evaluate(assets: dict[str, tuple], sleeve: str) -> dict:
    weights = (
        _build_weight_path(assets, "sma_50_200_inverse_vol")
        if sleeve == "trend"
        else _cs_weights(assets)
    )
    rows = _return_rows(assets, weights)
    if len(rows) < RESEARCH_COUNT + HOLDOUT_COUNT:
        raise ValueError("T052 return geometry is too short")
    adjusted = {
        symbol: _yahoo_adjclose(symbol, bars[0].timestamp, bars[-1].timestamp)
        for symbol, bars in assets.items()
    }
    base_gross = [row["gross_return"] for row in rows]
    turnover = [row["turnover"] for row in rows]
    scenarios = {}
    for name, multiplier in COST_MULTIPLIERS:
        rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier
        values = [gross - rate * turn for gross, turn in zip(base_gross, turnover)]
        research = _stats(values, 0, RESEARCH_COUNT)
        holdout = _stats(values, RESEARCH_COUNT, RESEARCH_COUNT + HOLDOUT_COUNT)
        rolling = _rolling(values)
        rolling_pf_gain = sum(x["period_return"] for x in rolling if x["period_return"] > 0)
        rolling_pf_loss = -sum(x["period_return"] for x in rolling if x["period_return"] < 0)
        rolling_pf = rolling_pf_gain / rolling_pf_loss if rolling_pf_loss > 0 else ("inf" if rolling_pf_gain > 0 else 0.0)
        scenarios[name] = {
            "research": research,
            "holdout": holdout,
            "rolling": rolling,
            "rolling_profit_factor": rolling_pf,
            "rolling_profitable_window_ratio": sum(x["period_return"] > 0 for x in rolling) / len(rolling),
            "rolling_average_drawdown_percent": sum(x["max_drawdown_percent"] for x in rolling) / len(rolling),
            "oos_to_is_return_ratio": holdout["period_return"] / research["period_return"] if research["period_return"] > 0 else 0.0,
        }
    total_rows = _total_return_rows(assets, weights, adjusted)
    total_rate = FEE_RATE + SLIPPAGE_RATE
    total_values = [gross - total_rate * turn for gross, turn in zip(total_rows, turnover)]
    base = scenarios["base"]
    stress15 = scenarios["stress_1_5x_cost"]["holdout"]
    stress2 = scenarios["stress_2x_cost"]["holdout"]
    total_holdout = _stats(total_values, RESEARCH_COUNT, RESEARCH_COUNT + HOLDOUT_COUNT)
    gates = {
        "research_return_positive": base["research"]["period_return"] > 0.0,
        "research_drawdown_lte_10pct": base["research"]["max_drawdown_percent"] <= 10.0,
        "research_profit_factor_gte_1_10": _pf(base["research"]["profit_factor"]) >= 1.10,
        "rolling_profit_factor_gte_1_10": _pf(base["rolling_profit_factor"]) >= 1.10,
        "rolling_profitable_window_ratio_gte_0_50": base["rolling_profitable_window_ratio"] >= 0.50,
        "rolling_average_drawdown_lte_10pct": base["rolling_average_drawdown_percent"] <= 10.0,
        "oos_to_is_return_ratio_gte_0_25": base["oos_to_is_return_ratio"] >= 0.25,
        "holdout_return_positive": base["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor_gte_1_10": _pf(base["holdout"]["profit_factor"]) >= 1.10,
        "holdout_drawdown_lte_10pct": base["holdout"]["max_drawdown_percent"] <= 10.0,
        "stress_1_5x_holdout_nonnegative": stress15["period_return"] >= 0.0,
        "stress_2x_holdout_nonnegative": stress2["period_return"] >= 0.0,
        "total_return_sensitivity_holdout_nonnegative": total_holdout["period_return"] >= 0.0,
    }
    return {
        "base": base,
        "stress_1_5x_cost": scenarios["stress_1_5x_cost"],
        "stress_2x_cost": scenarios["stress_2x_cost"],
        "total_return_sensitivity": {
            "research": _stats(total_values, 0, RESEARCH_COUNT),
            "holdout": total_holdout,
        },
        "all_gates_passed": all(gates.values()),
        "gates": gates,
    }

def run(preregistration_path: Path, manifests: dict[str, Path], output_path: Path) -> dict:
    spec = _load_prereg(preregistration_path)
    expected = {u["trial_id"]: u for u in spec["universes"]}
    reports = {}
    for trial_id in ("T-2026-09-27-049", "T-2026-09-27-050"):
        assets = _load_assets(manifests[trial_id], expected[trial_id])
        reports[trial_id] = {
            "universe": expected[trial_id]["universe"],
            "symbols": list(expected[trial_id]["symbols"]),
            "snapshot_fingerprint": json.loads(manifests[trial_id].read_text(encoding="utf-8"))["snapshot_fingerprint"],
            "trend_sma_50_200": _evaluate(assets, "trend"),
            "cs_momentum_12_1_top2": _evaluate(assets, "cs"),
        }
    report = {
        "schema_version": 1,
        "trial_id": "T-2026-09-27-052",
        "status": "COMPLETED",
        "code_version": os.getenv("GITHUB_SHA", "UNVERIFIED_LOCAL_CODE"),
        "governance": {
            "selection_used": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "variant_search": False,
            "holdout_used_for_selection": False,
            "automatic_promotion": False,
        },
        "universes": reports,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return report

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", required=True)
    parser.add_argument("--t049-manifest", required=True)
    parser.add_argument("--t050-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(
        Path(args.preregistration),
        {
            "T-2026-09-27-049": Path(args.t049_manifest),
            "T-2026-09-27-050": Path(args.t050_manifest),
        },
        Path(args.output),
    )
    print("T052_STATUS: COMPLETED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
