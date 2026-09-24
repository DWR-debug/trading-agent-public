"""Independent validation of the fixed 50/50 + 10% vol-budget research candidate.

Research-only: no optimization, selection, production mutation or orders.
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
from automation.literature_strategy_lab import load_bars
from config import settings
from research.asset_universes import get_universe
from research.protocol import dataset_fingerprint
from validation.research_gates import ResearchGateConfig

TREND_UNIVERSE = "validation_trend"
CS_UNIVERSE = "validation_cs"
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
TREND_STRATEGY = "sma_50_200_inverse_vol"
CS_LOOKBACK = 252
CS_SKIP = 21
CS_REBALANCE = 21
CS_TOP_N = 2
TARGET_VOL = 0.10
VOL_WINDOW = 63
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)
YAHOO_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"


def _canon(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode()).hexdigest()


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


def _align_assets_by_latest_start(assets: dict[str, tuple]) -> dict[str, tuple]:
    if not assets:
        return {}
    starts = {symbol: bars[0].timestamp for symbol, bars in assets.items() if bars}
    if len(starts) != len(assets):
        raise ValueError("All assets need at least one candle.")
    reference_symbol = max(starts, key=starts.get)
    reference_timestamps = tuple(bar.timestamp for bar in assets[reference_symbol])
    reference_set = set(reference_timestamps)
    aligned: dict[str, tuple] = {}
    for symbol, bars in assets.items():
        by_timestamp = {bar.timestamp: bar for bar in bars}
        missing = reference_set.difference(by_timestamp)
        if missing:
            sample = ", ".join(sorted(ts.isoformat() for ts in missing)[:3])
            raise ValueError(
                f"{symbol}: reference calendar has missing timestamps ({sample})."
            )
        aligned[symbol] = tuple(by_timestamp[timestamp] for timestamp in reference_timestamps)
    return aligned


def _assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    out = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if len(bars) != TARGET_COUNT or dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: Dataset-Identität/Fingerprint stimmt nicht.")
        out[symbol] = bars

    if not out:
        raise ValueError("Mindestens ein Asset wird benötigt.")
    if len({len(bars) for bars in out.values()}) != 1:
        raise ValueError("Asset-Kalender müssen dieselbe Candle-Anzahl besitzen.")
    aligned = _align_assets_by_latest_start(out)
    if len(next(iter(aligned.values()))) != TARGET_COUNT:
        raise ValueError("Referenzkalender-Ausrichtung hat die Zielhistorie verändert.")
    return aligned
def _cs_weights(assets: dict[str, tuple]) -> tuple[dict[str, float], ...]:
    n = min(len(v) for v in assets.values())
    current = {s: 0.0 for s in assets}
    out = []
    for i in range(n):
        if i % CS_REBALANCE == 0:
            if i < CS_LOOKBACK + CS_SKIP:
                current = {s: 0.0 for s in assets}
            else:
                anchor = i - CS_SKIP
                origin = anchor - CS_LOOKBACK
                scores = {
                    s: assets[s][anchor].close / assets[s][origin].close - 1.0
                    for s in assets
                }
                winners = set(
                    sorted(scores, key=scores.get, reverse=True)[:CS_TOP_N]
                )
                current = {
                    s: (1.0 / CS_TOP_N if s in winners else 0.0)
                    for s in assets
                }
        out.append(dict(current))
    return tuple(out)


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
                raise RuntimeError(
                    f"Adjusted-Close für {symbol} nicht verfügbar: {exc}"
                ) from exc
            time.sleep(1.0 * (2**attempt))
    raise RuntimeError("Unerwarteter Yahoo-Fehler.")


def _return_rows(
    assets: dict[str, tuple],
    weights: tuple[dict[str, float], ...],
    adjusted: dict[str, dict[datetime, float]],
) -> tuple[dict, ...]:
    """Build two-session PIT returns by timestamp, never by position."""
    if not assets:
        return ()
    for symbol, bars in assets.items():
        if len(weights) != len(bars):
            raise ValueError(
                f"weights length for {symbol} ({len(weights)}) must match asset length ({len(bars)})."
            )
        if len(bars) < 3:
            raise ValueError(f"{symbol}: at least 3 candles are required.")

    per_asset: dict[str, dict[datetime, dict[str, float]]] = {}
    realization_timestamps: set[datetime] = set()
    for symbol, bars in assets.items():
        weight_by_time = {
            bars[index].timestamp: float(weights[index].get(symbol, 0.0))
            for index in range(len(bars))
        }
        adjusted_values = adjusted.get(symbol)
        if adjusted_values is None:
            raise ValueError(f"Missing adjusted-close series for {symbol}.")
        rows = {}
        previous_weight = 0.0
        for index in range(2, len(bars)):
            decision_timestamp = bars[index - 2].timestamp
            previous_timestamp = bars[index - 1].timestamp
            timestamp = bars[index].timestamp
            if not previous_timestamp < timestamp:
                raise ValueError(f"{symbol}: timestamps must be strictly increasing.")
            try:
                adjusted_return = adjusted_values[timestamp] / adjusted_values[previous_timestamp] - 1.0
            except KeyError as exc:
                raise ValueError(
                    f"{symbol}: adjusted close missing at {exc.args[0]!s}."
                ) from exc
            target_weight = weight_by_time[decision_timestamp]
            rows[timestamp] = {
                "gross_open": bars[index].open / bars[index - 1].open - 1.0,
                "gross_close": bars[index].close / bars[index - 1].close - 1.0,
                "gross_adjusted_close": adjusted_return,
                "turnover": abs(target_weight - previous_weight),
                "weight": target_weight,
            }
            previous_weight = target_weight
            realization_timestamps.add(timestamp)
        per_asset[symbol] = rows

    common = sorted(set.intersection(*(set(rows) for rows in per_asset.values())))
    if len(common) < 1:
        raise ValueError("No common realization timestamps after PIT construction.")

    output = []
    for timestamp in common:
        gross_open = gross_close = gross_adjusted_close = turnover = 0.0
        for symbol, rows in per_asset.items():
            row = rows[timestamp]
            weight = row["weight"]
            gross_open += weight * row["gross_open"]
            gross_close += weight * row["gross_close"]
            gross_adjusted_close += weight * row["gross_adjusted_close"]
            turnover += row["turnover"]
        output.append({
            "timestamp": timestamp,
            "gross_open": gross_open,
            "gross_close": gross_close,
            "gross_adjusted_close": gross_adjusted_close,
            "turnover": turnover,
        })
    return tuple(output)
def _align(
    trend: dict[str, tuple],
    trend_weights: tuple[dict[str, float], ...],
    trend_adj: dict[str, dict[datetime, float]],
    cs: dict[str, tuple],
    cs_weights: tuple[dict[str, float], ...],
    cs_adj: dict[str, dict[datetime, float]],
) -> tuple[dict, ...]:
    trend_rows = {
        row["timestamp"]: row
        for row in _return_rows(trend, trend_weights, trend_adj)
    }
    cs_rows = {
        row["timestamp"]: row
        for row in _return_rows(cs, cs_weights, cs_adj)
    }
    common = sorted(set(trend_rows) & set(cs_rows))
    if len(common) < 3300:
        raise ValueError(f"Zu wenig gemeinsame Returns: {len(common)}")
    return tuple(
        {
            "timestamp": ts,
            "gross_open": (
                0.5 * trend_rows[ts]["gross_open"]
                + 0.5 * cs_rows[ts]["gross_open"]
            ),
            "gross_close": (
                0.5 * trend_rows[ts]["gross_close"]
                + 0.5 * cs_rows[ts]["gross_close"]
            ),
            "gross_adjusted_close": (
                0.5 * trend_rows[ts]["gross_adjusted_close"]
                + 0.5 * cs_rows[ts]["gross_adjusted_close"]
            ),
            "turnover": (
                0.5 * trend_rows[ts]["turnover"]
                + 0.5 * cs_rows[ts]["turnover"]
            ),
        }
        for ts in common
    )


def _vol(history: list[float]) -> float | None:
    if len(history) < VOL_WINDOW:
        return None
    sample = history[-VOL_WINDOW:]
    mean = sum(sample) / len(sample)
    variance = sum((x - mean) ** 2 for x in sample) / len(sample)
    return math.sqrt(variance) * math.sqrt(252.0)


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
        realized_vol = _vol(history)
        if use_budget and realized_vol is not None and realized_vol > TARGET_VOL:
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
                "realized_vol_estimate": realized_vol,
            }
        )
        previous_scale = scale
        history.append(
            row["gross_open"]
            - (FEE_RATE + SLIPPAGE_RATE) * row["turnover"]
        )
    return output


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
    gp = gl = 0.0
    max_dd = 0.0
    scales = []
    for row in segment:
        value = row["net_return"]
        scales.append(row["scale"])
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
        if value > 0:
            gp += value
        elif value < 0:
            gl -= value
    pf = gp / gl if gl > 0 else ("inf" if gp > 0 else 0.0)
    ordered = sorted(scales)
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": pf,
        "day_count": len(segment),
        "median_scale": ordered[len(ordered) // 2],
        "minimum_scale": min(scales),
    }


def _rolling(rows: list[dict], research_end: int) -> list[dict]:
    width = research_end // 5
    windows = []
    start = 0
    for index in range(5):
        end = research_end if index == 4 else start + width
        windows.append(
            {"window_index": index + 1, **_stats(rows, start, end)}
        )
        start = end
    return windows


def _summary(rows: list[dict], windows: list[dict]) -> dict:
    values = [row["net_return"] for row in rows]
    gp = sum(value for value in values if value > 0)
    gl = -sum(value for value in values if value < 0)
    equity = 1.0
    for value in values:
        equity *= 1.0 + value
    return {
        "window_count": len(windows),
        "profitable_windows": sum(
            item["period_return"] > 0 for item in windows
        ),
        "profitable_window_ratio": sum(
            item["period_return"] > 0 for item in windows
        ) / len(windows),
        "total_net_return": equity - 1.0,
        "overall_profit_factor": (
            gp / gl if gl > 0 else ("inf" if gp > 0 else 0.0)
        ),
        "average_drawdown_percent": sum(
            item["max_drawdown_percent"] for item in windows
        ) / len(windows),
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
        roll = _rolling(price, RESEARCH_COUNT)
        out[name] = {
            "price_only": {
                "research": research,
                "holdout": holdout,
                "rolling_windows": roll,
                "rolling_summary": _summary(price[:RESEARCH_COUNT], roll),
                "oos_to_is_return_ratio": (
                    holdout["period_return"] / research["period_return"]
                    if research["period_return"] > 0
                    else 0.0
                ),
            },
            "total_return_sensitivity": {
                "research": total_research,
                "holdout": total_holdout,
            },
        }
    return out


def _gates(scenarios: dict, config: ResearchGateConfig) -> dict:
    base = scenarios["base"]["vol_budget_10pct"]["price_only"]
    stress15 = scenarios["stress_1_5x_cost"]["vol_budget_10pct"]["price_only"]
    stress2 = scenarios["stress_2x_cost"]["vol_budget_10pct"]["price_only"]
    total = scenarios["base"]["vol_budget_10pct"]["total_return_sensitivity"]
    roll = base["rolling_summary"]
    checks = {
        "research_drawdown": (
            base["research"]["max_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "rolling_return_positive": roll["total_net_return"] > 0,
        "rolling_profit_factor": (
            _pf(roll["overall_profit_factor"])
            >= config.minimum_profit_factor
        ),
        "rolling_profitable_window_ratio": (
            roll["profitable_window_ratio"]
            >= config.minimum_profitable_window_ratio
        ),
        "rolling_average_drawdown": (
            roll["average_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "oos_to_is_return_ratio": (
            base["oos_to_is_return_ratio"]
            >= config.minimum_oos_to_is_return_ratio
        ),
        "holdout_return_positive": base["holdout"]["period_return"] > 0,
        "holdout_profit_factor": (
            _pf(base["holdout"]["profit_factor"])
            >= config.minimum_profit_factor
        ),
        "holdout_drawdown": (
            base["holdout"]["max_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "stress_1_5x_nonnegative": (
            stress15["holdout"]["period_return"] >= 0
        ),
        "stress_2x_nonnegative": (
            stress2["holdout"]["period_return"] >= 0
        ),
        "total_return_sensitivity_nonnegative": (
            total["holdout"]["period_return"] >= 0
        ),
    }
    return {
        "thresholds": {
            "minimum_profit_factor": config.minimum_profit_factor,
            "maximum_drawdown_percent": config.maximum_drawdown_percent,
            "minimum_profitable_window_ratio": (
                config.minimum_profitable_window_ratio
            ),
            "minimum_oos_to_is_return_ratio": (
                config.minimum_oos_to_is_return_ratio
            ),
            "formal_stress_cost_multiplier": config.stress_cost_multiplier,
        },
        "checks": checks,
        "all_relevant_checks_passed": all(checks.values()),
        "trade_count_checks": (
            "not_applicable_for_continuous_portfolio_return_control"
        ),
    }


def _delta(price: dict, total: dict) -> dict:
    p = price["holdout"]
    t = total["holdout"]
    ppf = _pf(p["profit_factor"])
    tpf = _pf(t["profit_factor"])
    pfdelta = (
        "unchanged_inf"
        if math.isinf(ppf) and math.isinf(tpf)
        else (
            "inf"
            if math.isinf(tpf)
            else ("-inf" if math.isinf(ppf) else tpf - ppf)
        )
    )
    return {
        "holdout_return_delta_percentage_points": (
            t["period_return"] - p["period_return"]
        )
        * 100.0,
        "holdout_drawdown_delta_percentage_points": (
            t["max_drawdown_percent"] - p["max_drawdown_percent"]
        ),
        "holdout_profit_factor_delta": pfdelta,
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
    trend_weights = _build_weight_path(trend, TREND_STRATEGY)
    cs_weights = _cs_weights(cs)
    all_assets = {**trend, **cs}
    adjusted = {
        symbol: _yahoo_adjclose(symbol, bars[0].timestamp, bars[-1].timestamp)
        for symbol, bars in all_assets.items()
    }
    adjusted_archive = {
        symbol: [
            [bar.timestamp.isoformat(), adjusted[symbol][bar.timestamp]]
            for bar in bars
        ]
        for symbol, bars in all_assets.items()
    }
    adjusted_close_fingerprints = {
        symbol: _fp(values)
        for symbol, values in adjusted_archive.items()
    }
    trend_adjusted = {symbol: adjusted[symbol] for symbol in trend}
    cs_adjusted = {symbol: adjusted[symbol] for symbol in cs}
    rows = _align(
        trend,
        trend_weights,
        trend_adjusted,
        cs,
        cs_weights,
        cs_adjusted,
    )
    if len(rows) < RESEARCH_COUNT + HOLDOUT_COUNT:
        raise ValueError(f"Zu wenige Returns: {len(rows)}")
    scenarios = {
        name: _scenario(rows, multiplier)
        for name, multiplier in COST_SCENARIOS
    }
    adjusted_archive_document = {
        "schema_version": 1,
        "source": "yahoo_chart_adjusted_close",
        "datasets": adjusted_archive,
    }
    adjusted_archive_fingerprint = _fp(adjusted_archive_document)
    adjusted_archive_document["archive_fingerprint"] = adjusted_archive_fingerprint
    archive_path = output_path.with_name("adjusted_close_archive.json")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(
        json.dumps(
            adjusted_archive_document,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    gates = _gates(scenarios, ResearchGateConfig())
    reference = scenarios["base"]["vol_budget_10pct"]
    report = {
        "schema_version": 1,
        "diagnostic_type": "candidate_validation_50_50_vol_budget",
        "status": "COMPLETED",
        "candidate_status": (
            "PASS" if gates["all_relevant_checks_passed"] else "BLOCKED"
        ),
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "source": {
            "trend_universe": TREND_UNIVERSE,
            "trend_symbols": list(get_universe(TREND_UNIVERSE).symbols),
            "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
            "trend_source_run_id": trend_manifest.get("provenance", {}).get("run_id"),
            "cs_universe": CS_UNIVERSE,
            "cs_symbols": list(get_universe(CS_UNIVERSE).symbols),
            "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
            "cs_source_run_id": cs_manifest.get("provenance", {}).get("run_id"),
            "raw_candle_count_per_asset": TARGET_COUNT,
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "common_return_count": len(rows),
            "independent_asset_universes": True,
            "out_of_time_validation": False,
            "adjusted_close_fingerprints": adjusted_close_fingerprints,
            "adjusted_close_archive_fingerprint": adjusted_archive_fingerprint,
        },
        "methodology": {
            "architecture": (
                "fixed 50/50 Cross-Asset SMA 50/200 inverse-volatility "
                "+ 12-1 CS momentum top-2 long-only"
            ),
            "vol_budget_target_annualized": TARGET_VOL,
            "vol_budget_window_sessions": VOL_WINDOW,
            "execution_model": (
                "close(t) decision -> next-session open -> following-open return"
            ),
            "research_holdout_split": (
                "2,798 / 700 return observations after two-session PIT construction"
            ),
            "rolling_windows": "5 fixed windows covering the full Research span",
            "cost_scenarios": [name for name, _ in COST_SCENARIOS],
            "optimization_used": False,
            "selection_profile_used": False,
            "signal_parameters_changed": False,
            "sleeve_weights_changed": False,
            "production_strategy_changed": False,
            "orders_enabled": False,
            "total_return_sensitivity": (
                "Adjusted-Close dividend/split sensitivity added to the same "
                "open-to-open path; diagnostic only"
            ),
        },
        "reference_unscaled": scenarios["base"]["unscaled_baseline"],
        "scenarios": scenarios,
        "gate_contract": gates,
        "total_return_sensitivity_delta": _delta(
            reference["price_only"],
            reference["total_return_sensitivity"],
        ),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
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
    print("CANDIDATE_VALIDATION_STATUS:", report["status"])
    print("CANDIDATE_STATUS:", report["candidate_status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    print(
        "ALL_RELEVANT_CHECKS_PASSED:",
        report["gate_contract"]["all_relevant_checks_passed"],
    )


if __name__ == "__main__":
    main()
