"""Preregistered, research-only Cross-Asset Network Momentum laboratory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import settings
from research.protocol import dataset_fingerprint

ROOT = Path(__file__).resolve().parents[1]

TRIAL_ID = "T-2026-09-24-039"
UNIVERSE = "validation_2026_09_24_network_momentum_t039"
SYMBOLS = (
    "EIRL", "ENZL", "NORW", "EDEN", "FXF", "FXC",
    "CEW", "EIDO", "SCHO", "MINT", "FTGC", "RWX",
)
REQUESTED_CANDLES = 3520
COMMON_CANDLES = 3500
RESEARCH_RETURNS = 2798
HOLDOUT_RETURNS = 700

OWN_LOOKBACK = 252
SKIP = 21
PEER_LAG = 21
CORR_LOOKBACK = 252
VOL_WINDOW = 60
TARGET_VOL = 0.10
REBALANCE = 21
BLEND_WEIGHT = 0.50
MAX_GROSS_EXPOSURE = settings.MAX_LEVERAGE

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)

DEFAULT_PREREGISTRATION = (
    ROOT
    / "research"
    / "preregistrations"
    / "trial_039_network_momentum_2026_09_24.json"
)


def _activate_preregistration(
    preregistration_path: str | Path,
) -> dict:
    """Load and validate the fixed mechanism contract for a single trial."""
    global TRIAL_ID, UNIVERSE, SYMBOLS
    global REQUESTED_CANDLES, COMMON_CANDLES
    global RESEARCH_RETURNS, HOLDOUT_RETURNS

    path = Path(preregistration_path)
    if not path.is_absolute():
        path = ROOT / path
    spec = json.loads(path.read_text(encoding="utf-8"))

    if spec.get("research_family") not in {
        "cross_asset_network_momentum",
        "cross_asset_network_momentum_repair",
    }:
        raise ValueError("T039/T040 Network Momentum preregistration required.")

    rules = spec["rule"]
    expected = {
        "own_trend_lookback": OWN_LOOKBACK,
        "skip": SKIP,
        "peer_lag": PEER_LAG,
        "correlation_lookback": CORR_LOOKBACK,
        "blend_weight": BLEND_WEIGHT,
    }
    actual = {
        "own_trend_lookback": int(
            rules.get("own_trend_lookback", 252)
        ),
        "skip": int(
            rules.get("skip", 21)
        ),
        "peer_lag": int(
            rules.get("peer_lag", rules.get("peer_trend_lag", 21))
        ),
        "correlation_lookback": int(
            rules["correlation_lookback"]
        ),
        "blend_weight": float(
            rules.get("blend_weight", 0.50)
        ),
    }
    if actual != expected:
        raise ValueError(
            "Preregistration changes the fixed Network Momentum mechanism."
        )

    symbols = tuple(spec["symbols"])
    if len(symbols) != 12 or len(symbols) != len(set(symbols)):
        raise ValueError("Network Momentum requires exactly 12 unique symbols.")

    if rules.get("positive_links_only") is not True:
        raise ValueError("Network Momentum requires positive links only.")
    if spec.get("execution", {}).get("decision") not in {None, "monthly close"}:
        raise ValueError("Network Momentum requires monthly-close decisions.")
    TRIAL_ID = str(spec["trial_id"])
    UNIVERSE = str(spec["universe"])
    SYMBOLS = symbols
    REQUESTED_CANDLES = int(spec["requested_candles"])
    COMMON_CANDLES = int(spec["target_candles"])
    split = spec["split"]
    research_returns = split.get("research_return_periods")
    if research_returns is None:
        research_returns = split["pit_research_return_periods"]
    holdout_returns = split.get("holdout_return_periods")
    if holdout_returns is None:
        holdout_returns = split["holdout_candles"]

    RESEARCH_RETURNS = int(research_returns)
    HOLDOUT_RETURNS = int(holdout_returns)

    if REQUESTED_CANDLES != 3520:
        raise ValueError("Network Momentum data contract requires 3520 candles.")
    if COMMON_CANDLES != 3500:
        raise ValueError("Network Momentum common-calendar target must be 3500.")
    if RESEARCH_RETURNS != 2798 or HOLDOUT_RETURNS != 700:
        raise ValueError("Network Momentum split contract must be 2798/700.")

    return spec


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        _canonical(value).encode("utf-8")
    ).hexdigest()


def _load_csv(path: Path) -> tuple[Bar, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = (
            "timestamp", "open", "high", "low", "close", "volume"
        )
        if tuple(reader.fieldnames or ()) != required:
            raise ValueError(f"Ungültige Spalten in {path}")

        bars = tuple(
            Bar(
                timestamp=datetime.fromisoformat(
                    row["timestamp"].replace("Z", "+00:00")
                ),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            for row in reader
        )

    if len(bars) != REQUESTED_CANDLES:
        raise ValueError(
            f"{path}: {len(bars)} statt {REQUESTED_CANDLES} Candles"
        )
    return bars


def _load_snapshot(preflight_path: Path) -> dict[str, tuple[Bar, ...]]:
    payload = json.loads(
        preflight_path.read_text(encoding="utf-8")
    )
    if payload.get("trial_id") != TRIAL_ID:
        raise ValueError("Coverage-Preflight gehört nicht zur aktivierten Trial-ID.")
    if payload.get("status") != "coverage_passed":
        raise ValueError(
            f"{TRIAL_ID}-Forschung ist ohne Coverage-Pass gesperrt."
        )

    snapshot = payload.get("data_snapshot") or {}
    datasets = {
        item["symbol"]: item
        for item in snapshot.get("datasets", [])
    }
    if tuple(datasets) != SYMBOLS:
        raise ValueError(
            "Coverage-Snapshot-Symbole weichen von T039 ab."
        )

    assets: dict[str, tuple[Bar, ...]] = {}
    for symbol in SYMBOLS:
        item = datasets[symbol]
        bars = _load_csv(ROOT / item["path"])
        if item.get("candle_count") != len(bars):
            raise ValueError(f"{symbol}: Snapshot-Count stimmt nicht.")
        if item.get("fingerprint") != dataset_fingerprint(bars):
            raise ValueError(
                f"{symbol}: Snapshot-Fingerprint stimmt nicht."
            )
        assets[symbol] = bars

    return assets


def _align(
    assets: dict[str, tuple[Bar, ...]],
) -> dict[str, tuple[Bar, ...]]:
    common = set.intersection(
        *[
            {bar.timestamp for bar in bars}
            for bars in assets.values()
        ]
    )
    if len(common) < COMMON_CANDLES:
        raise ValueError(
            f"Zu wenige gemeinsame Candles: {len(common)}"
        )

    timestamps = sorted(common)[-COMMON_CANDLES:]
    aligned: dict[str, tuple[Bar, ...]] = {}
    for symbol, bars in assets.items():
        by_timestamp = {
            bar.timestamp: bar
            for bar in bars
        }
        aligned[symbol] = tuple(
            by_timestamp[timestamp]
            for timestamp in timestamps
        )
    return aligned


def _month_end_indices(
    bars: tuple[Bar, ...],
) -> set[int]:
    result: set[int] = set()
    previous_key = None
    previous_index = None

    for index, bar in enumerate(bars):
        key = (bar.timestamp.year, bar.timestamp.month)
        if (
            previous_key is not None
            and key != previous_key
        ):
            result.add(previous_index)

        previous_key = key
        previous_index = index

    if previous_index is not None:
        result.add(previous_index)

    return result


def _trend_returns(closes: list[float]) -> list[float]:
    result = [0.0] * len(closes)
    for index in range(OWN_LOOKBACK, len(closes)):
        end_index = index - SKIP
        result[index] = (
            closes[end_index] / closes[index - OWN_LOOKBACK]
            - 1.0
        )
    return result


def _trend_signals(
    trend: list[float],
) -> list[int]:
    return [
        1 if value > 0.0 else
        -1 if value < 0.0 else
        0
        for value in trend
    ]


def _prefix(values: list[float]) -> list[float]:
    output = [0.0]
    total = 0.0
    for value in values:
        total += value
        output.append(total)
    return output


def _corr_from_prefix(
    px: list[float],
    py: list[float],
    px2: list[float],
    py2: list[float],
    pxy: list[float],
    start_x: int,
    end_x: int,
    start_y: int,
    end_y: int,
) -> float:
    n = end_x - start_x
    if n < 2 or (end_y - start_y) != n:
        return 0.0

    sx = px[end_x] - px[start_x]
    sy = py[end_y] - py[start_y]
    sx2 = px2[end_x] - px2[start_x]
    sy2 = py2[end_y] - py2[start_y]
    sxy = pxy[end_x] - pxy[start_x]

    var_x = max(
        0.0,
        sx2 - sx * sx / n,
    )
    var_y = max(
        0.0,
        sy2 - sy * sy / n,
    )
    if var_x <= 1e-18 or var_y <= 1e-18:
        return 0.0

    covariance = (
        sxy - sx * sy / n
    )
    correlation = covariance / math.sqrt(
        var_x * var_y
    )
    return max(-1.0, min(1.0, correlation))


def _pair_correlations(
    target: list[float],
    peer: list[float],
) -> list[float]:
    px = _prefix(target)
    py = _prefix(peer)
    px2 = _prefix(
        [value * value for value in target]
    )
    py2 = _prefix(
        [value * value for value in peer]
    )
    pxy = _prefix(
        [a * b for a, b in zip(target, peer)]
    )

    result = [0.0] * len(target)
    first = CORR_LOOKBACK + PEER_LAG

    for index in range(first, len(target)):
        start = index - CORR_LOOKBACK
        result[index] = _corr_from_prefix(
            px,
            py,
            px2,
            py2,
            pxy,
            start,
            index,
            start - PEER_LAG,
            index - PEER_LAG,
        )

    return result


def _network_scores(
    trends: dict[str, list[float]],
    signals: dict[str, list[int]],
) -> dict[str, list[float]]:
    output = {
        symbol: [0.0] * len(trends[symbol])
        for symbol in SYMBOLS
    }

    for target in SYMBOLS:
        for peer in SYMBOLS:
            if target == peer:
                continue

            correlations = _pair_correlations(
                trends[target],
                trends[peer],
            )

            for index, correlation in enumerate(correlations):
                if correlation <= 0.0:
                    continue

                peer_index = index - PEER_LAG
                if peer_index < 0:
                    continue

                output[target][index] += (
                    correlation
                    * signals[peer][peer_index]
                )

    for target in SYMBOLS:
        for index in range(len(output[target])):
            total_weight = 0.0
            total_score = 0.0

            for peer in SYMBOLS:
                if peer == target:
                    continue

                correlation = _pair_correlations(
                    trends[target],
                    trends[peer],
                )[index]

                if correlation <= 0.0:
                    continue

                peer_index = index - PEER_LAG
                if peer_index < 0:
                    continue

                total_weight += correlation
                total_score += (
                    correlation
                    * signals[peer][peer_index]
                )

            output[target][index] = (
                total_score / total_weight
                if total_weight > 0.0
                else 0.0
            )

    return output


def _network_scores_fast(
    trends: dict[str, list[float]],
    signals: dict[str, list[int]],
) -> dict[str, list[float]]:
    correlations: dict[tuple[str, str], list[float]] = {}

    for target in SYMBOLS:
        for peer in SYMBOLS:
            if target != peer:
                correlations[(target, peer)] = _pair_correlations(
                    trends[target],
                    trends[peer],
                )

    output = {
        symbol: [0.0] * len(trends[symbol])
        for symbol in SYMBOLS
    }

    for target in SYMBOLS:
        for index in range(
            CORR_LOOKBACK + PEER_LAG,
            len(trends[target]),
        ):
            numerator = 0.0
            denominator = 0.0
            peer_index = index - PEER_LAG

            for peer in SYMBOLS:
                if peer == target:
                    continue
                correlation = correlations[(target, peer)][index]
                if correlation > 0.0:
                    denominator += correlation
                    numerator += (
                        correlation
                        * signals[peer][peer_index]
                    )

            if denominator > 0.0:
                output[target][index] = (
                    numerator / denominator
                )

    return output


def _sma_signals(
    closes: list[float],
) -> list[int]:
    output = [0] * len(closes)
    for index in range(199, len(closes)):
        fast = sum(
            closes[index - 49:index + 1]
        ) / 50.0
        slow = sum(
            closes[index - 199:index + 1]
        ) / 200.0
        output[index] = 1 if fast > slow else 0
    return output


def _close_returns(
    bars: tuple[Bar, ...],
) -> list[float]:
    returns = [0.0] * len(bars)
    for index in range(1, len(bars)):
        returns[index] = (
            bars[index].close
            / bars[index - 1].close
            - 1.0
        )
    return returns


def _annualized_vol(
    values: list[float],
    index: int,
) -> float:
    if index < VOL_WINDOW:
        return 0.0

    sample = values[index - VOL_WINDOW:index]
    mean = sum(sample) / len(sample)
    variance = sum(
        (value - mean) ** 2
        for value in sample
    ) / len(sample)
    return math.sqrt(variance) * math.sqrt(252.0)


def _covariance(
    values_by_symbol: dict[str, list[float]],
    active: list[str],
    index: int,
) -> dict[tuple[str, str], float]:
    if index < VOL_WINDOW:
        return {}

    window = {
        symbol: values_by_symbol[symbol][
            index - VOL_WINDOW:index
        ]
        for symbol in active
    }
    means = {
        symbol: sum(values) / len(values)
        for symbol, values in window.items()
    }

    output = {}
    for left in active:
        for right in active:
            output[(left, right)] = (
                sum(
                    (a - means[left])
                    * (b - means[right])
                    for a, b in zip(
                        window[left],
                        window[right],
                    )
                )
                / len(window[left])
                * 252.0
            )
    return output


def _target_weights(
    direction: dict[str, list[int]],
    returns_by_symbol: dict[str, list[float]],
    index: int,
) -> dict[str, float]:
    active = [
        symbol
        for symbol in SYMBOLS
        if direction[symbol][index] > 0
    ]

    if not active or index < VOL_WINDOW:
        return {
            symbol: 0.0
            for symbol in SYMBOLS
        }

    inverse_vol = {}
    for symbol in active:
        volatility = _annualized_vol(
            returns_by_symbol[symbol],
            index,
        )
        if volatility > 0.0:
            inverse_vol[symbol] = 1.0 / volatility

    if not inverse_vol:
        return {
            symbol: 0.0
            for symbol in SYMBOLS
        }

    total = sum(inverse_vol.values())
    base = {
        symbol: inverse_vol[symbol] / total
        for symbol in inverse_vol
    }

    covariance = _covariance(
        returns_by_symbol,
        list(base),
        index,
    )
    variance = sum(
        base[left]
        * base[right]
        * covariance[(left, right)]
        for left in base
        for right in base
    )
    portfolio_vol = math.sqrt(
        max(0.0, variance)
    )
    if portfolio_vol <= 0.0:
        scale = 0.0
    else:
        scale = TARGET_VOL / portfolio_vol

    scale = min(
        MAX_GROSS_EXPOSURE,
        scale,
    )
    return {
        symbol: base.get(symbol, 0.0) * scale
        for symbol in SYMBOLS
    }


def _stats(
    values: list[float],
) -> dict:
    if not values:
        return {
            "return": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": 0.0,
            "days": 0,
            "positive_days": 0,
        }

    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    positive_days = 0

    for value in values:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_drawdown = max(
            max_drawdown,
            1.0 - equity / peak,
        )

        if value > 0.0:
            gross_profit += value
            positive_days += 1
        elif value < 0.0:
            gross_loss -= value

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0.0
        else (
            "inf"
            if gross_profit > 0.0
            else 0.0
        )
    )
    return {
        "return": equity - 1.0,
        "max_drawdown": max_drawdown,
        "profit_factor": profit_factor,
        "days": len(values),
        "positive_days": positive_days,
    }


def _rolling(
    values: list[float],
) -> list[dict]:
    width = len(values) // 5
    output = []
    start = 0

    for index in range(5):
        end = (
            len(values)
            if index == 4
            else start + width
        )
        output.append(
            {
                "window": index + 1,
                "start": start,
                "end": end,
                **_stats(values[start:end]),
            }
        )
        start = end

    return output


def _pf(value: object) -> float:
    return (
        float("inf")
        if value == "inf"
        else float(value)
    )


def _run_returns(
    assets: dict[str, tuple[Bar, ...]],
    direction: dict[str, list[int]],
) -> list[float]:
    returns_by_symbol = {
        symbol: _close_returns(assets[symbol])
        for symbol in SYMBOLS
    }
    reference = next(iter(assets.values()))
    month_ends = _month_end_indices(reference)

    current = {
        symbol: 0.0
        for symbol in SYMBOLS
    }
    weights = [
        {symbol: 0.0 for symbol in SYMBOLS}
        for _ in reference
    ]

    for index in range(len(reference)):
        if index in month_ends:
            current = _target_weights(
                direction,
                returns_by_symbol,
                index,
            )
        weights[index] = dict(current)

    output_by_cost = {}

    for scenario, multiplier in COST_SCENARIOS:
        values = []
        previous = {
            symbol: 0.0
            for symbol in SYMBOLS
        }

        for decision in range(
            len(reference) - 2
        ):
            portfolio_return = 0.0
            turnover = 0.0

            for symbol in SYMBOLS:
                weight = weights[decision][symbol]
                market_return = (
                    assets[symbol][decision + 2].open
                    / assets[symbol][decision + 1].open
                    - 1.0
                )
                portfolio_return += (
                    weight * market_return
                )
                turnover += abs(
                    weight - previous[symbol]
                )
                previous[symbol] = weight

            values.append(
                portfolio_return
                - (
                    FEE_RATE
                    + SLIPPAGE_RATE
                )
                * multiplier
                * turnover
            )

        research = values[
            :RESEARCH_RETURNS
        ]
        holdout = values[
            RESEARCH_RETURNS:
            RESEARCH_RETURNS
            + HOLDOUT_RETURNS
        ]

        development_end = int(
            len(research) * 0.80
        )
        development = research[:development_end]
        oos = research[development_end:]

        rolling = _rolling(research)
        research_stats = _stats(research)
        oos_stats = _stats(oos)

        output_by_cost[scenario] = {
            "research": research_stats,
            "development": _stats(development),
            "oos": oos_stats,
            "oos_to_research_return_ratio": (
                (
                    oos_stats["return"]
                    / research_stats["return"]
                )
                if research_stats["return"] != 0.0
                else (
                    float("inf")
                    if oos_stats["return"] > 0.0
                    else 0.0
                )
            ),
            "rolling": rolling,
            "rolling_min_profit_factor": min(
                _pf(item["profit_factor"])
                for item in rolling
            ),
            "rolling_profitable_ratio": (
                sum(
                    item["return"] > 0.0
                    for item in rolling
                )
                / len(rolling)
            ),
            "rolling_average_drawdown": (
                sum(
                    item["max_drawdown"]
                    for item in rolling
                )
                / len(rolling)
            ),
            "holdout": _stats(holdout),
        }

    return output_by_cost


def _strategy(
    assets: dict[str, tuple[Bar, ...]],
    challenger: bool,
) -> dict:
    closes = {
        symbol: [
            bar.close
            for bar in assets[symbol]
        ]
        for symbol in SYMBOLS
    }
    trends = {
        symbol: _trend_returns(closes[symbol])
        for symbol in SYMBOLS
    }
    signals = {
        symbol: _trend_signals(trends[symbol])
        for symbol in SYMBOLS
    }

    if challenger:
        network = _network_scores_fast(
            trends,
            signals,
        )
        direction = {
            symbol: [
                1
                if (
                    BLEND_WEIGHT * signals[symbol][index]
                    + BLEND_WEIGHT * network[symbol][index]
                ) > 0.0
                else 0
                for index in range(len(trends[symbol]))
            ]
            for symbol in SYMBOLS
        }
    else:
        network = None
        direction = {
            symbol: _sma_signals(closes[symbol])
            for symbol in SYMBOLS
        }

    scenarios = _run_returns(
        assets,
        direction,
    )

    return {
        "direction_statistics": {
            symbol: {
                "long": sum(
                    value > 0
                    for value in direction[symbol]
                ),
                "flat": sum(
                    value == 0
                    for value in direction[symbol]
                ),
                "short": 0,
            }
            for symbol in SYMBOLS
        },
        "scenarios": scenarios,
        "network_score_range": (
            {
                symbol: {
                    "min": min(network[symbol]),
                    "max": max(network[symbol]),
                }
                for symbol in SYMBOLS
            }
            if network is not None
            else None
        ),
    }


def _compare(
    challenger: dict,
    control: dict,
) -> dict:
    left = challenger["scenarios"]["base"]
    right = control["scenarios"]["base"]
    return {
        "research_return_not_lower": (
            left["research"]["return"]
            >= right["research"]["return"]
        ),
        "research_drawdown_not_higher": (
            left["research"]["max_drawdown"]
            <= right["research"]["max_drawdown"]
        ),
        "research_profit_factor_not_lower": (
            _pf(left["research"]["profit_factor"])
            >= _pf(right["research"]["profit_factor"])
        ),
        "rolling_profitable_ratio_not_lower": (
            left["rolling_profitable_ratio"]
            >= right["rolling_profitable_ratio"]
        ),
        "holdout_return_not_lower": (
            left["holdout"]["return"]
            >= right["holdout"]["return"]
        ),
        "holdout_drawdown_not_higher": (
            left["holdout"]["max_drawdown"]
            <= right["holdout"]["max_drawdown"]
        ),
        "holdout_profit_factor_not_lower": (
            _pf(left["holdout"]["profit_factor"])
            >= _pf(right["holdout"]["profit_factor"])
        ),
    }


def _evaluate(
    challenger: dict,
    control: dict,
) -> dict:
    base = challenger["scenarios"]["base"]
    holdout_15 = challenger[
        "scenarios"]["stress_1_5x_cost"
    ]["holdout"]
    holdout_20 = challenger[
        "scenarios"]["stress_2x_cost"
    ]["holdout"]
    comparison = _compare(
        challenger,
        control,
    )

    gates = {
        "positive_research_return": (
            base["research"]["return"] > 0.0
        ),
        "research_max_drawdown_lte_10pct": (
            base["research"]["max_drawdown"] <= 0.10
        ),
        "research_profit_factor_gte_1_10": (
            _pf(base["research"]["profit_factor"])
            >= 1.10
        ),
        "rolling_profit_factor_gte_1_10": (
            base["rolling_min_profit_factor"] >= 1.10
        ),
        "profitable_rolling_windows_gte_50pct": (
            base["rolling_profitable_ratio"] >= 0.50
        ),
        "average_rolling_drawdown_lte_10pct": (
            base["rolling_average_drawdown"] <= 0.10
        ),
        "oos_to_research_return_ratio_gte_25pct": (
            base["oos_to_research_return_ratio"] >= 0.25
        ),
        "positive_holdout_return": (
            base["holdout"]["return"] > 0.0
        ),
        "holdout_profit_factor_gte_1_10": (
            _pf(base["holdout"]["profit_factor"])
            >= 1.10
        ),
        "holdout_max_drawdown_lte_10pct": (
            base["holdout"]["max_drawdown"] <= 0.10
        ),
        "holdout_return_nonnegative_1_5x_cost": (
            holdout_15["return"] >= 0.0
        ),
        "holdout_return_nonnegative_2x_cost": (
            holdout_20["return"] >= 0.0
        ),
        "non_deterioration_vs_fixed_candidate": all(
            comparison.values()
        ),
    }

    return {
        "passed": all(gates.values()),
        "gates": gates,
        "comparison": comparison,
    }


def run_trial(
    preflight_path: str | Path,
    output_path: str | Path,
    preregistration_path: str | Path = DEFAULT_PREREGISTRATION,
) -> dict:
    _activate_preregistration(preregistration_path)

    if settings.PAPER_ONLY is not True:
        raise RuntimeError("T039 requires PAPER_ONLY=True.")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError(
            "T039 requires LIVE_TRADING_ENABLED=False."
        )

    assets = _align(
        _load_snapshot(
            Path(preflight_path)
        )
    )
    challenger = _strategy(
        assets,
        challenger=True,
    )
    control = _strategy(
        assets,
        challenger=False,
    )
    evaluation = _evaluate(
        challenger,
        control,
    )

    report = {
        "trial_id": TRIAL_ID,
        "status": (
            "PASSED_NO_AUTO_PROMOTION"
            if evaluation["passed"]
            else "BLOCKED"
        ),
        "scientific_outcome": (
            "EVIDENCE_GATED_PASS"
            if evaluation["passed"]
            else "NO_PROMOTION_EVIDENCE"
        ),
        "source": {
            "universe": UNIVERSE,
            "symbols": list(SYMBOLS),
            "requested_candles": REQUESTED_CANDLES,
            "common_candles": COMMON_CANDLES,
            "research_return_count": RESEARCH_RETURNS,
            "holdout_return_count": HOLDOUT_RETURNS,
        },
        "methodology": {
            "own_trend_lookback": OWN_LOOKBACK,
            "skip": SKIP,
            "peer_lag": PEER_LAG,
            "correlation_lookback": CORR_LOOKBACK,
            "correlation_basis": (
                "continuous_252_21_trend_returns"
            ),
            "positive_links_only": True,
            "blend_weight": BLEND_WEIGHT,
            "volatility_window": VOL_WINDOW,
            "target_annual_volatility": TARGET_VOL,
            "max_gross_exposure": MAX_GROSS_EXPOSURE,
            "rebalance": "monthly",
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "cost_stress": [1.5, 2.0],
            "holdout_used_for_selection": False,
            "optimization_used": False,
            "parameter_search": False,
            "point_in_time": True,
            "execution": (
                "close_t_decision_then_next_open_to_following_open"
            ),
        },
        "challenger": challenger,
        "fixed_sma_control": control,
        "evaluation": evaluation,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    report["report_fingerprint"] = _fingerprint(
        report
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--preregistration",
        default=str(DEFAULT_PREREGISTRATION),
    )
    args = parser.parse_args()

    report = run_trial(
        args.coverage,
        args.output,
        args.preregistration,
    )
    print("T039_STATUS:", report["status"])
    print(
        "REPORT_FINGERPRINT:",
        report["report_fingerprint"],
    )


if __name__ == "__main__":
    main()
