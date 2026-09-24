"""Trial 034: fixed cointegration-gated ETF relative-value strategy.

Research-only. Exactly five pre-registered ETF pairs are tested. No pair search,
parameter optimization, holdout selection, production mutation or orders.

Method:
- monthly (21-session) eligibility refresh using 200-session ADF p-value < 0.05
  on the price ratio;
- daily ratio z-score on the same 200-session window;
- enter at |z| > 1.65;
- exit at |z| < 0.75;
- equal capital within each active pair, equal gross allocation across active
  pairs, so gross exposure is <= 1.0 and net exposure is 0.0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

from statsmodels.tsa.stattools import adfuller

from automation.candidate_validation_50_50_vol_budget import _yahoo_adjclose
from automation.literature_strategy_lab import load_bars
from config import settings
from research.asset_universes import get_universe, list_universes
from research.protocol import dataset_fingerprint
from validation.research_gates import ResearchGateConfig

TRIAL_ID = "T-2026-09-24-034"
UNIVERSE = "validation_2026_09_24_relative_value_etf_pairs_v3"

TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700

FORMATION_WINDOW = 200
Z_WINDOW = 200
REBALANCE_PERIOD = 21
ENTRY_Z = 1.65
EXIT_ABS_Z = 0.75
ADF_PVALUE = 0.05

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)

PAIR_SPECS = (
    ("VTWO", "IJR", "us_small_cap"),
    ("QQEW", "ONEQ", "nasdaq_equity"),
    ("EEMV", "SCHE", "emerging_markets"),
    ("IGIB", "SPIB", "investment_grade_corporates"),
    ("SCHP", "STIP", "us_tips"),
)

SYMBOLS = tuple(symbol for pair in PAIR_SPECS for symbol in pair[:2])


@dataclass(frozen=True)
class PairState:
    left: str
    right: str
    economic_group: str
    state_by_index: tuple[int, ...]
    eligible_by_index: tuple[bool, ...]
    z_by_index: tuple[float | None, ...]
    adf_pvalue_by_rebalance: tuple[tuple[int, float], ...]
    entry_count: int
    exit_count: int


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


def _pf(value: float | str) -> float:
    return float("inf") if value == "inf" else float(value)


def _load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(UNIVERSE)
    actual = tuple(item["symbol"] for item in data.get("datasets", []))
    expected = tuple(universe.symbols)

    if data.get("universe") != UNIVERSE or actual != expected:
        raise ValueError("Manifest passt nicht zu Trial 034.")
    if data.get("target_count") != TARGET_COUNT:
        raise ValueError("Trial 034 benötigt exakt 3.500 Candles je Symbol.")
    if data.get("source") != "yahoo_chart":
        raise ValueError("Unerwartete Datenquelle für Trial 034.")

    safety = data.get("safety", {})
    if (
        safety.get("paper_only") is not True
        or safety.get("live_trading_enabled") is not False
        or safety.get("orders_enabled") is not False
    ):
        raise RuntimeError("Paper-only-Sicherheitsvertrag im Manifest verletzt.")

    return data


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    assets: dict[str, tuple] = {}

    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if len(bars) != TARGET_COUNT:
            raise ValueError(
                f"{symbol}: {len(bars)} statt {TARGET_COUNT} Candles."
            )

        actual_fp = dataset_fingerprint(bars)
        if actual_fp != item["fingerprint"]:
            raise ValueError(f"{symbol}: Dataset-Fingerprint stimmt nicht.")

        assets[symbol] = bars

    if set(assets) != set(SYMBOLS):
        raise ValueError("Trial-034-Symbole fehlen oder wurden verändert.")

    common = set.intersection(
        *[{bar.timestamp for bar in bars} for bars in assets.values()]
    )
    if len(common) < TARGET_COUNT:
        raise ValueError(
            f"Gemeinsamer Kalender nur {len(common)} statt {TARGET_COUNT}."
        )

    selected = sorted(common)[-TARGET_COUNT:]

    aligned = {
        symbol: tuple(
            {bar.timestamp: bar for bar in bars}[timestamp]
            for timestamp in selected
        )
        for symbol, bars in assets.items()
    }

    if len(next(iter(aligned.values()))) != TARGET_COUNT:
        raise ValueError("Kalenderausrichtung hat die Zielhistorie verändert.")

    return aligned


def _ratio(left_bars: tuple, right_bars: tuple) -> list[float]:
    if len(left_bars) != len(right_bars):
        raise ValueError("Pair-Längen müssen identisch sein.")

    ratios = []
    for left, right in zip(left_bars, right_bars):
        if left.close <= 0.0 or right.close <= 0.0:
            raise ValueError("Nichtpositive Kurse im Pair.")
        ratios.append(left.close / right.close)
    return ratios


def _zscore(values: list[float]) -> float | None:
    if len(values) < Z_WINDOW:
        return None

    sample = values[-Z_WINDOW:]
    mean = sum(sample) / len(sample)
    variance = sum((value - mean) ** 2 for value in sample) / len(sample)
    standard_deviation = math.sqrt(variance)

    if standard_deviation <= 0.0:
        return None

    return (sample[-1] - mean) / standard_deviation


def _adf_pvalue(values: list[float]) -> float:
    if len(values) < FORMATION_WINDOW:
        raise ValueError("ADF-Formationperiode ist zu kurz.")

    statistic = adfuller(
        values[-FORMATION_WINDOW:],
        regression="c",
        autolag="AIC",
    )
    pvalue = float(statistic[1])

    if not math.isfinite(pvalue):
        raise ValueError("ADF-P-Wert ist nicht endlich.")

    return pvalue


def _transition_state(
    current_state: int,
    z_score: float | None,
    eligible: bool,
) -> int:
    if not eligible or z_score is None:
        return 0

    if current_state == 0:
        if z_score > ENTRY_Z:
            return -1
        if z_score < -ENTRY_Z:
            return 1
        return 0

    if abs(z_score) < EXIT_ABS_Z:
        return 0

    return current_state


def _pair_state(
    left_bars: tuple,
    right_bars: tuple,
    left: str,
    right: str,
    economic_group: str,
) -> PairState:
    ratios = _ratio(left_bars, right_bars)
    length = len(ratios)

    states: list[int] = []
    eligible: list[bool] = []
    z_scores: list[float | None] = []
    adf_records: list[tuple[int, float]] = []

    current_state = 0
    current_eligible = False
    entry_count = 0
    exit_count = 0
    previous_state = 0

    for index in range(length):
        if (
            index >= FORMATION_WINDOW - 1
            and index % REBALANCE_PERIOD == 0
        ):
            pvalue = _adf_pvalue(
                ratios[
                    index - FORMATION_WINDOW + 1 : index + 1
                ]
            )
            current_eligible = pvalue < ADF_PVALUE
            adf_records.append((index, pvalue))

            if not current_eligible:
                current_state = 0

        z_score = _zscore(
            ratios[: index + 1]
        )

        current_state = _transition_state(
            current_state=current_state,
            z_score=z_score,
            eligible=current_eligible,
        )

        if previous_state == 0 and current_state != 0:
            entry_count += 1
        elif previous_state != 0 and current_state == 0:
            exit_count += 1

        states.append(current_state)
        eligible.append(current_eligible)
        z_scores.append(z_score)
        previous_state = current_state

    return PairState(
        left=left,
        right=right,
        economic_group=economic_group,
        state_by_index=tuple(states),
        eligible_by_index=tuple(eligible),
        z_by_index=tuple(z_scores),
        adf_pvalue_by_rebalance=tuple(adf_records),
        entry_count=entry_count,
        exit_count=exit_count,
    )


def _build_pair_states(
    assets: dict[str, tuple],
) -> tuple[PairState, ...]:
    states = []
    for left, right, group in PAIR_SPECS:
        states.append(
            _pair_state(
                assets[left],
                assets[right],
                left,
                right,
                group,
            )
        )
    return tuple(states)


def _weights_from_states(
    pair_states: tuple[PairState, ...],
    index: int,
) -> dict[str, float]:
    active = [
        pair_state
        for pair_state in pair_states
        if pair_state.state_by_index[index] != 0
    ]

    weights = {symbol: 0.0 for symbol in SYMBOLS}
    if not active:
        return weights

    pair_gross = 1.0 / len(active)
    leg = 0.5 * pair_gross

    for pair_state in active:
        state = pair_state.state_by_index[index]
        if state == 1:
            weights[pair_state.left] += leg
            weights[pair_state.right] -= leg
        else:
            weights[pair_state.left] -= leg
            weights[pair_state.right] += leg

    return weights


def _simulate(
    assets: dict[str, tuple],
    pair_states: tuple[PairState, ...],
    multiplier: float,
) -> tuple[list[dict], dict[str, float]]:
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier
    realized: list[dict] = []
    previous_weights = {symbol: 0.0 for symbol in SYMBOLS}

    total_entries = 0
    total_exits = 0

    for index in range(0, len(next(iter(assets.values()))) - 2):
        target_weights = _weights_from_states(pair_states, index)

        next_open_index = index + 1
        realization_open_index = index + 2

        gross_return = 0.0
        gross_exposure = 0.0

        for symbol in SYMBOLS:
            weight = target_weights[symbol]
            bars = assets[symbol]
            asset_return = (
                bars[realization_open_index].open
                / bars[next_open_index].open
                - 1.0
            )
            gross_return += weight * asset_return
            gross_exposure += abs(weight)

        turnover = sum(
            abs(target_weights[symbol] - previous_weights[symbol])
            for symbol in SYMBOLS
        )
        cost = cost_rate * turnover
        net_return = gross_return - cost

        current_entries = sum(
            1
            for pair_state in pair_states
            if index > 0
            and pair_state.state_by_index[index - 1] == 0
            and pair_state.state_by_index[index] != 0
        )
        current_exits = sum(
            1
            for pair_state in pair_states
            if index > 0
            and pair_state.state_by_index[index - 1] != 0
            and pair_state.state_by_index[index] == 0
        )

        total_entries += current_entries
        total_exits += current_exits

        realized.append(
            {
                "index": index,
                "timestamp": assets[SYMBOLS[0]][realization_open_index].timestamp,
                "net_return": net_return,
                "gross_return": gross_return,
                "turnover": turnover,
                "gross_exposure": gross_exposure,
                "active_pair_count": sum(
                    pair_state.state_by_index[index] != 0
                    for pair_state in pair_states
                ),
                "entry_count": current_entries,
                "exit_count": current_exits,
            }
        )

        previous_weights = target_weights

    diagnostics = {
        "entry_count": float(total_entries),
        "exit_count": float(total_exits),
    }
    return realized, diagnostics


def _metrics(rows: list[dict], start: int, end: int) -> dict:
    segment = rows[start:end]
    if not segment:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "day_count": 0,
            "trade_count": 0,
            "positive_day_ratio": 0.0,
            "active_day_ratio": 0.0,
            "median_active_pair_count": 0.0,
            "average_gross_exposure": 0.0,
        }

    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    positive_days = 0
    active_days = 0
    trade_count = 0
    active_pairs = []
    gross_exposure = []

    for row in segment:
        value = float(row["net_return"])
        equity *= 1.0 + value
        peak = max(peak, equity)
        if peak > 0.0:
            max_dd = max(max_dd, 1.0 - equity / peak)

        if value > 0.0:
            gross_profit += value
            positive_days += 1
        elif value < 0.0:
            gross_loss -= value

        if row["gross_exposure"] > 0.0:
            active_days += 1

        trade_count += int(row["exit_count"])
        active_pairs.append(int(row["active_pair_count"]))
        gross_exposure.append(float(row["gross_exposure"]))

    if gross_loss > 0.0:
        profit_factor: float | str = gross_profit / gross_loss
    elif gross_profit > 0.0:
        profit_factor = "inf"
    else:
        profit_factor = 0.0

    active_pairs_sorted = sorted(active_pairs)
    median_active_pairs = active_pairs_sorted[
        len(active_pairs_sorted) // 2
    ]

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": profit_factor,
        "day_count": len(segment),
        "trade_count": trade_count,
        "positive_day_ratio": positive_days / len(segment),
        "active_day_ratio": active_days / len(segment),
        "median_active_pair_count": median_active_pairs,
        "average_gross_exposure": sum(gross_exposure) / len(gross_exposure),
    }


def _rolling_metrics(rows: list[dict]) -> tuple[list[dict], dict]:
    width = RESEARCH_COUNT // 5
    windows = []
    start = 0

    for index in range(5):
        end = RESEARCH_COUNT if index == 4 else start + width
        windows.append(
            {
                "window_index": index + 1,
                **_metrics(rows, start, end),
            }
        )
        start = end

    profitable_windows = sum(
        window["period_return"] > 0.0
        for window in windows
    )
    zero_trade_windows = sum(
        window["trade_count"] == 0
        for window in windows
    )

    research = rows[:RESEARCH_COUNT]
    values = [float(row["net_return"]) for row in research]
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)

    if gross_loss > 0.0:
        overall_pf: float | str = gross_profit / gross_loss
    elif gross_profit > 0.0:
        overall_pf = "inf"
    else:
        overall_pf = 0.0

    summary = {
        "window_count": len(windows),
        "profitable_windows": profitable_windows,
        "profitable_window_ratio": profitable_windows / len(windows),
        "zero_trade_windows": zero_trade_windows,
        "zero_trade_window_ratio": zero_trade_windows / len(windows),
        "overall_profit_factor": overall_pf,
        "total_trade_count": sum(
            window["trade_count"] for window in windows
        ),
        "total_net_return": _metrics(
            rows,
            0,
            RESEARCH_COUNT,
        )["period_return"],
        "average_drawdown_percent": sum(
            window["max_drawdown_percent"]
            for window in windows
        ) / len(windows),
    }

    return windows, summary


def _scenario(
    assets: dict[str, tuple],
    pair_states: tuple[PairState, ...],
    multiplier: float,
) -> dict:
    rows, diagnostics = _simulate(assets, pair_states, multiplier)

    research = _metrics(rows, 0, RESEARCH_COUNT)
    holdout = _metrics(
        rows,
        RESEARCH_COUNT,
        RESEARCH_COUNT + HOLDOUT_COUNT,
    )
    windows, rolling = _rolling_metrics(rows)

    oos_to_is = (
        holdout["period_return"] / research["period_return"]
        if research["period_return"] > 0.0
        else 0.0
    )

    return {
        "research": research,
        "holdout": holdout,
        "rolling_windows": windows,
        "rolling_summary": rolling,
        "oos_to_is_return_ratio": oos_to_is,
        "diagnostics": diagnostics,
    }


def _gates(
    scenarios: dict,
    config: ResearchGateConfig,
) -> dict:
    base = scenarios["base"]
    stress15 = scenarios["stress_1_5x_cost"]
    stress2 = scenarios["stress_2x_cost"]

    research = base["research"]
    holdout = base["holdout"]
    rolling = base["rolling_summary"]

    checks = {
        "research_return_positive": research["period_return"] > 0.0,
        "research_drawdown": (
            research["max_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "research_profit_factor": (
            _pf(research["profit_factor"])
            >= config.minimum_profit_factor
        ),
        "research_trade_count": (
            research["trade_count"]
            >= config.minimum_rolling_trades
        ),
        "rolling_total_return_positive": (
            rolling["total_net_return"] > 0.0
        ),
        "rolling_profit_factor": (
            _pf(rolling["overall_profit_factor"])
            >= config.minimum_profit_factor
        ),
        "rolling_profitable_window_ratio": (
            rolling["profitable_window_ratio"]
            >= config.minimum_profitable_window_ratio
        ),
        "rolling_zero_trade_window_ratio": (
            rolling["zero_trade_window_ratio"]
            <= config.maximum_zero_trade_window_ratio
        ),
        "rolling_average_drawdown": (
            rolling["average_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "oos_to_is_return_ratio": (
            base["oos_to_is_return_ratio"]
            >= config.minimum_oos_to_is_return_ratio
        ),
        "holdout_return_positive": holdout["period_return"] > 0.0,
        "holdout_profit_factor": (
            _pf(holdout["profit_factor"])
            >= config.minimum_profit_factor
        ),
        "holdout_drawdown": (
            holdout["max_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "holdout_trade_count": (
            holdout["trade_count"]
            >= config.minimum_holdout_trades
        ),
        "stress_1_5x_nonnegative": (
            stress15["holdout"]["period_return"] >= 0.0
        ),
        "stress_2x_nonnegative": (
            stress2["holdout"]["period_return"] >= 0.0
        ),
    }

    return {
        "checks": checks,
        "thresholds": {
            "minimum_profit_factor": config.minimum_profit_factor,
            "maximum_drawdown_percent": config.maximum_drawdown_percent,
            "minimum_profitable_window_ratio": config.minimum_profitable_window_ratio,
            "maximum_zero_trade_window_ratio": config.maximum_zero_trade_window_ratio,
            "minimum_oos_to_is_return_ratio": config.minimum_oos_to_is_return_ratio,
            "minimum_research_trades": config.minimum_rolling_trades,
            "minimum_holdout_trades": config.minimum_holdout_trades,
        },
        "all_relevant_checks_passed": all(checks.values()),
    }


def _pair_diagnostics(
    pair_states: tuple[PairState, ...],
) -> dict[str, dict]:
    result = {}

    for state in pair_states:
        eligible_count = sum(state.eligible_by_index)
        nonzero_z = [
            value
            for value in state.z_by_index
            if value is not None
        ]

        result[f"{state.left}/{state.right}"] = {
            "economic_group": state.economic_group,
            "adf_rebalance_count": len(state.adf_pvalue_by_rebalance),
            "adf_eligible_rebalance_ratio": (
                sum(
                    pvalue < ADF_PVALUE
                    for _, pvalue in state.adf_pvalue_by_rebalance
                )
                / len(state.adf_pvalue_by_rebalance)
                if state.adf_pvalue_by_rebalance
                else 0.0
            ),
            "eligible_day_ratio": eligible_count / len(state.eligible_by_index),
            "entry_count": state.entry_count,
            "exit_count": state.exit_count,
            "max_abs_z": (
                max(abs(value) for value in nonzero_z)
                if nonzero_z
                else 0.0
            ),
            "last_adf_pvalue": (
                state.adf_pvalue_by_rebalance[-1][1]
                if state.adf_pvalue_by_rebalance
                else None
            ),
        }

    return result


def run_validation(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only-Sicherheitsvertrag verletzt.")

    manifest = _load_manifest(manifest_path)

    universe_symbols = tuple(get_universe(UNIVERSE).symbols)
    if universe_symbols != SYMBOLS:
        raise ValueError("Trial-034-Universe entspricht nicht dem Pair-Set.")

    for universe in list_universes():
        if universe.name == UNIVERSE:
            continue
        if set(SYMBOLS).intersection(universe.symbols):
            raise ValueError(
                f"Symbol-Overlap mit bestehendem Universum: {universe.name}"
            )

    assets = _load_assets(data_dir, manifest)
    pair_states = _build_pair_states(assets)

    adjusted_close_fingerprints = {}
    for symbol, bars in assets.items():
        adjusted = _yahoo_adjclose(
            symbol,
            bars[0].timestamp,
            bars[-1].timestamp,
        )
        adjusted_close_fingerprints[symbol] = _fp(
            [
                [timestamp.isoformat(), value]
                for timestamp, value in sorted(adjusted.items())
            ]
        )

    scenarios = {
        name: _scenario(assets, pair_states, multiplier)
        for name, multiplier in COST_SCENARIOS
    }

    gates = _gates(scenarios, ResearchGateConfig())

    report = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "research_only": True,
        "candidate_status": (
            "VALIDATED_PASS"
            if gates["all_relevant_checks_passed"]
            else "BLOCKED"
        ),
        "hypothesis": (
            "Five fixed ex ante ETF pairs with monthly ADF cointegration "
            "eligibility and daily price-ratio mean reversion can provide a "
            "standalone market-neutral return stream after project costs."
        ),
        "pairs": [
            {
                "left": left,
                "right": right,
                "economic_group": group,
            }
            for left, right, group in PAIR_SPECS
        ],
        "source": {
            "universe": UNIVERSE,
            "symbols": list(SYMBOLS),
            "target_candles_per_symbol": TARGET_COUNT,
            "common_return_count": len(
                next(iter(assets.values()))
            ) - 2,
            "research_count": RESEARCH_COUNT,
            "holdout_count": HOLDOUT_COUNT,
            "coverage_preflight_workflow": 36044264502,
            "coverage_preflight_artifact": 10827702970,
            "coverage_preflight_fingerprint": "b4102c8e01e442ca5657426b96f0dc97ec919783299408946975f49b05c445a4",
            "fully_symbol_disjoint": True,
            "performance_selection_in_coverage": False,
            "adjusted_close_fingerprints": adjusted_close_fingerprints,
        },
        "methodology": {
            "formation_window_sessions": FORMATION_WINDOW,
            "zscore_window_sessions": Z_WINDOW,
            "monthly_refresh_spacing_sessions": REBALANCE_PERIOD,
            "adf_test": {
                "test": "Augmented Dickey-Fuller",
                "regression": "c",
                "autolag": "AIC",
                "eligibility_pvalue": ADF_PVALUE,
            },
            "entry_abs_z": ENTRY_Z,
            "exit_abs_z": EXIT_ABS_Z,
            "position_sizing": (
                "equal capital within each pair; equal gross allocation "
                "across active pairs; max gross exposure 1.0; net exposure 0.0"
            ),
            "execution": "Close(t) decision -> next open -> following-open return",
            "costs": {
                "fee_rate": FEE_RATE,
                "slippage_rate": SLIPPAGE_RATE,
            },
            "cost_stress": [name for name, _ in COST_SCENARIOS],
            "short_leg_borrow_cost_modeled": False,
            "dividend_cashflows_modeled": False,
            "parameter_search": False,
            "threshold_search": False,
            "pair_search": False,
            "selection_used": False,
            "holdout_used_for_selection": False,
            "orders_enabled": False,
        },
        "pair_diagnostics": _pair_diagnostics(pair_states),
        "scenarios": scenarios,
        "gate_contract": gates,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_validation(
        Path(args.data_dir),
        Path(args.manifest),
        Path(args.output),
    )
    print("TRIAL_034_STATUS:", report["status"])
    print("TRIAL_034_CANDIDATE_STATUS:", report["candidate_status"])
    print("TRIAL_034_REPORT_FINGERPRINT:", report["report_fingerprint"])
    print(
        "TRIAL_034_CHECKS:",
        json.dumps(report["gate_contract"], sort_keys=True),
    )


if __name__ == "__main__":
    main()
