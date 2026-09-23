"""Diagnose Rolling-WF failures against ex-ante and realized volatility regimes.

Diagnostic only: archived inputs only, no downloads, backtests, optimizations or orders.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

MIN_PF = 1.10
MAX_DD = 10.0
VOL_LOOKBACK = 20
LOW = 1 / 3
HIGH = 2 / 3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = {"timestamp", "open", "high", "low", "close", "volume"}
    if not rows or set(rows[0]) != expected:
        raise ValueError(f"Unexpected CSV schema: {path}")
    return [
        {
            "timestamp": datetime.fromisoformat(r["timestamp"]),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": float(r["volume"]),
        }
        for r in rows
    ]


def dataset_fingerprint(rows: list[dict[str, Any]]) -> str:
    payload = [
        {
            "timestamp": r["timestamp"].isoformat(),
            "open": r["open"],
            "high": r["high"],
            "low": r["low"],
            "close": r["close"],
            "volume": r["volume"],
        }
        for r in rows
    ]
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def log_returns(closes: list[float]) -> list[float]:
    return [math.log(b / a) for a, b in zip(closes, closes[1:])]


def annualized_vol(values: list[float]) -> float:
    return statistics.stdev(values) * math.sqrt(252.0) if len(values) >= 2 else 0.0


def percentile(values: list[float], value: float) -> float:
    return sum(v <= value for v in values) / len(values) if values else 0.5


def regime(p: float) -> str:
    if p < LOW:
        return "low"
    if p > HIGH:
        return "high"
    return "middle"


def candidate_values(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_per_trade": candidate["risk_per_trade"],
        "leverage": candidate["leverage"],
        "momentum.lookback": candidate["strategy"]["momentum"]["lookback"],
        "mean_reversion.window": candidate["strategy"]["mean_reversion"]["window"],
        "mean_reversion.threshold": candidate["strategy"]["mean_reversion"]["threshold"],
    }


def changed_parameters(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    a, b = candidate_values(left), candidate_values(right)
    return sorted(k for k in a if a[k] != b[k])


def flags(window: dict[str, Any]) -> dict[str, bool]:
    pf = float("inf") if window["profit_factor"] == "inf" else float(window["profit_factor"])
    return {
        "nonpositive_profit": float(window["net_profit_eur"]) <= 0.0,
        "profit_factor_failure": pf < MIN_PF,
        "drawdown_failure": float(window["max_drawdown_percent"]) > MAX_DD,
    }


def build_market_features(rolling: dict[str, Any], raw_by_symbol: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    n = int(rolling["research_candle_count"])
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()
    for ds in rolling["datasets"]:
        symbol = ds["symbol"]
        rows = raw_by_symbol[symbol][:n]
        closes = [r["close"] for r in rows]
        returns = log_returns(closes)
        rolling_vol: list[float | None] = [None] * len(rows)
        for end in range(VOL_LOOKBACK, len(rows)):
            rolling_vol[end] = annualized_vol(returns[end - VOL_LOOKBACK:end])
        for profile in ds["profiles"]:
            for geometry in ("small", "large"):
                for w in profile[geometry]["windows"]:
                    key = (symbol, geometry, int(w["window_index"]))
                    if key in seen:
                        continue
                    seen.add(key)
                    start, end = int(w["test_start_index"]), int(w["test_end_index"])
                    if not (0 <= start < end <= n):
                        raise ValueError(f"Window outside research range: {key}")
                    test_rows = rows[start:end]
                    test_returns = returns[start:end]
                    pre_returns = returns[start - VOL_LOOKBACK:start]
                    if len(pre_returns) < VOL_LOOKBACK:
                        raise ValueError(f"Insufficient pre-test history for {key}")
                    pre_vol = annualized_vol(pre_returns)
                    historical = [v for v in rolling_vol[VOL_LOOKBACK:start] if v is not None]
                    p = percentile(historical, pre_vol)
                    realized = annualized_vol(test_returns)
                    start_close, end_close = test_rows[0]["close"], test_rows[-1]["close"]
                    out.append({
                        "symbol": symbol,
                        "geometry": geometry,
                        "window_index": int(w["window_index"]),
                        "test_start": w["test_start"],
                        "test_end": w["test_end"],
                        "test_start_index": start,
                        "test_end_index": end,
                        "pre_test_vol_20d": pre_vol,
                        "pre_test_vol_percentile": p,
                        "pre_test_vol_regime": regime(p),
                        "test_realized_vol_pct": realized * 100.0,
                        "test_mean_abs_return_pct": statistics.mean(abs(x) for x in test_returns) * 100.0 if test_returns else 0.0,
                        "test_mean_range_pct": statistics.mean((r["high"] - r["low"]) / r["close"] for r in test_rows) * 100.0,
                        "test_return_pct": (end_close / start_close - 1.0) * 100.0,
                    })
    return out


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"evaluation_count": 0, "positive_profit_rate": 0.0, "pf_pass_rate": 0.0, "median_profit_eur": None}
    return {
        "evaluation_count": len(rows),
        "positive_profit_rate": sum(float(r["net_profit_eur"]) > 0 for r in rows) / len(rows),
        "pf_pass_rate": sum(not r["flags"]["profit_factor_failure"] for r in rows) / len(rows),
        "median_profit_eur": statistics.median(float(r["net_profit_eur"]) for r in rows),
    }


def analyze(rolling: dict[str, Any], archive_manifest: dict[str, Any], raw_dir: str | Path) -> dict[str, Any]:
    raw_root = Path(raw_dir)
    manifest_by_symbol = {d["symbol"]: d for d in archive_manifest["datasets"]}
    raw: dict[str, list[dict[str, Any]]] = {}
    integrity = []
    for ds in rolling["datasets"]:
        symbol = ds["symbol"]
        item = manifest_by_symbol[symbol]
        path = raw_root / symbol / "1d.csv"
        if sha256_file(path) != item["byte_sha256"]:
            raise ValueError(f"{symbol}: byte SHA-256 mismatch")
        rows = load_csv(path)
        if len(rows) != int(item["candle_count"]):
            raise ValueError(f"{symbol}: candle count mismatch")
        if dataset_fingerprint(rows) != item["dataset_fingerprint"]:
            raise ValueError(f"{symbol}: dataset fingerprint mismatch")
        research = rows[: int(rolling["research_candle_count"])]
        if dataset_fingerprint(research) != ds["research_fingerprint"]:
            raise ValueError(f"{symbol}: research fingerprint mismatch")
        raw[symbol] = rows
        integrity.append({
            "symbol": symbol,
            "full_candle_count": len(rows),
            "research_candle_count": len(research),
            "byte_sha256": item["byte_sha256"],
            "full_dataset_fingerprint": item["dataset_fingerprint"],
            "research_fingerprint": ds["research_fingerprint"],
        })

    market = build_market_features(rolling, raw)
    fmap = {(r["symbol"], r["geometry"], r["window_index"]): r for r in market}
    evaluations = []
    transitions = []
    for ds in rolling["datasets"]:
        symbol = ds["symbol"]
        for profile in ds["profiles"]:
            for geometry in ("small", "large"):
                windows = profile[geometry]["windows"]
                for w in windows:
                    m = fmap[(symbol, geometry, int(w["window_index"]))]
                    evaluations.append({
                        "symbol": symbol,
                        "selection_profile": profile["selection_profile"],
                        "geometry": geometry,
                        "window_index": int(w["window_index"]),
                        "net_profit_eur": float(w["net_profit_eur"]),
                        "profit_factor": w["profit_factor"],
                        "max_drawdown_percent": float(w["max_drawdown_percent"]),
                        "flags": flags(w),
                        "pre_test_vol_percentile": m["pre_test_vol_percentile"],
                        "pre_test_vol_regime": m["pre_test_vol_regime"],
                        "pre_test_vol_20d": m["pre_test_vol_20d"],
                        "test_realized_vol_pct": m["test_realized_vol_pct"],
                        "test_mean_abs_return_pct": m["test_mean_abs_return_pct"],
                        "test_mean_range_pct": m["test_mean_range_pct"],
                        "test_return_pct": m["test_return_pct"],
                    })
                for left, right in zip(windows, windows[1:]):
                    src = fmap[(symbol, geometry, int(left["window_index"]))]
                    dst = fmap[(symbol, geometry, int(right["window_index"]))]
                    changed = changed_parameters(left["candidate"], right["candidate"])
                    transitions.append({
                        "symbol": symbol,
                        "selection_profile": profile["selection_profile"],
                        "geometry": geometry,
                        "source_window": int(left["window_index"]),
                        "destination_window": int(right["window_index"]),
                        "changed_parameters": changed,
                        "migration": bool(changed),
                        "source_pre_test_vol_percentile": src["pre_test_vol_percentile"],
                        "destination_pre_test_vol_percentile": dst["pre_test_vol_percentile"],
                        "vol_percentile_delta": dst["pre_test_vol_percentile"] - src["pre_test_vol_percentile"],
                        "destination_positive_profit": float(right["net_profit_eur"]) > 0,
                        "destination_profit_factor_failure": flags(right)["profit_factor_failure"],
                        "destination_profit_eur": float(right["net_profit_eur"]),
                    })

    regimes = {}
    for geometry in ("small", "large"):
        ev = [r for r in evaluations if r["geometry"] == geometry]
        market_rows = [r for r in market if r["geometry"] == geometry]
        counts = Counter(r["pre_test_vol_regime"] for r in market_rows)
        groups: dict[str, Any] = {}
        for label in ("low", "middle", "high"):
            groups[label] = summary([r for r in ev if r["pre_test_vol_regime"] == label])
        regimes[geometry] = {"market_window_count": len(market_rows), "regime_counts": dict(counts), "by_regime": groups}

    def transition_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
        if not rows:
            return {"transition_count": 0, "migration_count": 0, "migration_rate": 0.0, "positive_destination_rate": 0.0, "pf_pass_rate": 0.0, "median_destination_profit_eur": None}
        return {
            "transition_count": len(rows),
            "migration_count": sum(r["migration"] for r in rows),
            "migration_rate": sum(r["migration"] for r in rows) / len(rows),
            "positive_destination_rate": sum(r["destination_positive_profit"] for r in rows) / len(rows),
            "pf_pass_rate": sum(not r["destination_profit_factor_failure"] for r in rows) / len(rows),
            "median_destination_profit_eur": statistics.median(r["destination_profit_eur"] for r in rows),
        }

    migration = {
        "transition_count": len(transitions),
        "migration_count": sum(r["migration"] for r in transitions),
        "stable_count": sum(not r["migration"] for r in transitions),
        "migration_rate": sum(r["migration"] for r in transitions) / len(transitions),
        "by_destination_regime": {},
        "by_volatility_shift": {},
        "parameter_associations": {},
    }
    for label in ("low", "middle", "high"):
        migration["by_destination_regime"][label] = transition_group([
            r for r in transitions
            if fmap[(r["symbol"], r["geometry"], r["destination_window"])]["pre_test_vol_regime"] == label
        ])
    shift_groups = {
        "contracting": lambda d: d < -0.10,
        "stable_band": lambda d: -0.10 <= d <= 0.10,
        "expanding": lambda d: d > 0.10,
    }
    for label, predicate in shift_groups.items():
        migration["by_volatility_shift"][label] = transition_group([r for r in transitions if predicate(r["vol_percentile_delta"])])

    for param in ("risk_per_trade", "leverage", "momentum.lookback", "mean_reversion.window", "mean_reversion.threshold"):
        changed = [r for r in transitions if param in r["changed_parameters"]]
        unchanged = [r for r in transitions if param not in r["changed_parameters"]]
        migration["parameter_associations"][param] = {
            "change_count": len(changed),
            "changed_median_vol_percentile_delta": statistics.median(r["vol_percentile_delta"] for r in changed) if changed else None,
            "unchanged_median_vol_percentile_delta": statistics.median(r["vol_percentile_delta"] for r in unchanged) if unchanged else None,
            "changed_positive_destination_rate": sum(r["destination_positive_profit"] for r in changed) / len(changed) if changed else 0.0,
            "changed_pf_pass_rate": sum(not r["destination_profit_factor_failure"] for r in changed) / len(changed) if changed else 0.0,
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "rolling_regime_volatility_failure_analysis",
        "source_diagnostic_fingerprint": rolling["diagnostic_fingerprint"],
        "source_code_version": rolling["code_version"],
        "source_target_count": rolling["target_count"],
        "source_research_candle_count": rolling["research_candle_count"],
        "source_universe": rolling["universe"],
        "volatility_definition": {
            "pre_test_lookback_days": VOL_LOOKBACK,
            "pre_test_regime_method": "historical_percentile_using_only_data_available_before_test_start",
            "regime_boundaries": {"low_below": LOW, "high_above": HIGH},
            "realized_volatility": "annualized_standard_deviation_of_log_close_returns_in_test_window",
            "diagnostic_shift_band": {"contracting_below": -0.10, "expanding_above": 0.10},
        },
        "archive_integrity": integrity,
        "market_features": market,
        "evaluation_count": len(evaluations),
        "regime_summary": regimes,
        "migration_summary": migration,
        "migrations": transitions,
        "interpretation_scope": {
            "diagnostic_only": True,
            "no_new_backtest": True,
            "no_new_optimization": True,
            "no_new_data_download": True,
            "uses_only_immutable_archived_raw_data": True,
            "associations_are_descriptive_not_causal": True,
            "evaluation_rows_repeat_market_windows_across_selection_profiles": True,
            "regime_labels_are_ex_ante_relative_to_each_test_start": True,
        },
        "safety": rolling["safety"],
    }
    result["analysis_fingerprint"] = hashlib.sha256(
        json.dumps({k: v for k, v in result.items() if k != "analysis_fingerprint"}, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()
    return result


def markdown(result: dict[str, Any]) -> str:
    def fmt(v: Any) -> str:
        return "n/a" if v is None else f"{v:.3f}"
    lines = [
        "# Rolling-WF Regime-/Volatilitäts-Failure-Analyse",
        "",
        f"- Analysis-Fingerprint: {result['analysis_fingerprint']}",
        f"- Source-Fingerprint: {result['source_diagnostic_fingerprint']}",
        f"- Research-Candles: {result['source_research_candle_count']}",
        "- Basis: immutable archivierte Rohdaten; keine neuen Downloads, Backtests oder Optimierungen",
        "",
        "## Failure-/Profitabilitätsassoziation nach ex-ante Volatilitätsregime",
        "",
        "| Geometrie | Regime | Market-Windows | Evaluationen | positive Destinationen | PF-Pass | Median Profit EUR |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for geometry, data in result["regime_summary"].items():
        for label, item in data["by_regime"].items():
            lines.append(f"| {geometry} | {label} | {data['regime_counts'].get(label, 0)} | {item['evaluation_count']} | {item['positive_profit_rate']:.3f} | {item['pf_pass_rate']:.3f} | {fmt(item['median_profit_eur'])} |")
    lines += [
        "",
        "## Kandidatenmigration und Volatilitätswechsel",
        "",
        "| Kategorie | Transitions | Migrationen | Migration-Rate | positive Destinationen | PF-Pass | Median Profit EUR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for section in ("by_volatility_shift", "by_destination_regime"):
        for label, item in result["migration_summary"][section].items():
            lines.append(f"| {section}:{label} | {item['transition_count']} | {item['migration_count']} | {item['migration_rate']:.3f} | {item['positive_destination_rate']:.3f} | {item['pf_pass_rate']:.3f} | {fmt(item['median_destination_profit_eur'])} |")
    lines += [
        "",
        "## Parameterwechsel und Volatilitätswechsel",
        "",
        "| Parameter | Änderung Count | Median Vol.-Perzentil-Delta bei Änderung | ohne Änderung | positive Destinationen bei Änderung | PF-Pass bei Änderung |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for param, item in result["migration_summary"]["parameter_associations"].items():
        lines.append(f"| {param} | {item['change_count']} | {fmt(item['changed_median_vol_percentile_delta'])} | {fmt(item['unchanged_median_vol_percentile_delta'])} | {item['changed_positive_destination_rate']:.3f} | {item['changed_pf_pass_rate']:.3f} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "Die Regimezuordnung ist ex-ante relativ zum jeweiligen Teststart und dient der Beschreibung der Marktbedingungen.",
        "Performancezeilen wiederholen dasselbe Marktfenster über die vier Selection-Profile und sind daher keine vier unabhängigen Marktbeobachtungen.",
        "Zusammenhänge zwischen Volatilitätsregime, Kandidatenmigration und Failure-Kriterien sind deskriptiv und nicht kausal.",
        "Keine beobachtete Assoziation verändert automatisch Parameterraum, Selection-Profile oder Gates.",
        "",
        "Paper-Only: True; Live-Trading: False; Orders: False.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rolling-json", required=True)
    parser.add_argument("--archive-manifest", required=True)
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output-dir", default="research/regime_volatility")
    args = parser.parse_args()
    rolling = json.loads(Path(args.rolling_json).read_text(encoding="utf-8"))
    archive = json.loads(Path(args.archive_manifest).read_text(encoding="utf-8"))
    result = analyze(rolling, archive, args.raw_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "regime_volatility_analysis.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    (out / "regime_volatility_analysis.md").write_text(markdown(result), encoding="utf-8")
    print("REGIME_VOLATILITY_ANALYSIS: COMPLETED")
    print("ANALYSIS_FINGERPRINT:", result["analysis_fingerprint"])
    print("EVALUATIONS:", result["evaluation_count"])
    print("TRANSITIONS:", len(result["migrations"]))
    print("PAPER_ONLY:", result["safety"]["paper_only"])
    print("LIVE_TRADING_ENABLED:", result["safety"]["live_trading_enabled"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
