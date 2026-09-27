"""Q039 fixed price-only alpha PIT mutation harness."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


SYMBOLS = ("IVE", "IWL", "DLN", "DHS", "DON", "DES", "USRT", "ITB")
DECISION_STEP = 113
MIN_HISTORY = 273


@dataclass(frozen=True)
class Bar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def _fp(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load(root: Path) -> dict[str, list[Bar]]:
    assets: dict[str, list[Bar]] = {}
    for symbol in SYMBOLS:
        path = root / symbol / "1d.csv"
        rows: list[Bar] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows.append(
                    Bar(
                        timestamp=row["timestamp"],
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                    )
                )
        if len(rows) != 3500:
            raise ValueError(f"{symbol}: expected 3500 rows, got {len(rows)}")
        if any(rows[i].timestamp >= rows[i + 1].timestamp for i in range(len(rows) - 1)):
            raise ValueError(f"{symbol}: timestamps not strictly increasing")
        assets[symbol] = rows
    return assets


def _returns(closes: list[float]) -> list[float]:
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]


def _a1_tsm_consensus(closes: list[float], index: int) -> int:
    if index < 252:
        return 0
    score = 0
    for lookback in (21, 63, 252):
        change = closes[index] / closes[index - lookback] - 1.0
        score += 1 if change > 0 else -1 if change < 0 else 0
    return 1 if score > 0 else -1 if score < 0 else 0


def _anchor(index: int) -> int:
    return index - 21


def _beta(asset_returns: list[float], market_returns: list[float]) -> float:
    if len(asset_returns) != len(market_returns) or not asset_returns:
        return 0.0
    asset_mean = sum(asset_returns) / len(asset_returns)
    market_mean = sum(market_returns) / len(market_returns)
    variance = sum((value - market_mean) ** 2 for value in market_returns)
    if variance <= 0:
        return 0.0
    covariance = sum(
        (asset - asset_mean) * (market - market_mean)
        for asset, market in zip(asset_returns, market_returns)
    )
    return covariance / variance


def _beta_inputs(
    closes: dict[str, list[float]],
    index: int,
) -> tuple[dict[str, float], dict[str, list[float]], int]:
    anchor = _anchor(index)
    if anchor < 273:
        return {}, {}, 0

    returns = {symbol: _returns(series) for symbol, series in closes.items()}
    start = anchor - 273
    end = anchor - 21
    market = [
        sum(returns[symbol][cursor] for symbol in SYMBOLS) / len(SYMBOLS)
        for cursor in range(start, end)
    ]
    betas = {
        symbol: _beta(returns[symbol][start:end], market)
        for symbol in SYMBOLS
    }
    return betas, returns, len(market)


def _a2_cs_top2(
    closes: dict[str, list[float]],
    index: int,
) -> tuple[str, ...]:
    anchor = _anchor(index)
    if anchor < 252:
        return ()
    scores = {
        symbol: series[anchor] / series[anchor - 252] - 1.0
        for symbol, series in closes.items()
    }
    return tuple(sorted(scores, key=lambda symbol: (-scores[symbol], symbol))[:2])


def _a3_residual_top2(
    closes: dict[str, list[float]],
    index: int,
) -> tuple[str, ...]:
    betas, returns, sample_size = _beta_inputs(closes, index)
    if sample_size < 252:
        return ()
    anchor = _anchor(index)
    start = anchor - 273
    end = anchor - 21
    market = [
        sum(returns[symbol][cursor] for symbol in SYMBOLS) / len(SYMBOLS)
        for cursor in range(start, end)
    ]
    scores: dict[str, float] = {}
    for symbol in SYMBOLS:
        residuals = [
            asset_return - betas[symbol] * market_return
            for asset_return, market_return
            in zip(returns[symbol][start:end], market)
        ]
        scores[symbol] = sum(residuals)
    return tuple(sorted(scores, key=lambda symbol: (-scores[symbol], symbol))[:2])


def _a5_low_beta_top2(
    closes: dict[str, list[float]],
    index: int,
) -> tuple[str, ...]:
    betas, _, sample_size = _beta_inputs(closes, index)
    if sample_size < 252:
        return ()
    return tuple(sorted(SYMBOLS, key=lambda symbol: (betas[symbol], symbol))[:2])


def _signals(assets: dict[str, list[Bar]], index: int) -> dict:
    closes = {
        symbol: [bar.close for bar in bars]
        for symbol, bars in assets.items()
    }
    return {
        "A1_TSM_CONSENSUS": {
            symbol: _a1_tsm_consensus(closes[symbol], index)
            for symbol in SYMBOLS
        },
        "A2_CS_MOMENTUM_TOP2": _a2_cs_top2(closes, index),
        "A3_RESIDUAL_MOMENTUM_TOP2": _a3_residual_top2(closes, index),
        "A5_LOW_BETA_TOP2": _a5_low_beta_top2(closes, index),
    }


def _mutate(
    assets: dict[str, list[Bar]],
    index: int,
    mode: str,
) -> dict[str, list[Bar]]:
    output = {
        symbol: list(bars)
        for symbol, bars in assets.items()
    }
    for symbol, series in output.items():
        for cursor in range(index + 1, len(series)):
            bar = series[cursor]
            if mode == "future":
                series[cursor] = Bar(
                    bar.timestamp,
                    bar.open * 0.2,
                    bar.high * 1.3,
                    bar.low * 0.4,
                    bar.close * 1.7,
                    bar.volume,
                )
            elif mode == "next" and cursor == index + 1:
                series[cursor] = Bar(
                    bar.timestamp,
                    bar.open * 9.0,
                    bar.high * 9.0,
                    bar.low * 0.1,
                    bar.close * 0.1,
                    bar.volume,
                )
    return output


def run(root: Path, output: Path) -> dict:
    assets = _load(root)
    checks = []
    length = len(next(iter(assets.values())))

    for index in range(MIN_HISTORY, length - 1, DECISION_STEP):
        original = _signals(assets, index)
        future = _signals(_mutate(assets, index, "future"), index)
        if original != future:
            raise AssertionError(
                f"future mutation changed price-only alpha signal at {index}"
            )
        next_session = _signals(_mutate(assets, index, "next"), index)
        if original != next_session:
            raise AssertionError(
                f"next-session OHLC mutation changed price-only alpha signal at {index}"
            )
        checks.append({"index": index, "signals": original})

    result = {
        "schema_version": "1.0",
        "trial_id": "T-2026-09-27-059",
        "status": "PIT_PASSED",
        "universe": "validation_2026_09_27_q039_price_only_alpha_pit",
        "symbols": list(SYMBOLS),
        "checked_decision_points": len(checks),
        "mechanisms": [
            "A1_TSM_CONSENSUS",
            "A2_CS_MOMENTUM_TOP2",
            "A3_RESIDUAL_MOMENTUM_TOP2",
            "A5_LOW_BETA_TOP2",
        ],
        "future_mutation_checks_passed": True,
        "next_session_mutation_checks_passed": True,
        "performance_evaluation": False,
        "oos_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "governance": {
            "performance_trial_authorized": False,
            "automatic_promotion": False,
            "parameter_search": False,
            "family_search": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "checks_fingerprint": _fp(checks),
    }
    result["report_fingerprint"] = _fp(result)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Q039_PRICE_ONLY_ALPHA_PIT_STATUS:", result["status"])
    print("CHECKED_DECISION_POINTS:", result["checked_decision_points"])
    print("REPORT_FINGERPRINT:", result["report_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(Path(args.universe_root), Path(args.output))
