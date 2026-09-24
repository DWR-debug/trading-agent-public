"""Trial 014 validation: pre-registered long/short and leverage control.

Research-only. No optimization, candidate selection, production mutation or orders.
The same SMA 50/200 signal is evaluated as long/flat and symmetric long/short
under fixed 1x, 1.5x, 2x and 3x margin leverage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation.literature_strategy_lab import load_bars
from config import settings
from research.asset_universes import get_universe
from research.leverage_model import LeverageConfig, portfolio_period_return
from research.long_short_strategies import build_signed_exposure, sma_50_200_long_short_signal
from research.protocol import dataset_fingerprint

UNIVERSE = "validation_2026_09_24_fourteenth_leverage"
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
TRADING_COST = FEE_RATE + SLIPPAGE_RATE
TARGET_ANNUALIZED_VOL = 0.10
VOLATILITY_WINDOW = 63
REBALANCE_PERIODS = 21
LEVERAGE_VARIANTS = (1.0, 1.5, 2.0, 3.0)


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(UNIVERSE)
    symbols = tuple(item["symbol"] for item in manifest.get("datasets", []))
    if manifest.get("universe") != UNIVERSE or symbols != universe.symbols:
        raise ValueError("Manifest does not match eighth leverage universe.")
    if manifest.get("target_count") != TARGET_COUNT or manifest.get("source") != "yahoo_chart":
        raise ValueError("Unexpected Trial-014 data source/count.")
    safety = manifest.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError("Manifest safety contract violated.")
    return manifest


def _assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    assets = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(data_dir / symbol / "1d.csv", expected_count=int(item["candle_count"]))
        if len(bars) != TARGET_COUNT or dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: dataset identity/fingerprint mismatch.")
        assets[symbol] = bars
    common = set.intersection(*[{bar.timestamp for bar in bars} for bars in assets.values()])
    if len(common) != TARGET_COUNT:
        raise ValueError(f"Expected {TARGET_COUNT} common candles, got {len(common)}.")
    ordered = sorted(common)
    return {symbol: tuple({bar.timestamp: bar for bar in bars}[ts] for ts in ordered) for symbol, bars in assets.items()}


def _normalized_weights(assets: dict[str, tuple], *, long_short: bool) -> tuple[dict[str, float], ...]:
    symbols = tuple(assets)
    lengths = {len(bars) for bars in assets.values()}
    if lengths != {TARGET_COUNT}:
        raise ValueError("All assets must have exactly 3500 candles.")
    raw = {}
    for symbol, bars in assets.items():
        closes = tuple(bar.close for bar in bars)
        signal = sma_50_200_long_short_signal(closes)
        if not long_short:
            signal = tuple(1 if value > 0 else 0 for value in signal)
        raw[symbol] = build_signed_exposure(
            closes,
            signal,
            target_annualized_vol=TARGET_ANNUALIZED_VOL,
            volatility_window=VOLATILITY_WINDOW,
            gross_exposure_cap=1.0,
            rebalance_periods=REBALANCE_PERIODS,
        )
    weights = []
    for index in range(TARGET_COUNT):
        gross = sum(abs(raw[symbol][index]) for symbol in symbols)
        normalizer = min(1.0, 1.0 / gross) if gross > 0.0 else 0.0
        weights.append({symbol: raw[symbol][index] * normalizer for symbol in symbols})
    return tuple(weights)


def _portfolio_rows(assets: dict[str, tuple], weights: tuple[dict[str, float], ...]) -> tuple[dict, ...]:
    symbols = tuple(assets)
    rows = []
    previous = {symbol: 0.0 for symbol in symbols}
    for index in range(TARGET_COUNT - 2):
        base_return = 0.0
        turnover = 0.0
        short_exposure = 0.0
        gross_exposure = 0.0
        current = weights[index]
        for symbol in symbols:
            bars = assets[symbol]
            market_return = bars[index + 2].open / bars[index + 1].open - 1.0
            weight = current[symbol]
            base_return += weight * market_return
            turnover += abs(weight - previous[symbol])
            gross_exposure += abs(weight)
            short_exposure += max(0.0, -weight)
            previous[symbol] = weight
        rows.append({
            "timestamp": assets[symbols[0]][index + 2].timestamp,
            "base_return": base_return,
            "turnover": turnover,
            "gross_exposure": gross_exposure,
            "short_exposure": short_exposure,
        })
    if len(rows) != EXPECTED_RETURNS:
        raise ValueError(f"Expected {EXPECTED_RETURNS} portfolio returns, got {len(rows)}.")
    return tuple(rows)


EXPECTED_RETURNS = TARGET_COUNT - 2


def _simulate(rows: tuple[dict, ...], multiple: float, *, trading_multiplier: float, financing: float, borrow: float) -> dict:
    underlying = tuple(row["base_return"] for row in rows)
    gross = tuple(row["gross_exposure"] for row in rows)
    short = tuple(row["short_exposure"] for row in rows)
    leverage = LeverageConfig(
        multiple=multiple,
        financing_rate_annual=financing,
        short_borrow_rate_annual=borrow,
    )
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    min_equity = 1.0
    gross_profit = 0.0
    gross_loss = 0.0
    net_returns = []
    ruined = False
    for index, row in enumerate(rows):
        net_return = portfolio_period_return(
            row["base_return"],
            row["gross_exposure"],
            row["short_exposure"],
            leverage,
        )
        trade_cost = (
            TRADING_COST
            * trading_multiplier
            * multiple
            * row["turnover"]
        )
        net_return -= trade_cost
        if ruined:
            net_return = 0.0
        else:
            new_equity = equity * (1.0 + net_return)
            if new_equity <= 0.0:
                equity = 0.0
                ruined = True
                net_return = -1.0
            else:
                equity = new_equity
        min_equity = min(min_equity, equity)
        peak = max(peak, equity)
        if peak > 0.0:
            max_dd = max(max_dd, 1.0 - equity / peak)
        if net_return > 0.0:
            gross_profit += net_return
        elif net_return < 0.0:
            gross_loss -= net_return
        net_returns.append(net_return)
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else ("inf" if gross_profit > 0 else 0.0)
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "minimum_equity": min_equity,
        "profit_factor": profit_factor,
        "ruined": ruined,
        "maximum_gross_exposure": max(
            (row["gross_exposure"] * multiple for row in rows),
            default=0.0,
        ),
        "maximum_short_exposure": max(
            (row["short_exposure"] * multiple for row in rows),
            default=0.0,
        ),
        "returns": tuple(net_returns),
    }


def _stats(returns: tuple[float, ...]) -> dict:
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    gp = gl = 0.0
    for value in returns:
        if value <= -1.0:
            equity = 0.0
        else:
            equity *= 1.0 + value
        peak = max(peak, equity)
        if peak > 0.0:
            max_dd = max(max_dd, 1.0 - equity / peak)
        if value > 0:
            gp += value
        elif value < 0:
            gl -= value
    pf = gp / gl if gl > 0 else ("inf" if gp > 0 else 0.0)
    return {"period_return": equity - 1.0, "max_drawdown_percent": max_dd * 100.0, "profit_factor": pf}


def _summary(returns: tuple[float, ...]) -> dict:
    windows = []
    width = RESEARCH_COUNT // 5
    start = 0
    for i in range(5):
        end = RESEARCH_COUNT if i == 4 else start + width
        window = _stats(returns[start:end])
        window["window_index"] = i + 1
        windows.append(window)
        start = end
    gp = sum(value for value in returns[:RESEARCH_COUNT] if value > 0)
    gl = -sum(value for value in returns[:RESEARCH_COUNT] if value < 0)
    pf = gp / gl if gl > 0 else ("inf" if gp > 0 else 0.0)
    return {
        "windows": windows,
        "profitable_window_ratio": sum(item["period_return"] > 0 for item in windows) / len(windows),
        "research_rolling_profit_factor": pf,
        "research_average_window_drawdown_percent": sum(item["max_drawdown_percent"] for item in windows) / len(windows),
    }


def _variant(rows, multiple: float) -> dict:
    results = {}
    for name, trading_multiplier, financing, borrow in (
        ("base", 1.0, 0.0, 0.0),
        ("realistic_stress", 1.5, 0.05, 0.05),
        ("adverse_stress", 2.0, 0.10, 0.10),
    ):
        result = _simulate(rows, multiple, trading_multiplier=trading_multiplier, financing=financing, borrow=borrow)
        research = result["returns"][:RESEARCH_COUNT]
        holdout = result["returns"][RESEARCH_COUNT:RESEARCH_COUNT + HOLDOUT_COUNT]
        results[name] = {
            "research": _stats(research),
            "holdout": _stats(holdout),
            "research_rolling": _summary(result["returns"]),
            "ruined": result["ruined"],
        }
    return results


def _gate(metrics: dict) -> bool:
    pf = metrics["profit_factor"]
    pf_value = float("inf") if pf == "inf" else float(pf)
    return (
        not metrics.get("ruined", False)
        and metrics["period_return"] > 0.0
        and metrics["max_drawdown_percent"] <= settings.MAX_DRAWDOWN_PERCENT
        and pf_value >= 1.10
    )


def run_validation(data_dir: Path, manifest_path: Path, output_path: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    manifest = _manifest(manifest_path)
    assets = _assets(data_dir, manifest)
    universe_symbols = set(get_universe(UNIVERSE).symbols)
    if set(assets) != universe_symbols:
        raise ValueError("Asset set does not match registered universe.")
    long_flat = _normalized_weights(assets, long_short=False)
    long_short = _normalized_weights(assets, long_short=True)
    rows_long_flat = _portfolio_rows(assets, long_flat)
    rows_long_short = _portfolio_rows(assets, long_short)

    variants = {}
    variants["long_flat_1x_margin"] = _variant(rows_long_flat, 1.0)
    for multiple in LEVERAGE_VARIANTS:
        variants[f"long_short_{multiple:g}x_margin"] = _variant(rows_long_short, multiple)

    report = {
        "schema_version": 1,
        "diagnostic_type": "trial_014_long_short_leverage_validation",
        "status": "COMPLETED",
        "source": {
            "universe": UNIVERSE,
            "symbols": list(get_universe(UNIVERSE).symbols),
            "manifest_fingerprint": manifest["manifest_fingerprint"],
            "target_candles_per_asset": TARGET_COUNT,
            "common_candle_count": TARGET_COUNT,
            "common_return_count": EXPECTED_RETURNS,
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint_validation_set": True,
        },
        "methodology": {
            "signal": "SMA 50/200",
            "baseline": "long/flat 1x",
            "long_short_variants": [f"{x:g}x" for x in LEVERAGE_VARIANTS],
            "volatility_target_annualized": TARGET_ANNUALIZED_VOL,
            "volatility_window_sessions": VOLATILITY_WINDOW,
            "rebalance_periods": REBALANCE_PERIODS,
            "execution": "close(t) decision -> next-session open -> following-open return",
            "optimization_used": False,
            "selection_used": False,
            "holdout_used_for_selection": False,
            "trading_cost": "0.10% fee + 0.05% slippage",
            "stress_assumptions": {
                "realistic_stress": "1.5x trading friction + 5% annual financing + 5% annual short borrow",
                "adverse_stress": "2x trading friction + 10% annual financing + 10% annual short borrow",
            },
        },
        "variants": variants,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
    }
    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_validation(Path(args.data_dir), Path(args.manifest), Path(args.output))
    print("EIGHTH_VALIDATION_STATUS:", report["status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    for name, scenarios in report["variants"].items():
        base = scenarios["base"]
        print(name, "RESEARCH_RETURN=", base["research"]["period_return"], "RESEARCH_DD=", base["research"]["max_drawdown_percent"], "HOLDOUT_RETURN=", base["holdout"]["period_return"], "HOLDOUT_DD=", base["holdout"]["max_drawdown_percent"], "HOLDOUT_PF=", base["holdout"]["profit_factor"] )


if __name__ == "__main__":
    main()
