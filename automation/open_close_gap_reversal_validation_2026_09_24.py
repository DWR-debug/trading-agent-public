"""Research-only validation of fixed overnight-gap / intraday reversal alpha."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import settings
from research.asset_universes import get_universe
from research.protocol import dataset_fingerprint

TARGET_UNIVERSE = "validation_2026_09_24_open_close_gap_reversal_v4"
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
ASSETS = ("JNJ", "KO", "PG", "WMT", "XOM", "CVX", "MCD", "PEP")
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
YAHOO_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"


def _canon(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(TARGET_UNIVERSE)
    symbols = tuple(item["symbol"] for item in manifest.get("datasets", []))
    if (
        manifest.get("universe") != TARGET_UNIVERSE
        or manifest.get("target_count") != TARGET_COUNT
        or symbols != ASSETS
        or manifest.get("source") != "yahoo_chart"
    ):
        raise ValueError("Open/Close Gap-Reversal market manifest contract mismatch.")
    safety = manifest.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError("Manifest safety contract violated.")
    if tuple(universe.symbols) != ASSETS:
        raise ValueError("Open/Close Gap-Reversal universe registration mismatch.")
    return manifest


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    from automation.candidate_validation_50_50_vol_budget import load_bars

    assets = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if len(bars) != TARGET_COUNT or dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: market dataset fingerprint mismatch.")
        assets[symbol] = tuple(bars)

    timestamps = [tuple(bar.timestamp for bar in bars) for bars in assets.values()]
    if any(values != timestamps[0] for values in timestamps[1:]):
        raise ValueError("Open/Close Gap-Reversal assets must share an identical timestamp calendar.")
    return assets


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
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "trading-agent-research/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode())
            result = payload["chart"]["result"][0]
            timestamps = result["timestamp"]
            adjusted = result["indicators"]["adjclose"][0]["adjclose"]
            return {
                datetime.fromtimestamp(int(ts), tz=timezone.utc): float(value)
                for ts, value in zip(timestamps, adjusted)
                if value is not None
            }
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            if attempt == 3:
                raise RuntimeError(f"Adjusted-Close für {symbol} nicht verfügbar: {exc}") from exc
            time.sleep(1.0 * (2**attempt))
    raise RuntimeError("Unerwarteter Yahoo-Fehler.")


def _adjusted_open_close(assets: dict[str, tuple]) -> dict[str, dict[datetime, tuple[float, float]]]:
    adjusted: dict[str, dict[datetime, tuple[float, float]]] = {}
    for symbol, bars in assets.items():
        adjclose = _yahoo_adjclose(symbol, bars[0].timestamp, bars[-1].timestamp)
        series = {}
        for bar in bars:
            try:
                adjusted_close = adjclose[bar.timestamp]
            except KeyError as exc:
                raise ValueError(
                    f"{symbol}: adjusted close missing at {bar.timestamp.isoformat()}."
                ) from exc
            factor = adjusted_close / bar.close
            adjusted_open = bar.open * factor
            if not math.isfinite(adjusted_open) or adjusted_open <= 0:
                raise ValueError(f"{symbol}: invalid adjusted open.")
            series[bar.timestamp] = (adjusted_open, adjusted_close)
        adjusted[symbol] = series
    return adjusted


def _return_rows(
    assets: dict[str, tuple],
    adjusted: dict[str, dict[datetime, tuple[float, float]]],
) -> tuple[dict, ...]:
    reference = next(iter(assets.values()))
    rows = []
    for index in range(2, TARGET_COUNT):
        timestamp = reference[index].timestamp
        previous = reference[index - 1].timestamp
        weighted_gross = 0.0
        gross_gap_mean = 0.0
        active_assets = 0
        turnover = 0.0
        strategy_weights = {}
        signed_edges = []
        for symbol, bars in assets.items():
            previous_close = adjusted[symbol][previous][1]
            current_open = adjusted[symbol][timestamp][0]
            current_close = adjusted[symbol][timestamp][1]
            gap = current_open / previous_close - 1.0
            intraday = current_close / current_open - 1.0
            signal = -1 if gap > 0.0 else 1 if gap < 0.0 else 0
            weight = signal / len(assets)
            strategy_return = weight * intraday
            weighted_gross += strategy_return
            gross_gap_mean += gap
            strategy_weights[symbol] = weight
            turnover += 2.0 * abs(weight)
            if signal != 0:
                active_assets += 1
            signed_edges.append(-gap * intraday)
        mean_gap = gross_gap_mean / len(assets)
        rows.append({
            "timestamp": timestamp.isoformat(),
            "previous_timestamp": previous.isoformat(),
            "overnight_gap_mean": mean_gap,
            "strategy_gross_return": weighted_gross,
            "turnover": turnover,
            "active_assets": active_assets,
            "mean_gap_reversal_edge": sum(signed_edges) / len(signed_edges),
            "net_before_costs": weighted_gross,
        })
    if len(rows) != RESEARCH_COUNT + HOLDOUT_COUNT:
        raise ValueError(f"Unexpected return count: {len(rows)}")
    return tuple(rows)


def _simulate(rows: tuple[dict, ...], multiplier: float) -> list[dict]:
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier
    return [
        {
            **row,
            "net_return": float(row["strategy_gross_return"]) - cost_rate * float(row["turnover"]),
        }
        for row in rows
    ]


def _stats(rows: list[dict]) -> dict:
    equity = peak = 1.0
    gp = gl = 0.0
    max_dd = 0.0
    edge_sum = 0.0
    positive_days = 0
    turnover = 0.0
    for row in rows:
        value = float(row["net_return"])
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak)
        if value > 0.0:
            gp += value
            positive_days += 1
        elif value < 0.0:
            gl -= value
        turnover += float(row["turnover"])
        edge_sum += float(row["mean_gap_reversal_edge"])
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gp / gl if gl > 0.0 else ("inf" if gp > 0.0 else 0.0),
        "day_count": len(rows),
        "positive_net_days": positive_days,
        "turnover": turnover,
        "mean_gap_reversal_edge": edge_sum / len(rows) if rows else None,
        "active_asset_days": sum(int(row["active_assets"]) for row in rows),
    }


def _rolling(rows: list[dict]) -> list[dict]:
    width = RESEARCH_COUNT // 5
    windows = []
    start = 0
    for index in range(5):
        end = RESEARCH_COUNT if index == 4 else start + width
        windows.append({"window_index": index + 1, **_stats(rows[start:end])})
        start = end
    return windows


def _scenario(rows: tuple[dict, ...], multiplier: float) -> dict:
    simulated = _simulate(rows, multiplier)
    research = _stats(simulated[:RESEARCH_COUNT])
    holdout = _stats(simulated[RESEARCH_COUNT:])
    rolling = _rolling(simulated)
    return {
        "research": research,
        "holdout": holdout,
        "rolling_windows": rolling,
        "rolling_summary": {
            "window_count": len(rolling),
            "profitable_windows": sum(item["period_return"] > 0.0 for item in rolling),
            "profitable_window_ratio": sum(item["period_return"] > 0.0 for item in rolling) / len(rolling),
        },
        "oos_to_is_return_ratio": (
            holdout["period_return"] / research["period_return"]
            if research["period_return"] > 0.0 else 0.0
        ),
    }


def run_validation(*, data_dir: Path, market_manifest: Path, output: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    manifest = _load_manifest(market_manifest)
    assets = _load_assets(data_dir, manifest)
    adjusted = _adjusted_open_close(assets)
    rows = _return_rows(assets, adjusted)
    scenarios = {
        "base": _scenario(rows, 1.0),
        "stress_1_5x_cost": _scenario(rows, 1.5),
        "stress_2x_cost": _scenario(rows, 2.0),
    }
    base = scenarios["base"]
    checks = {
        "research_return_positive": base["research"]["period_return"] > 0.0,
        "research_drawdown": base["research"]["max_drawdown_percent"] <= 10.0,
        "research_profit_factor": _pf(base["research"]["profit_factor"]) >= 1.10,
        "rolling_profitable_window_ratio": base["rolling_summary"]["profitable_window_ratio"] >= 0.50,
        "oos_to_is_return_ratio": base["oos_to_is_return_ratio"] >= 0.25,
        "holdout_return_positive": base["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor": _pf(base["holdout"]["profit_factor"]) >= 1.10,
        "holdout_drawdown": base["holdout"]["max_drawdown_percent"] <= 10.0,
        "stress_1_5x_nonnegative": scenarios["stress_1_5x_cost"]["holdout"]["period_return"] >= 0.0,
        "stress_2x_nonnegative": scenarios["stress_2x_cost"]["holdout"]["period_return"] >= 0.0,
        "gap_reversal_edge_positive": (
            base["research"]["mean_gap_reversal_edge"] > 0.0
            and base["holdout"]["mean_gap_reversal_edge"] > 0.0
        ),
    }
    report = {
        "schema_version": 1,
        "trial_id": "T-2026-09-24-021",
        "status": "COMPLETED",
        "research_only": True,
        "selection_used": False,
        "parameter_search_used": False,
        "data_scope": {
            "market_assets": list(ASSETS),
            "market_candles_per_asset": TARGET_COUNT,
            "market_manifest_fingerprint": manifest["manifest_fingerprint"],
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint_validation_set": True,
        },
        "policy": {
            "signal": "long after negative overnight gap, short after positive overnight gap, flat at zero",
            "weights": {symbol: 1.0 / len(ASSETS) for symbol in ASSETS},
            "gross_exposure_cap": 1.0,
            "price_field": "adjusted OHLC reconstructed from Yahoo adjusted close factors",
        },
        "methodology": {
            "execution": "current_open -> current_close after observing current opening price",
            "cost_basis": "0.10% fee + 0.05% slippage per turnover unit",
            "entry_exit_turnover": True,
            "cost_scenarios": ["base", "stress_1_5x_cost", "stress_2x_cost"],
            "holdout_used_for_selection": False,
            "strategy_variants": 1,
            "parameter_search": False,
        },
        "scenarios": scenarios,
        "decision": {"checks": checks, "all_checks_passed": all(checks.values())},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
    }
    report["report_fingerprint"] = _fp(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return report


def _pf(value: float | str) -> float:
    return float("inf") if value == "inf" else float(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--market-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_validation(
        data_dir=Path(args.data_dir),
        market_manifest=Path(args.market_manifest),
        output=Path(args.output),
    )
    print("OPEN_CLOSE_GAP_STATUS:", report["status"])
    print("OPEN_CLOSE_GAP_DECISION:", json.dumps(report["decision"], sort_keys=True))
    print("OPEN_CLOSE_GAP_SCENARIOS:", json.dumps(report["scenarios"], sort_keys=True))
    print("OPEN_CLOSE_GAP_REPORT_FINGERPRINT:", report["report_fingerprint"])


if __name__ == "__main__":
    main()
