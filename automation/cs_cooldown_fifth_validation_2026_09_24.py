"""Fixed one-session CS cooldown hypothesis on a fifth disjoint validation set.

The hypothesis is deliberately narrow and executable: after a Cross-Sectional
winner-reversal has been fully observed over one open-to-open interval, the
next interval carries zero CS sleeve exposure; that 50% sleeve is held in cash.
The fixed trend sleeve remains unchanged.

No parameter search or threshold tuning is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from automation import candidate_validation_50_50_vol_budget as base
from config import settings
from research.asset_universes import get_universe
from research.protocol import dataset_fingerprint

TREND_UNIVERSE = "validation_2026_09_24_fifth_trend"
CS_UNIVERSE = "validation_2026_09_24_fifth_cs"
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
COOLDOWN_SESSIONS = 1
FEE_RATE = base.FEE_RATE
SLIPPAGE_RATE = base.SLIPPAGE_RATE
COST_SCENARIOS = base.COST_SCENARIOS
TREND_STRATEGY = base.TREND_STRATEGY
CS_LOOKBACK = base.CS_LOOKBACK
CS_SKIP = base.CS_SKIP
CS_REBALANCE = base.CS_REBALANCE
CS_TOP_N = base.CS_TOP_N
TARGET_VOL = base.TARGET_VOL
VOL_WINDOW = base.VOL_WINDOW
YAHOO_BASE_URL = base.YAHOO_BASE_URL


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


def _manifest(path: Path, universe_name: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(universe_name)
    symbols = tuple(item["symbol"] for item in data.get("datasets", []))
    if data.get("universe") != universe_name or symbols != tuple(universe.symbols):
        raise ValueError(f"Manifest passt nicht zu {universe_name}.")
    if data.get("target_count") != TARGET_COUNT or data.get("source") != "yahoo_chart":
        raise ValueError(f"Unerwartete Datenbasis für {universe_name}.")
    safety = data.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError("Manifest-Sicherheitsvertrag verletzt.")
    return data


def _assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    out = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = base.load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if len(bars) != TARGET_COUNT:
            raise ValueError(f"{symbol}: unerwartete Candle-Anzahl")
        if dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: Dataset-Fingerprint mismatch")
        out[symbol] = bars
    common = set.intersection(
        *[{bar.timestamp for bar in bars} for bars in out.values()]
    )
    if len(common) != TARGET_COUNT:
        raise ValueError(f"Expected {TARGET_COUNT} common candles, got {len(common)}")
    ordered = sorted(common)
    return {
        symbol: tuple(
            {bar.timestamp: bar for bar in bars}[ts] for ts in ordered
        )
        for symbol, bars in out.items()
    }


def _yahoo_adjclose(
    symbol: str,
    start: datetime,
    end: datetime,
) -> dict[datetime, float]:
    params = {
        "period1": int((start - timedelta(days=3)).timestamp()),
        "period2": int((end + timedelta(days=3)).timestamp()),
        "interval": "1d",
        "events": "div,splits",
        "includePrePost": "false",
    }
    url = (
        f"{YAHOO_BASE_URL}/{urllib.parse.quote(symbol, safe='')}?"
        f"{urllib.parse.urlencode(params)}"
    )
    for attempt in range(4):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "trading-agent-research/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode())
            result = payload["chart"]["result"][0]
            return {
                datetime.fromtimestamp(int(ts), tz=timezone.utc): float(value)
                for ts, value in zip(
                    result["timestamp"],
                    result["indicators"]["adjclose"][0]["adjclose"],
                )
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
                raise RuntimeError(
                    f"Adjusted-Close für {symbol} nicht verfügbar: {exc}"
                ) from exc
            time.sleep(1.0 * (2**attempt))
    raise RuntimeError("Unerwarteter Yahoo-Fehler.")


def _cs_reversal_flags(
    cs: dict[str, tuple],
    cs_weights: tuple[dict[str, float], ...],
) -> tuple[bool | None, ...]:
    n = min(len(values) for values in cs.values())
    flags: list[bool | None] = []
    for i in range(n - 2):
        selected = tuple(
            symbol for symbol, weight in cs_weights[i].items()
            if weight > 0.0
        )
        if len(selected) != CS_TOP_N:
            flags.append(None)
            continue

        selected_returns = []
        nonselected_returns = []
        for symbol, bars in cs.items():
            value = bars[i + 2].open / bars[i + 1].open - 1.0
            if symbol in selected:
                selected_returns.append(value)
            else:
                nonselected_returns.append(value)

        spread = (
            sum(selected_returns) / len(selected_returns)
            - sum(nonselected_returns) / len(nonselected_returns)
        )
        flags.append(spread < 0.0)
    return tuple(flags)


def _portfolio_rows(
    trend: dict[str, tuple],
    cs: dict[str, tuple],
    trend_weights: tuple[dict[str, float], ...],
    cs_weights: tuple[dict[str, float], ...],
    adjusted: dict[str, dict[datetime, float]],
    *,
    cooldown: bool,
) -> tuple[dict, ...]:
    n = min(len(next(iter(trend.values()))), len(next(iter(cs.values())))) - 2
    reversal_flags = _cs_reversal_flags(cs, cs_weights)
    previous_trend_effective = {symbol: 0.0 for symbol in trend}
    previous_cs_effective = {symbol: 0.0 for symbol in cs}
    rows = []

    for i in range(n):
        trend_gross_open = 0.0
        trend_gross_close = 0.0
        trend_gross_adjusted = 0.0
        cs_gross_open = 0.0
        cs_gross_close = 0.0
        cs_gross_adjusted = 0.0
        turnover = 0.0

        cooldown_active = (
            cooldown
            and i > 0
            and reversal_flags[i - 1] is True
        )
        effective_cs_scale = 0.0 if cooldown_active else 0.5

        for symbol, bars in trend.items():
            weight = 0.5 * trend_weights[i][symbol]
            r_open = bars[i + 2].open / bars[i + 1].open - 1.0
            r_close = bars[i + 2].close / bars[i + 1].close - 1.0
            adj = adjusted[symbol]
            r_adj = (
                adj[bars[i + 2].timestamp]
                / adj[bars[i + 1].timestamp]
                - 1.0
            )
            trend_gross_open += weight * r_open
            trend_gross_close += weight * r_close
            trend_gross_adjusted += weight * r_adj
            turnover += abs(weight - previous_trend_effective[symbol])
            previous_trend_effective[symbol] = weight

        for symbol, bars in cs.items():
            weight = effective_cs_scale * cs_weights[i][symbol]
            r_open = bars[i + 2].open / bars[i + 1].open - 1.0
            r_close = bars[i + 2].close / bars[i + 1].close - 1.0
            adj = adjusted[symbol]
            r_adj = (
                adj[bars[i + 2].timestamp]
                / adj[bars[i + 1].timestamp]
                - 1.0
            )
            cs_gross_open += weight * r_open
            cs_gross_close += weight * r_close
            cs_gross_adjusted += weight * r_adj
            turnover += abs(weight - previous_cs_effective[symbol])
            previous_cs_effective[symbol] = weight

        gross_open = trend_gross_open + cs_gross_open
        gross_close = trend_gross_close + cs_gross_close
        gross_adjusted = trend_gross_adjusted + cs_gross_adjusted

        rows.append(
            {
                "timestamp": bars[i + 2].timestamp,
                "gross_open": gross_open,
                "gross_close": gross_close,
                "gross_adjusted_close": gross_adjusted,
                "turnover": turnover,
                "cooldown_active": cooldown_active,
                "previous_reversal_observed": (
                    reversal_flags[i - 1] is True if i > 0 else False
                ),
                "cs_reversal_observed": reversal_flags[i],
            }
        )

    return tuple(rows)


def _stats(rows: list[dict], start: int, end: int) -> dict:
    segment = rows[start:end]
    if not segment:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "day_count": 0,
            "median_scale": 0.0,
            "minimum_scale": 0.0,
        }

    equity = peak = 1.0
    gross_profit = gross_loss = 0.0
    max_dd = 0.0
    scales = []
    for row in segment:
        value = row["net_return"]
        scales.append(row["scale"])
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(
            max_dd,
            1.0 - equity / peak if equity > 0.0 else 1.0,
        )
        if value > 0.0:
            gross_profit += value
        elif value < 0.0:
            gross_loss -= value

    pf = (
        gross_profit / gross_loss
        if gross_loss > 0.0
        else ("inf" if gross_profit > 0.0 else 0.0)
    )
    ordered = sorted(scales)
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": pf,
        "day_count": len(segment),
        "median_scale": ordered[len(ordered) // 2],
        "minimum_scale": min(scales),
    }


def _simulate(
    rows: tuple[dict, ...],
    multiplier: float,
    use_budget: bool,
    total_return: bool,
) -> list[dict]:
    history: list[float] = []
    previous_scale = 1.0
    output = []
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier

    for row in rows:
        scale = 1.0
        if use_budget and len(history) >= VOL_WINDOW:
            sample = history[-VOL_WINDOW:]
            mean = sum(sample) / len(sample)
            variance = sum((x - mean) ** 2 for x in sample) / len(sample)
            realized_vol = variance**0.5 * (252.0**0.5)
            if realized_vol > TARGET_VOL:
                scale = min(1.0, TARGET_VOL / realized_vol)

        gross = row["gross_open"]
        if total_return:
            gross += row["gross_adjusted_close"] - row["gross_close"]

        turnover = scale * row["turnover"] + abs(scale - previous_scale)
        net = scale * gross - cost_rate * turnover
        output.append(
            {
                "timestamp": row["timestamp"],
                "scale": scale,
                "net_return": net,
                "gross_return": scale * gross,
            }
        )
        previous_scale = scale
        history.append(
            row["gross_open"]
            - (FEE_RATE + SLIPPAGE_RATE) * row["turnover"]
        )
    return output


def _rolling(rows: list[dict], research_end: int) -> list[dict]:
    width = research_end // 5
    output = []
    start = 0
    for index in range(5):
        end = research_end if index == 4 else start + width
        output.append({"window_index": index + 1, **_stats(rows, start, end)})
        start = end
    return output


def _summary(rows: list[dict], windows: list[dict]) -> dict:
    values = [row["net_return"] for row in rows]
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    equity = 1.0
    for value in values:
        equity *= 1.0 + value

    return {
        "window_count": len(windows),
        "profitable_windows": sum(
            item["period_return"] > 0.0 for item in windows
        ),
        "profitable_window_ratio": (
            sum(item["period_return"] > 0.0 for item in windows)
            / len(windows)
        ),
        "total_net_return": equity - 1.0,
        "overall_profit_factor": (
            gross_profit / gross_loss
            if gross_loss > 0.0
            else ("inf" if gross_profit > 0.0 else 0.0)
        ),
        "average_drawdown_percent": (
            sum(item["max_drawdown_percent"] for item in windows)
            / len(windows)
        ),
    }


def _scenario(rows: tuple[dict, ...], multiplier: float) -> dict:
    out = {}
    for name, budget in (
        ("unscaled_baseline", False),
        ("vol_budget_10pct", True),
    ):
        price = _simulate(rows, multiplier, budget, False)
        total = _simulate(rows, multiplier, budget, True)
        research = _stats(price, 0, RESEARCH_COUNT)
        holdout = _stats(price, RESEARCH_COUNT, len(price))
        total_research = _stats(total, 0, RESEARCH_COUNT)
        total_holdout = _stats(total, RESEARCH_COUNT, len(total))
        rolling = _rolling(price, RESEARCH_COUNT)
        out[name] = {
            "price_only": {
                "research": research,
                "holdout": holdout,
                "rolling_windows": rolling,
                "rolling_summary": _summary(price[:RESEARCH_COUNT], rolling),
                "oos_to_is_return_ratio": (
                    holdout["period_return"] / research["period_return"]
                    if research["period_return"] > 0.0
                    else 0.0
                ),
            },
            "total_return_sensitivity": {
                "research": total_research,
                "holdout": total_holdout,
            },
        }
    return out


def _gates(scenarios: dict) -> dict:
    from validation.research_gates import ResearchGateConfig

    base_scenario = scenarios["base"]["vol_budget_10pct"]["price_only"]
    stress15 = scenarios["stress_1_5x_cost"]["vol_budget_10pct"]["price_only"]
    stress2 = scenarios["stress_2x_cost"]["vol_budget_10pct"]["price_only"]
    total = scenarios["base"]["vol_budget_10pct"]["total_return_sensitivity"]
    rolling = base_scenario["rolling_summary"]
    config = ResearchGateConfig()

    checks = {
        "research_drawdown": (
            base_scenario["research"]["max_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "rolling_return_positive": rolling["total_net_return"] > 0.0,
        "rolling_profit_factor": (
            _pf(rolling["overall_profit_factor"])
            >= config.minimum_profit_factor
        ),
        "rolling_profitable_window_ratio": (
            rolling["profitable_window_ratio"]
            >= config.minimum_profitable_window_ratio
        ),
        "rolling_average_drawdown": (
            rolling["average_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "oos_to_is_return_ratio": (
            base_scenario["oos_to_is_return_ratio"]
            >= config.minimum_oos_to_is_return_ratio
        ),
        "holdout_return_positive": base_scenario["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor": (
            _pf(base_scenario["holdout"]["profit_factor"])
            >= config.minimum_profit_factor
        ),
        "holdout_drawdown": (
            base_scenario["holdout"]["max_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "stress_1_5x_nonnegative": stress15["holdout"]["period_return"] >= 0.0,
        "stress_2x_nonnegative": stress2["holdout"]["period_return"] >= 0.0,
        "total_return_sensitivity_nonnegative": (
            total["holdout"]["period_return"] >= 0.0
        ),
    }
    return {
        "checks": checks,
        "all_relevant_checks_passed": all(checks.values()),
    }


def _research_hypothesis_check(
    baseline: dict,
    cooldown: dict,
) -> dict:
    b = baseline["base"]["vol_budget_10pct"]["price_only"]
    c = cooldown["base"]["vol_budget_10pct"]["price_only"]
    b_roll = b["rolling_summary"]
    c_roll = c["rolling_summary"]

    checks = {
        "research_drawdown_not_worse": (
            c["research"]["max_drawdown_percent"]
            <= b["research"]["max_drawdown_percent"]
        ),
        "rolling_profit_factor_not_worse": (
            _pf(c_roll["overall_profit_factor"])
            >= _pf(b_roll["overall_profit_factor"])
        ),
        "rolling_average_drawdown_not_worse": (
            c_roll["average_drawdown_percent"]
            <= b_roll["average_drawdown_percent"]
        ),
        "research_return_not_worse": (
            c_roll["total_net_return"] >= b_roll["total_net_return"]
        ),
    )
    return {
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }


def _holdout_confirmation(
    baseline: dict,
    cooldown: dict,
) -> dict:
    b = baseline["base"]["vol_budget_10pct"]["price_only"]["holdout"]
    c = cooldown["base"]["vol_budget_10pct"]["price_only"]["holdout"]

    checks = {
        "holdout_return_not_worse": c["period_return"] >= b["period_return"],
        "holdout_drawdown_not_worse": (
            c["max_drawdown_percent"] <= b["max_drawdown_percent"]
        ),
        "holdout_profit_factor_not_worse": (
            _pf(c["profit_factor"]) >= _pf(b["profit_factor"])
        ),
    }
    return {
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }


def run_validation(
    trend_data_dir: Path,
    trend_manifest_path: Path,
    cs_data_dir: Path,
    cs_manifest_path: Path,
    output_path: Path,
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only-Sicherheitsvertrag verletzt.")

    trend_manifest = _manifest(trend_manifest_path, TREND_UNIVERSE)
    cs_manifest = _manifest(cs_manifest_path, CS_UNIVERSE)
    trend = _assets(trend_data_dir, trend_manifest)
    cs = _assets(cs_data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError("Validation-Universen sind nicht disjunkt.")

    trend_weights = base._build_weight_path(trend, TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)
    all_assets = {**trend, **cs}
    adjusted = {
        symbol: _yahoo_adjclose(
            symbol,
            bars[0].timestamp,
            bars[-1].timestamp,
        )
        for symbol, bars in all_assets.items()
    }

    archive = {
        "schema_version": 1,
        "source": "yahoo_chart_adjusted_close",
        "datasets": {
            symbol: [
                [bar.timestamp.isoformat(), adjusted[symbol][bar.timestamp]]
                for bar in bars
            ]
            for symbol, bars in all_assets.items()
        },
    }
    archive["archive_fingerprint"] = _fp(archive)
    archive_path = output_path.with_name("adjusted_close_archive.json")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(
        json.dumps(archive, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )

    baseline_rows = _portfolio_rows(
        trend,
        cs,
        trend_weights,
        cs_weights,
        adjusted,
        cooldown=False,
    )
    cooldown_rows = _portfolio_rows(
        trend,
        cs,
        trend_weights,
        cs_weights,
        adjusted,
        cooldown=True,
    )

    if len(baseline_rows) < RESEARCH_COUNT + HOLDOUT_COUNT:
        raise ValueError(f"Zu wenige Returns: {len(baseline_rows)}")
    if len(cooldown_rows) != len(baseline_rows):
        raise ValueError("Baseline/Cooldown Return-Längen unterscheiden sich.")

    baseline_scenarios = {
        name: _scenario(baseline_rows, multiplier)
        for name, multiplier in COST_SCENARIOS
    }
    cooldown_scenarios = {
        name: _scenario(cooldown_rows, multiplier)
        for name, multiplier in COST_SCENARIOS
    }

    report = {
        "schema_version": 1,
        "diagnostic_type": "cs_cooldown_fifth_validation_2026_09_24",
        "status": "COMPLETED",
        "candidate_status": "RESEARCH_ONLY",
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "source": {
            "trend_universe": TREND_UNIVERSE,
            "trend_symbols": list(get_universe(TREND_UNIVERSE).symbols),
            "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
            "cs_universe": CS_UNIVERSE,
            "cs_symbols": list(get_universe(CS_UNIVERSE).symbols),
            "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
            "raw_candle_count_per_asset": TARGET_COUNT,
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "independent_asset_universes": True,
            "fully_symbol_disjoint_validation_set": True,
            "adjusted_close_archive_fingerprint": archive["archive_fingerprint"],
        },
        "methodology": {
            "baseline_architecture_fixed": True,
            "trend_strategy": TREND_STRATEGY,
            "cs_lookback_sessions": CS_LOOKBACK,
            "cs_skip_sessions": CS_SKIP,
            "cs_rebalance_sessions": CS_REBALANCE,
            "cs_top_n": CS_TOP_N,
            "cooldown_sessions": COOLDOWN_SESSIONS,
            "cooldown_rule": (
                "After a fixed CS winner reversal is observed over one complete "
                "open-to-open interval, the next return interval carries zero "
                "CS sleeve weight; the 50% CS sleeve is held in cash."
            ),
            "lookahead_control": (
                "Cooldown uses reversal_flags[i-1] only; the same return interval "
                "that reveals the reversal is never modified."
            ),
            "trend_sleeve_during_cooldown": "unchanged 50%",
            "cost_model": "same base/stress cost model as fixed candidate",
            "optimization_used": False,
            "parameter_search": False,
            "asset_selection": False,
            "sleeve_weight_search": False,
            "holdout_used_for_selection": False,
            "gate_changes": False,
            "production_mutation": False,
            "orders_enabled": False,
        },
        "scope": {
            "new_data_downloads": True,
            "new_disjoint_validation_set": True,
            "research_holdout_split": "2798 / 700",
            "holdout_used_for_selection": False,
        },
        "baseline_scenarios": baseline_scenarios,
        "cooldown_scenarios": cooldown_scenarios,
        "research_hypothesis_check": _research_hypothesis_check(
            baseline_scenarios,
            cooldown_scenarios,
        ),
        "holdout_confirmation": _holdout_confirmation(
            baseline_scenarios,
            cooldown_scenarios,
        ),
        "baseline_gates": {
            name: _gates(baseline_scenarios) for name in ("base",)
        },
        "cooldown_gates": {
            name: _gates(cooldown_scenarios) for name in ("base",)
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    # Research rule first; holdout is confirmation, never selection.
    report["research_hypothesis_status"] = (
        "PASS"
        if report["research_hypothesis_check"]["all_checks_passed"]
        else "FAIL"
    )
    report["holdout_confirmation_status"] = (
        "PASS"
        if report["holdout_confirmation"]["all_checks_passed"]
        else "FAIL"
    )
    report["research_validation_status"] = (
        "PASS"
        if (
            report["research_hypothesis_status"] == "PASS"
            and report["cooldown_gates"]["base"]["all_relevant_checks_passed"]
            and report["holdout_confirmation_status"] == "PASS"
        )
        else "FAIL"
    )

    report = json.loads(
        json.dumps(report, ensure_ascii=False, allow_nan=False)
    )
    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend-data-dir", required=True)
    parser.add_argument("--trend-manifest", required=True)
    parser.add_argument("--cs-data-dir", required=True)
    parser.add_argument("--cs-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_validation(
        Path(args.trend_data_dir),
        Path(args.trend_manifest),
        Path(args.cs_data_dir),
        Path(args.cs_manifest),
        Path(args.output),
    )
    print("CS_COOLDOWN_VALIDATION_STATUS:", report["status"])
    print("RESEARCH_HYPOTHESIS_STATUS:", report["research_hypothesis_status"])
    print("HOLDOUT_CONFIRMATION_STATUS:", report["holdout_confirmation_status"])
    print("RESEARCH_VALIDATION_STATUS:", report["research_validation_status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])


if __name__ == "__main__":
    main()
