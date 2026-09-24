"""Research-only diagnosis of reversal/rebound states in the fixed candidate.

External motivation:
Daniel & Moskowitz (2016) document momentum crashes as negative-return episodes
that can occur after market declines and contemporaneously with market rebounds.
This diagnostic does not import an external market index; instead it constructs
one fixed, equal-weighted cross-asset return proxy from the already archived
validation assets.

Two fixed diagnostic states are evaluated on the four immutable validations:
1. rebound_after_decline:
   prior 20-session equal-weighted cross-asset close-to-close return < 0
   AND current realized equal-weighted open-to-open return > 0.
2. cs_winner_reversal:
   current open-to-open return of the fixed top-2 cross-sectional momentum
   winners minus the equal-weighted return of all non-selected CS assets < 0.

A combined state requires both conditions.

Only the Research span is reported. Holdout is never entered into the result.
No parameter search, asset selection, strategy mutation, gate change, new data
download, or order is permitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from automation import candidate_validation_50_50_vol_budget as base
from config import settings

RESEARCH_COUNT = base.RESEARCH_COUNT
PRIOR_DECLINE_SESSIONS = 20
MIN_DIAGNOSTIC_WARMUP = base.CS_LOOKBACK + base.CS_SKIP
WORST_DAY_BUCKET_PERCENT = 5

CASES = (
    {
        "name": "validation_1",
        "artifact_id": 10751817990,
        "run_id": 35865847394,
        "root": "research/candidate_validation",
        "trend_universe": "validation_trend",
        "cs_universe": "validation_cs",
    },
    {
        "name": "validation_2",
        "artifact_id": 10740188093,
        "run_id": 35839443616,
        "root": "research/independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_trend",
        "cs_universe": "validation_2026_09_23_cs",
    },
    {
        "name": "validation_3",
        "artifact_id": 10745697729,
        "run_id": 35851876264,
        "root": "research/third_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_third_trend",
        "cs_universe": "validation_2026_09_23_third_cs",
    },
    {
        "name": "validation_4",
        "artifact_id": 10753545703,
        "run_id": 35867637587,
        "root": "research/fourth_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_fourth_trend",
        "cs_universe": "validation_2026_09_23_fourth_cs",
    },
)


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


def _manifest(path: Path, universe_name: str) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    universe = base.get_universe(universe_name)
    symbols = tuple(item["symbol"] for item in manifest.get("datasets", []))
    if manifest.get("universe") != universe_name:
        raise ValueError(f"{universe_name}: unexpected universe")
    if symbols != tuple(universe.symbols):
        raise ValueError(f"{universe_name}: manifest symbols mismatch")
    if manifest.get("target_count") != base.TARGET_COUNT:
        raise ValueError(f"{universe_name}: unexpected target count")
    if manifest.get("source") != "yahoo_chart":
        raise ValueError(f"{universe_name}: unexpected data source")
    safety = manifest.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError(f"{universe_name}: paper-only manifest contract violated")
    return manifest


def _assets(data_dir: Path, manifest: dict[str, Any]) -> dict[str, tuple]:
    assets: dict[str, tuple] = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = base.load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if len(bars) != base.TARGET_COUNT:
            raise ValueError(f"{symbol}: unexpected candle count")
        if base.dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: dataset fingerprint mismatch")
        assets[symbol] = bars

    common = set.intersection(
        *[{bar.timestamp for bar in bars} for bars in assets.values()]
    )
    if len(common) != base.TARGET_COUNT:
        raise ValueError(
            f"Calendar intersection changed unexpectedly: {len(common)}"
        )

    ordered = sorted(common)
    aligned = {
        symbol: tuple(
            {bar.timestamp: bar for bar in bars}[timestamp]
            for timestamp in ordered
        )
        for symbol, bars in assets.items()
    }
    return aligned


def _load_case(source_root: Path, case: dict[str, Any]) -> tuple[dict[str, tuple], dict[str, tuple]]:
    root = source_root / case["root"]
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    stored_report_fp = report["report_fingerprint"]
    payload = dict(report)
    payload.pop("report_fingerprint", None)
    if _fp(payload) != stored_report_fp:
        raise ValueError(f'{case["name"]}: report fingerprint mismatch')
    if report["status"] != "COMPLETED":
        raise ValueError(f'{case["name"]}: report not completed')
    if report["candidate_status"] != "BLOCKED":
        raise ValueError(f'{case["name"]}: source candidate must remain BLOCKED')

    archive = json.loads((root / "adjusted_close_archive.json").read_text(encoding="utf-8"))
    stored_archive_fp = archive["archive_fingerprint"]
    archive_payload = dict(archive)
    archive_payload.pop("archive_fingerprint", None)
    if _fp(archive_payload) != stored_archive_fp:
        raise ValueError(f'{case["name"]}: archive fingerprint mismatch')
    if stored_archive_fp != report["source"]["adjusted_close_archive_fingerprint"]:
        raise ValueError(f'{case["name"]}: report/archive mismatch')

    data_dir = source_root / "data" / "market_data"
    trend_manifest = _manifest(root / "data_trend_manifest.json", case["trend_universe"])
    cs_manifest = _manifest(root / "data_cs_manifest.json", case["cs_universe"])
    trend = _assets(data_dir, trend_manifest)
    cs = _assets(data_dir, cs_manifest)

    if set(trend) & set(cs):
        raise ValueError(f'{case["name"]}: trend/CS universes overlap')

    return trend, cs


def _prior_close_return(
    assets: dict[str, tuple],
    index: int,
    lookback: int,
) -> float:
    values = []
    for bars in assets.values():
        start = bars[index - lookback].close
        end = bars[index].close
        if start <= 0:
            raise ValueError("Encountered non-positive close price")
        values.append(end / start - 1.0)
    return sum(values) / len(values)


def _cs_selected_symbols(weights: dict[str, float]) -> tuple[str, ...]:
    selected = tuple(symbol for symbol, weight in weights.items() if weight > 0.0)
    return tuple(sorted(selected))


def _case_rows(
    trend: dict[str, tuple],
    cs: dict[str, tuple],
) -> list[dict[str, Any]]:
    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)
    all_assets = {**trend, **cs}
    previous_trend = {symbol: 0.0 for symbol in trend}
    previous_cs = {symbol: 0.0 for symbol in cs}

    rows: list[dict[str, Any]] = []
    return_count = min(
        len(next(iter(trend.values()))),
        len(next(iter(cs.values()))),
    ) - 2

    for i in range(return_count):
        trend_gross = 0.0
        cs_gross = 0.0
        trend_turnover = 0.0
        cs_turnover = 0.0

        for symbol, bars in trend.items():
            value = bars[i + 2].open / bars[i + 1].open - 1.0
            weight = trend_weights[i][symbol]
            trend_gross += weight * value
            trend_turnover += abs(weight - previous_trend[symbol])
            previous_trend[symbol] = weight

        for symbol, bars in cs.items():
            value = bars[i + 2].open / bars[i + 1].open - 1.0
            weight = cs_weights[i][symbol]
            cs_gross += weight * value
            cs_turnover += abs(weight - previous_cs[symbol])
            previous_cs[symbol] = weight

        gross_open = 0.5 * trend_gross + 0.5 * cs_gross
        turnover = 0.5 * trend_turnover + 0.5 * cs_turnover
        portfolio_net = gross_open - (base.FEE_RATE + base.SLIPPAGE_RATE) * turnover

        proxy_values = []
        for bars in all_assets.values():
            previous_open = bars[i + 1].open
            current_open = bars[i + 2].open
            if previous_open <= 0:
                raise ValueError("Encountered non-positive open price")
            proxy_values.append(current_open / previous_open - 1.0)
        proxy_current = sum(proxy_values) / len(proxy_values)

        prior_decline = (
            _prior_close_return(all_assets, i, PRIOR_DECLINE_SESSIONS)
            if i >= PRIOR_DECLINE_SESSIONS
            else None
        )

        selected = _cs_selected_symbols(cs_weights[i])
        cs_spread = None
        if len(selected) == base.CS_TOP_N:
            selected_returns = []
            nonselected_returns = []
            for symbol, bars in cs.items():
                previous_open = bars[i + 1].open
                current_open = bars[i + 2].open
                value = current_open / previous_open - 1.0
                if symbol in selected:
                    selected_returns.append(value)
                else:
                    nonselected_returns.append(value)
            if not selected_returns or not nonselected_returns:
                raise ValueError("CS winner/nonwinner groups must both be non-empty")
            cs_spread = (
                sum(selected_returns) / len(selected_returns)
                - sum(nonselected_returns) / len(nonselected_returns)
            )

        rows.append(
            {
                "timestamp": next(iter(trend.values()))[i + 2].timestamp,
                "portfolio_net_return": portfolio_net,
                "trend_gross_return": trend_gross,
                "cs_gross_return": cs_gross,
                "turnover": turnover,
                "proxy_current_open_return": proxy_current,
                "prior_20d_proxy_close_return": prior_decline,
                "rebound_after_decline": (
                    prior_decline is not None
                    and prior_decline < 0.0
                    and proxy_current > 0.0
                ),
                "cs_winner_loser_spread": cs_spread,
                "cs_winner_reversal": cs_spread is not None and cs_spread < 0.0,
                "combined_reversal_rebound": (
                    prior_decline is not None
                    and prior_decline < 0.0
                    and proxy_current > 0.0
                    and cs_spread is not None
                    and cs_spread < 0.0
                ),
                "cs_selected_symbols": list(selected),
            }
        )

    return rows


def _max_drawdown_interval(rows: list[dict[str, Any]]) -> tuple[int, int, float]:
    equity = peak = 1.0
    peak_index = 0
    best = (0, 0, 0.0)
    for index, row in enumerate(rows[:RESEARCH_COUNT]):
        equity *= 1.0 + row["portfolio_net_return"]
        if equity > peak:
            peak = equity
            peak_index = index
        drawdown = 1.0 - equity / peak
        if drawdown > best[2]:
            best = (peak_index, index, drawdown)
    return best


def _summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    research = rows[:RESEARCH_COUNT]
    state = [r for r in research if r[field]]
    non_state = [r for r in research if not r[field]]

    def mean(values: list[float]) -> float | None:
        return sum(values) / len(values) if values else None

    def pf(values: list[float]) -> float | str:
        gross_profit = sum(v for v in values if v > 0.0)
        gross_loss = sum(-v for v in values if v < 0.0)
        if gross_loss > 0:
            return gross_profit / gross_loss
        return "inf" if gross_profit > 0 else 0.0

    state_returns = [r["portfolio_net_return"] for r in state]
    non_returns = [r["portfolio_net_return"] for r in non_state]
    worst_count = max(1, (len(research) * WORST_DAY_BUCKET_PERCENT + 99) // 100)
    worst = sorted(
        research,
        key=lambda r: r["portfolio_net_return"],
    )[:worst_count]

    return {
        "state": field,
        "observations": len(state),
        "fraction": len(state) / len(research) if research else 0.0,
        "mean_portfolio_return": mean(state_returns),
        "median_portfolio_return": (
            sorted(state_returns)[len(state_returns) // 2]
            if state_returns
            else None
        ),
        "positive_day_rate": (
            sum(v > 0.0 for v in state_returns) / len(state_returns)
            if state_returns
            else None
        ),
        "profit_factor": pf(state_returns),
        "non_state_observations": len(non_state),
        "non_state_mean_portfolio_return": mean(non_returns),
        "mean_difference_state_minus_non_state": (
            mean(state_returns) - mean(non_returns)
            if state_returns and non_returns
            else None
        ),
        "worst_5pct_observations": sum(bool(r[field]) for r in worst),
        "worst_5pct_fraction": (
            sum(bool(r[field]) for r in worst) / len(worst)
            if worst
            else 0.0
        ),
        "worst_5pct_enrichment_ratio": (
            (
                sum(bool(r[field]) for r in worst) / len(worst)
            ) / (len(state) / len(research))
            if state and worst
            else 0.0
        ),
    }


def _state_at_max_drawdown_onset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    peak_index, trough_index, max_dd = _max_drawdown_interval(rows)
    onset = min(peak_index + 1, RESEARCH_COUNT - 1)
    first_two = rows[onset : min(onset + 2, trough_index + 1)]
    return {
        "peak_index": peak_index,
        "trough_index": trough_index,
        "max_drawdown_percent": max_dd * 100.0,
        "onset_timestamp": rows[onset]["timestamp"].isoformat(),
        "onset_rebound_after_decline": rows[onset]["rebound_after_decline"],
        "onset_cs_winner_reversal": rows[onset]["cs_winner_reversal"],
        "onset_combined_reversal_rebound": rows[onset]["combined_reversal_rebound"],
        "first_two_reversal_rebound_count": sum(
            r["combined_reversal_rebound"] for r in first_two
        ),
    }


def _rolling_window_state_rates(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    width = RESEARCH_COUNT // 5
    bounds = tuple(
        (
            index * width,
            RESEARCH_COUNT if index == 4 else (index + 1) * width,
        )
        for index in range(5)
    )
    result = []
    for index, (start, end) in enumerate(bounds, start=1):
        segment = rows[start:end]
        negative = sum(r["portfolio_net_return"] < 0.0 for r in segment)
        state_days = sum(bool(r[field]) for r in segment)
        result.append(
            {
                "window_index": index,
                "start_index": start,
                "end_index_exclusive": end,
                "portfolio_negative_day_rate": negative / len(segment),
                "state_fraction": state_days / len(segment),
            }
        )
    return result


def _case_analysis(
    trend: dict[str, tuple],
    cs: dict[str, tuple],
) -> dict[str, Any]:
    rows = _case_rows(trend, cs)
    rebound = _summary(rows, "rebound_after_decline")
    reversal = _summary(rows, "cs_winner_reversal")
    combined = _summary(rows, "combined_reversal_rebound")

    windows = {
        "rebound_after_decline": _rolling_window_state_rates(rows, "rebound_after_decline"),
        "cs_winner_reversal": _rolling_window_state_rates(rows, "cs_winner_reversal"),
        "combined_reversal_rebound": _rolling_window_state_rates(rows, "combined_reversal_rebound"),
    }

    rebound_enriched = (
        rebound["observations"] >= 10
        and rebound["worst_5pct_enrichment_ratio"] > 1.0
        and (rebound["mean_difference_state_minus_non_state"] or 0.0) < 0.0
    )
    reversal_enriched = (
        reversal["observations"] >= 10
        and reversal["worst_5pct_enrichment_ratio"] > 1.0
        and (reversal["mean_difference_state_minus_non_state"] or 0.0) < 0.0
    )
    combined_enriched = (
        combined["observations"] >= 10
        and combined["worst_5pct_enrichment_ratio"] > 1.0
        and (combined["mean_difference_state_minus_non_state"] or 0.0) < 0.0
    )

    return {
        "research_counts": {
            "rows": len(rows),
            "eligible_rebound_rows": sum(
                r["prior_20d_proxy_close_return"] is not None for r in rows[:RESEARCH_COUNT]
            ),
            "eligible_cs_reversal_rows": sum(
                r["cs_winner_loser_spread"] is not None for r in rows[:RESEARCH_COUNT]
            ),
        },
        "states": {
            "rebound_after_decline": rebound,
            "cs_winner_reversal": reversal,
            "combined_reversal_rebound": combined,
        },
        "rolling_window_rates": windows,
        "max_drawdown_onset": _state_at_max_drawdown_onset(rows),
        "case_flags": {
            "rebound_enriched": rebound_enriched,
            "cs_reversal_enriched": reversal_enriched,
            "combined_enriched": combined_enriched,
        },
    }


def _consensus(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rebound = sum(case["case_flags"]["rebound_enriched"] for case in cases.values())
    reversal = sum(case["case_flags"]["cs_reversal_enriched"] for case in cases.values())
    combined = sum(case["case_flags"]["combined_enriched"] for case in cases.values())

    return {
        "replication_counts": {
            "rebound_enriched": rebound,
            "cs_reversal_enriched": reversal,
            "combined_enriched": combined,
        },
        "diagnostic_rule": (
            "A state is called enriched within a validation only when it has "
            ">=10 Research observations, a worst-5%-day enrichment ratio >1, "
            "and a lower mean portfolio return than non-state days. A replicated "
            "mechanism requires the same flag in >=3/4 validations. This rule "
            "is descriptive and creates no production decision."
        ),
        "interpretation": (
            "rebound_state_replicated"
            if rebound >= 3
            else "cs_reversal_state_replicated"
            if reversal >= 3
            else "combined_reversal_rebound_replicated"
            if combined >= 3
            else "no_replicated_reversal_rebound_state"
        ),
    }


def analyze(source_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    cases: dict[str, Any] = {}
    for case in CASES:
        trend, cs = _load_case(source_root, case)
        cases[case["name"]] = {
            "source": {
                "artifact_id": case["artifact_id"],
                "run_id": case["run_id"],
            },
            "analysis": _case_analysis(trend, cs),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "signal_reversal_rebound_diagnosis_2026_09_24",
        "status": "COMPLETED",
        "question": (
            "Are the candidate's worst Research days enriched for a fixed "
            "decline-then-rebound state and/or a fixed cross-sectional "
            "winner-to-nonwinner reversal state?"
        ),
        "scope": {
            "datasets": 4,
            "research_return_count_per_dataset": RESEARCH_COUNT,
            "prior_decline_sessions": PRIOR_DECLINE_SESSIONS,
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "new_data_downloads": False,
            "parameter_search": False,
            "asset_selection": False,
            "strategy_mutation": False,
            "gate_changes": False,
            "production_mutation": False,
        },
        "methodology": {
            "candidate_architecture_fixed": True,
            "trend_strategy_fixed": base.TREND_STRATEGY,
            "cs_lookback_sessions": base.CS_LOOKBACK,
            "cs_skip_sessions": base.CS_SKIP,
            "cs_rebalance_sessions": base.CS_REBALANCE,
            "cs_top_n": base.CS_TOP_N,
            "market_proxy": (
                "equal-weighted open-to-open return across the union of the "
                "13 validation assets, not an external index"
            ),
            "rebound_state": (
                "prior 20-session equal-weighted close-to-close proxy return < 0 "
                "and current equal-weighted open-to-open proxy return > 0"
            ),
            "cs_reversal_state": (
                "current return of the fixed top-2 CS winners minus the "
                "equal-weighted return of the three non-selected CS assets < 0"
            ),
            "combined_state": "rebound_state AND cs_reversal_state",
            "worst_bucket_percent": WORST_DAY_BUCKET_PERCENT,
            "replication_threshold": ">=3/4 validations",
            "minimum_state_observations": 10,
            "descriptive_not_causal": True,
        },
        "literature_context": {
            "primary_reference": (
                "Daniel, K. and Moskowitz, T. J. (2016), Momentum Crashes, "
                "Journal of Financial Economics 122(2), 221-247, "
                "https://doi.org/10.1016/j.jfineco.2015.12.002"
            ),
            "secondary_reference": (
                "Moreira, A. and Muir, T. (2017), Volatility-Managed Portfolios, "
                "Journal of Finance 72(4), 1611-1644, "
                "https://doi.org/10.1111/jofi.12513"
            ),
        },
        "cases": cases,
        "consensus": _consensus(cases),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["diagnostic_fingerprint"] = _fp(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = analyze(Path(args.source_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    print("SIGNAL_REVERSAL_REBOUND_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    print("CONSENSUS:", result["consensus"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
