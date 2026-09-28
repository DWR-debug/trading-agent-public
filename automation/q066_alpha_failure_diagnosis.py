"""Q066 fixed-result alpha failure-mechanism diagnosis.

This module reconstructs row-level exposure and return paths from the two
immutable Q041/Q045 performance artifacts. It performs no new market-data
acquisition, selection, optimization or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import statistics
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable


TRIAL_ID = "T-2026-09-28-066"
COST_RATE = 0.0015
Q041 = {
    "trial_id": "T-2026-09-27-060",
    "artifact_digest": "sha256:d960f60ebb21a60624d27a33f6eafce561b24f62922f0a26824e418055eed4db",
    "report_fingerprint": "18b4529b47e3a768f4b92c3ac7f7bff415585a13a5c8bc17f8ed6790834d63d5",
    "runner": "automation/q041_alpha_multiarm_performance.py",
    "runner_blob_sha": "cc9e76a1748db85db23b76cba209d7faf147847b",
    "universe": "validation_2026_09_27_q039_price_only_alpha_pit",
    "symbols": ("IVE", "IWL", "DLN", "DHS", "DON", "DES", "USRT", "ITB"),
}
Q045 = {
    "trial_id": "T-2026-09-27-065",
    "artifact_digest": "sha256:7126b5d84eedbaed17e53124a96e8f8b0c987de0ca2410ea4ef61a796d2ba6a7",
    "report_fingerprint": "0b29881c2405c4498b2327d8252a8db0c41b32deff18bd9482cd08b3abb8fe0a",
    "runner": "automation/q045_fixed_alpha_replication_performance.py",
    "runner_blob_sha": "a27fa60a892d31ae62cf9a85fa3d9b33b538670b",
    "universe": "validation_2026_09_27_q043_fresh_alpha_replication",
    "symbols": ("AON", "CVS", "ADSK", "BA", "T", "F", "LUV", "NFLX"),
}


def canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def hhi(weights: Iterable[float]) -> float:
    values = [abs(float(x)) for x in weights]
    total = sum(values)
    if total <= 0.0:
        return 0.0
    return sum((x / total) ** 2 for x in values)


def median(values: list[float]) -> float:
    return statistics.median(values)


def std_population(values: list[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def classify_regime(market_returns: list[float]) -> list[str]:
    """Assign each evaluated day using only prior return history."""
    labels: list[str] = []
    vols: list[float | None] = [None] * len(market_returns)
    for i in range(len(market_returns)):
        if i >= 21:
            vols[i] = std_population(market_returns[i - 21 : i])
        if i < 273 or vols[i] is None:
            labels.append("UNDEFINED_EARLY")
            continue
        prior_vols = [v for v in vols[i - 252 : i] if v is not None]
        threshold = median(prior_vols)
        trend_return = math.prod(1.0 + x for x in market_returns[i - 63 : i]) - 1.0
        trend = "UPTREND" if trend_return >= 0.0 else "DOWNTREND"
        vol = "HIGHVOL" if vols[i] >= threshold else "LOWVOL"
        labels.append(f"{trend}_{vol}")
    return labels


def find_manifest(root: Path) -> Path:
    paths = sorted(root.rglob("coverage_preflight_*.json"))
    if not paths:
        raise FileNotFoundError(f"coverage manifest not found under {root}")
    return paths[-1]


def localize_manifest(manifest_path: Path, root: Path) -> Path:
    source = json.loads(manifest_path.read_text(encoding="utf-8"))
    localized = json.loads(json.dumps(source))
    datasets = localized.get("data_snapshot", {}).get("datasets", [])
    for item in datasets:
        raw = Path(str(item["path"]))
        if raw.is_absolute() and raw.exists():
            item["path"] = str(raw)
            continue
        symbol = str(item["symbol"])
        interval = str(item.get("interval", "1d"))
        candidates = sorted(root.rglob(f"{symbol}/{interval}.csv"))
        if len(candidates) != 1:
            raise FileNotFoundError(
                f"expected exactly one extracted dataset for {symbol}/{interval}, found {len(candidates)}"
            )
        item["path"] = str(candidates[0])
    target = root / "_localized_q066_manifest.json"
    target.write_text(
        json.dumps(localized, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return target


def load_assets(root: Path, expected: dict) -> tuple[dict, dict]:
    from data.canonical_snapshot import load_frozen_snapshot

    manifest_path = find_manifest(root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") not in {"coverage_passed", "COVERAGE_PASSED"}:
        raise ValueError("coverage manifest is not passed")
    if manifest.get("universe") != expected["universe"]:
        raise ValueError("universe mismatch")
    if tuple(manifest.get("symbols", ())) != expected["symbols"]:
        raise ValueError("symbol mismatch")
    if int(manifest.get("target_common_calendar", -1)) != 3500:
        raise ValueError("target calendar mismatch")
    safety = {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    if manifest.get("safety") != safety:
        raise ValueError("coverage safety mismatch")
    localized = localize_manifest(manifest_path, root)
    assets = load_frozen_snapshot(localized)
    if tuple(assets) != expected["symbols"]:
        raise ValueError("loaded symbol mismatch")
    if any(len(v) != 3500 for v in assets.values()):
        raise ValueError("frozen geometry mismatch")
    return assets, manifest


def find_report(root: Path) -> tuple[Path, dict]:
    paths = sorted(root.rglob("performance_report.json"))
    if not paths:
        raise FileNotFoundError(f"performance report not found under {root}")
    path = paths[-1]
    data = json.loads(path.read_text(encoding="utf-8"))
    return path, data


def verify_source_blob(path: Path, expected_sha: str) -> str:
    actual = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
    if actual != expected_sha:
        raise RuntimeError(f"source blob mismatch for {path}: {actual} != {expected_sha}")
    return actual


def build_weights(module, assets: dict, q045: bool) -> dict[str, tuple[dict[str, float], ...]]:
    if q045:
        arms = {
            "CONTROL": module._control(assets),
            "A1_TSM_CONSENSUS": module._a1(assets),
            "A2_CS_MOMENTUM_TOP2": module._a2(assets),
            "A3_RESIDUAL_MOMENTUM_TOP2": module._a3(assets),
            "A5_LOW_BETA_TOP2": module._a5(assets),
            "A1B_52W_HIGH_TOP2": module._a1b(assets),
            "A6_OVERNIGHT_TUGWAR_TOP2": module._a6(assets),
        }
        arms["ENSEMBLE_ALL6"] = module._avg(
            [
                arms["A1_TSM_CONSENSUS"],
                arms["A2_CS_MOMENTUM_TOP2"],
                arms["A3_RESIDUAL_MOMENTUM_TOP2"],
                arms["A5_LOW_BETA_TOP2"],
                arms["A1B_52W_HIGH_TOP2"],
                arms["A6_OVERNIGHT_TUGWAR_TOP2"],
            ]
        )
        return arms
    return {
        "CONTROL": module._control_weights(assets),
        "A1_TSM_CONSENSUS": module._a1_weights(assets),
        "A2_CS_MOMENTUM_TOP2": module._a2_weights(assets),
        "A3_RESIDUAL_MOMENTUM_TOP2": module._a3_weights(assets),
        "A5_LOW_BETA_TOP2": module._a5_weights(assets),
    }


def asset_returns(assets: dict, symbols: tuple[str, ...]) -> list[list[float]]:
    rows: list[list[float]] = []
    for i in range(3498):
        rows.append(
            [
                assets[s][i + 2].open / assets[s][i + 1].open - 1.0
                for s in symbols
            ]
        )
    return rows


def timestamps(assets: dict, symbol: str) -> list[str]:
    return [b.timestamp.isoformat() for b in assets[symbol][2:3500]]


def compute_paths(
    assets: dict, symbols: tuple[str, ...], weights: tuple[dict[str, float], ...]
) -> dict:
    returns = asset_returns(assets, symbols)
    prev = {s: 0.0 for s in symbols}
    daily: list[dict] = []
    symbol_series = {s: [] for s in symbols}
    gross_exposure: list[float] = []
    hhi_series: list[float] = []
    top1_series: list[float] = []
    top2_series: list[float] = []
    turnover: list[float] = []
    gross: list[float] = []
    net: list[float] = []
    for i, row in enumerate(returns):
        w = {s: float(weights[i].get(s, 0.0)) for s in symbols}
        deltas = {s: abs(w[s] - prev[s]) for s in symbols}
        turn = sum(deltas.values())
        g = sum(w[s] * row[k] for k, s in enumerate(symbols))
        n = g - COST_RATE * turn
        gross_exposure.append(sum(abs(x) for x in w.values()))
        hhi_series.append(hhi(w.values()))
        ordered = sorted((abs(x) for x in w.values()), reverse=True)
        top1_series.append(ordered[0] if ordered else 0.0)
        top2_series.append(sum(ordered[:2]))
        turnover.append(turn)
        gross.append(g)
        net.append(n)
        for k, s in enumerate(symbols):
            symbol_series[s].append(
                w[s] * row[k] - COST_RATE * deltas[s]
            )
        daily.append(
            {
                "timestamp": timestamps(assets, symbols[0])[i],
                "gross": g,
                "net": n,
                "turnover": turn,
                "gross_exposure": gross_exposure[-1],
                "hhi": hhi_series[-1],
            }
        )
        prev = w
    return {
        "daily": daily,
        "gross": gross,
        "net": net,
        "turnover": turnover,
        "gross_exposure": gross_exposure,
        "hhi": hhi_series,
        "top1_share": top1_series,
        "top2_share": top2_series,
        "symbol_series": symbol_series,
    }


def stats(values: list[float]) -> dict:
    if not values:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "positive_day_ratio": 0.0,
            "day_count": 0,
        }
    equity = peak = 1.0
    gp = gl = 0.0
    positives = 0
    max_dd = 0.0
    for x in values:
        equity *= 1.0 + x
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0.0 else 1.0)
        if x > 0:
            gp += x
            positives += 1
        elif x < 0:
            gl -= x
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gp / gl if gl else ("inf" if gp else 0.0),
        "positive_day_ratio": positives / len(values),
        "day_count": len(values),
    }


def summary(values: list[float]) -> dict:
    r = stats(values[:2798])
    h = stats(values[2798:3498])
    width = 2798 // 5
    wins = [
        stats(values[k * width : 2798 if k == 4 else (k + 1) * width])
        for k in range(5)
    ]
    gain = sum(max(x["period_return"], 0.0) for x in wins)
    loss = -sum(min(x["period_return"], 0.0) for x in wins)
    return {
        "research": r,
        "holdout": h,
        "rolling_windows": wins,
        "rolling_profit_factor": gain / loss if loss else ("inf" if gain else 0.0),
        "rolling_profitable_window_ratio": sum(
            x["period_return"] > 0.0 for x in wins
        )
        / 5.0,
        "rolling_average_drawdown_percent": sum(
            x["max_drawdown_percent"] for x in wins
        )
        / 5.0,
        "oos_to_is_return_ratio": h["period_return"] / r["period_return"]
        if r["period_return"] > 0.0
        else 0.0,
    }


def close_enough(a, b, tol=1e-12) -> bool:
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    return math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=tol)


def verify_report_fingerprint(report: dict, expected: str) -> bool:
    payload = dict(report)
    actual = payload.pop("report_fingerprint", None)
    return actual == expected and fingerprint(payload) == expected


def verify_aggregate_report(paths: dict, report: dict) -> bool:
    for arm, series in paths.items():
        stored = report["arms"][arm]["base"]
        reconstructed = summary(series["net"])
        for period in ("research", "holdout"):
            for key in ("period_return", "max_drawdown_percent", "positive_day_ratio", "day_count"):
                if not close_enough(stored[period][key], reconstructed[period][key]):
                    return False
            if not close_enough(stored[period]["profit_factor"], reconstructed[period]["profit_factor"]):
                return False
        for key in (
            "rolling_profit_factor",
            "rolling_profitable_window_ratio",
            "rolling_average_drawdown_percent",
            "oos_to_is_return_ratio",
        ):
            if not close_enough(report["arms"][arm]["base"][key], reconstructed[key]):
                return False
    return True


def max_drawdown_interval(values: list[float]) -> dict:
    equity = peak_equity = 1.0
    peak_idx = -1
    best_dd = 0.0
    best_start = best_end = 0
    for i, x in enumerate(values):
        equity *= 1.0 + x
        if equity > peak_equity:
            peak_equity = equity
            peak_idx = i
        dd = 1.0 - equity / peak_equity if equity > 0 else 1.0
        if dd > best_dd:
            best_dd = dd
            best_start = peak_idx + 1
            best_end = i
    return {
        "start_index": best_start,
        "end_index": best_end,
        "length": best_end - best_start + 1,
        "max_drawdown_percent": best_dd * 100.0,
    }


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def pearson(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    x = a[:n]
    y = b[:n]
    if n < 2:
        return 0.0
    ax = statistics.fmean(x)
    ay = statistics.fmean(y)
    vx = sum((v - ax) ** 2 for v in x)
    vy = sum((v - ay) ** 2 for v in y)
    if vx <= 0 or vy <= 0:
        return 0.0
    return sum((xx - ax) * (yy - ay) for xx, yy in zip(x, y)) / math.sqrt(vx * vy)


def top_share(values: list[float], fraction: float) -> float:
    positives = sorted((x for x in values if x > 0.0), reverse=True)
    if not positives:
        return 0.0
    k = max(1, math.ceil(len(positives) * fraction))
    total = sum(positives)
    return sum(positives[:k]) / total if total else 0.0


def symbol_diagnostics(
    assets: dict,
    symbols: tuple[str, ...],
    weights: tuple[dict[str, float], ...],
    series: dict,
) -> dict:
    returns = asset_returns(assets, symbols)
    prev = {s: 0.0 for s in symbols}
    rows = {s: [] for s in symbols}
    exposure_rows = {s: [] for s in symbols}
    for i, row in enumerate(returns):
        w = {s: float(weights[i].get(s, 0.0)) for s in symbols}
        for k, s in enumerate(symbols):
            rows[s].append(w[s] * row[k] - COST_RATE * abs(w[s] - prev[s]))
            exposure_rows[s].append(w[s])
        prev = w
    dd = max_drawdown_interval(series["net"])
    by_symbol = {}
    for s in symbols:
        vals = rows[s]
        by_symbol[s] = {
            "mean_weight": mean(exposure_rows[s]),
            "max_weight": max(exposure_rows[s]),
            "gross_return_contribution": sum(
                float(weights[i].get(s, 0.0)) * returns[i][symbols.index(s)]
                for i in range(len(returns))
            ),
            "net_contribution": sum(vals),
            "cost_contribution": -COST_RATE * sum(
                abs(float(weights[i].get(s, 0.0)) - (0.0 if i == 0 else float(weights[i - 1].get(s, 0.0))))
                for i in range(len(returns))
            ),
            "max_drawdown_interval_net_contribution": sum(
                vals[dd["start_index"] : dd["end_index"] + 1]
            ),
        }
    return {
        "global": by_symbol,
        "research": {
            s: {
                "mean_weight": mean(exposure_rows[s][:2798]),
                "net_contribution": sum(rows[s][:2798]),
            }
            for s in symbols
        },
        "holdout": {
            s: {
                "mean_weight": mean(exposure_rows[s][2798:3498]),
                "net_contribution": sum(rows[s][2798:3498]),
            }
            for s in symbols
        },
    }


def exposure_diagnostics(series: dict) -> dict:
    return {
        "mean_gross_exposure": mean(series["gross_exposure"]),
        "max_gross_exposure": max(series["gross_exposure"]),
        "mean_hhi": mean(series["hhi"]),
        "max_hhi": max(series["hhi"]),
        "mean_top1_share": mean(series["top1_share"]),
        "mean_top2_share": mean(series["top2_share"]),
        "active_days": sum(x > 0 for x in series["gross_exposure"]),
        "active_day_fraction": mean([1.0 if x > 0 else 0.0 for x in series["gross_exposure"]]),
    }


def turnover_diagnostics(series: dict) -> dict:
    daily_cost = [COST_RATE * x for x in series["turnover"]]
    return {
        "turnover_sum": sum(series["turnover"]),
        "turnover_mean": mean(series["turnover"]),
        "base_cost_drag_simple": sum(daily_cost),
        "turnover_top10pct_share": top_share(series["turnover"], 0.10),
    }


def return_drawdown_diagnostics(series: dict) -> dict:
    net = series["net"]
    underwater = []
    eq = peak = 1.0
    for x in net:
        eq *= 1.0 + x
        peak = max(peak, eq)
        underwater.append(eq < peak)
    negatives = [abs(x) for x in net if x < 0]
    worst_interval = max_drawdown_interval(net)
    return {
        "max_drawdown_interval": worst_interval,
        "underwater_fraction": mean([1.0 if x else 0.0 for x in underwater]),
        "negative_day_fraction": mean([1.0 if x < 0 else 0.0 for x in net]),
        "worst_5pct_negative_loss_share": top_share(negatives, 0.05),
        "underwater_simple_return": sum(x for x, u in zip(net, underwater) if u),
        "worst_drawdown_interval_simple_return": sum(
            net[worst_interval["start_index"] : worst_interval["end_index"] + 1]
        ),
    }


def regime_diagnostics(series: dict, regimes: list[str]) -> dict:
    grouped: dict[str, list[float]] = {}
    for label, value in zip(regimes, series["net"]):
        grouped.setdefault(label, []).append(value)
    out = {}
    for label, vals in grouped.items():
        out[label] = {
            "day_count": len(vals),
            "compound_return": math.prod(1.0 + x for x in vals) - 1.0 if vals else 0.0,
            "simple_return_sum": sum(vals),
            "mean_daily_return": mean(vals),
            "negative_day_fraction": mean([1.0 if x < 0 else 0.0 for x in vals]),
        }
    return out


def overlap_diagnostics(
    weights_by_arm: dict[str, tuple[dict[str, float], ...]],
    control_underwater: list[bool],
) -> dict:
    arms = [
        k
        for k in weights_by_arm
        if k != "CONTROL" and k != "ENSEMBLE_ALL6"
    ]
    pairs = {}
    for i, a in enumerate(arms):
        for b in arms[i + 1 :]:
            all_values = []
            adverse_values = []
            for j in range(len(weights_by_arm[a])):
                sa = {s for s, w in weights_by_arm[a][j].items() if abs(float(w)) > 1e-12}
                sb = {s for s, w in weights_by_arm[b][j].items() if abs(float(w)) > 1e-12}
                value = jaccard(sa, sb)
                all_values.append(value)
                if control_underwater[j]:
                    adverse_values.append(value)
            pairs[f"{a}__{b}"] = {
                "mean_jaccard_all_days": mean(all_values),
                "mean_jaccard_control_underwater": mean(adverse_values),
                "underwater_observation_count": len(adverse_values),
            }
    return pairs


def correlation_diagnostics(series_by_arm: dict[str, dict], control_underwater: list[bool]) -> dict:
    arms = list(series_by_arm)
    overall = {}
    adverse = {}
    for a in arms:
        overall[a] = {}
        adverse[a] = {}
        for b in arms:
            overall[a][b] = 1.0 if a == b else pearson(
                series_by_arm[a]["net"], series_by_arm[b]["net"]
            )
            ax = [x for x, keep in zip(series_by_arm[a]["net"], control_underwater) if keep]
            bx = [x for x, keep in zip(series_by_arm[b]["net"], control_underwater) if keep]
            adverse[a][b] = 1.0 if a == b else pearson(ax, bx)
    return {"overall": overall, "control_underwater": adverse}


def control_sleeve_diagnostics(module, assets: dict, control_series: dict, symbols: tuple[str, ...]) -> dict:
    trend = module._build_weight_path(assets, "sma_50_200_inverse_vol")
    cs = module._cs_weights(assets)
    returns = asset_returns(assets, symbols)
    trend_gross = []
    cs_gross = []
    trend_turn = []
    cs_turn = []
    prev_tr = {s: 0.0 for s in symbols}
    prev_cs = {s: 0.0 for s in symbols}
    for i, row in enumerate(returns):
        tw = {s: 0.5 * float(trend[i].get(s, 0.0)) for s in symbols}
        cw = {s: 0.5 * float(cs[i].get(s, 0.0)) for s in symbols}
        trend_gross.append(sum(tw[s] * row[k] for k, s in enumerate(symbols)))
        cs_gross.append(sum(cw[s] * row[k] for k, s in enumerate(symbols)))
        trend_turn.append(sum(abs(tw[s] - prev_tr[s]) for s in symbols))
        cs_turn.append(sum(abs(cw[s] - prev_cs[s]) for s in symbols))
        prev_tr = tw
        prev_cs = cw
    dd = control_series["return_drawdown"]["max_drawdown_interval"]
    overlap = [
        jaccard(
            {s for s, w in trend[i].items() if abs(float(w)) > 1e-12},
            {s for s, w in cs[i].items() if abs(float(w)) > 1e-12},
        )
        for i in range(len(trend))
    ]
    sleeve_corr = pearson(trend_gross, cs_gross)
    return {
        "trend_gross_contribution_simple_sum": sum(trend_gross),
        "cs_gross_contribution_simple_sum": sum(cs_gross),
        "trend_mean_exposure": mean([sum(abs(float(v)) for v in x.values()) for x in trend]),
        "cs_mean_exposure": mean([sum(abs(float(v)) for v in x.values()) for x in cs]),
        "trend_turnover_sum": sum(trend_turn),
        "cs_turnover_sum": sum(cs_turn),
        "trend_cs_signal_overlap_mean_jaccard": mean(overlap),
        "trend_cs_gross_return_correlation": sleeve_corr,
        "worst_drawdown_interval": {
            "trend_gross_simple_contribution": sum(trend_gross[dd["start_index"] : dd["end_index"] + 1]),
            "cs_gross_simple_contribution": sum(cs_gross[dd["start_index"] : dd["end_index"] + 1]),
            "control_cost_drag": -COST_RATE * sum(
                control_series["turnover"][dd["start_index"] : dd["end_index"] + 1]
            ),
        },
    }


def analyze_universe(root: Path, expected: dict, prereg: dict, q045: bool) -> dict:
    assets, manifest = load_assets(root, expected)
    report_path, report = find_report(root)
    if report.get("trial_id") != expected["trial_id"]:
        raise ValueError("performance trial id mismatch")
    if not verify_report_fingerprint(report, expected["report_fingerprint"]):
        raise ValueError("performance report fingerprint mismatch")
    module_name = (
        "automation.q045_fixed_alpha_replication_performance"
        if q045
        else "automation.q041_alpha_multiarm_performance"
    )
    module = importlib.import_module(module_name)
    verify_source_blob(Path(expected["runner"]), expected["runner_blob_sha"])
    weights_by_arm = build_weights(module, assets, q045)
    series_by_arm = {
        arm: compute_paths(assets, expected["symbols"], weights)
        for arm, weights in weights_by_arm.items()
    }
    exact = verify_aggregate_report(series_by_arm, report)
    if not exact:
        raise RuntimeError(f"aggregate reconstruction mismatch for {expected['trial_id']}")
    return_matrix = asset_returns(assets, expected["symbols"])
    market_returns = [mean(row) for row in return_matrix]
    regimes = classify_regime(market_returns)
    control_net = series_by_arm["CONTROL"]["net"]
    eq = peak = 1.0
    control_underwater = []
    for x in control_net:
        eq *= 1.0 + x
        peak = max(peak, eq)
        control_underwater.append(eq < peak)
    analyses = {}
    for arm, series in series_by_arm.items():
        symbol = symbol_diagnostics(
            assets, expected["symbols"], weights_by_arm[arm], series
        )
        analyses[arm] = {
            "stored_gate_count": report["arms"][arm]["gates_passed"],
            "stored_gate_total": report["arms"][arm]["gates_total"],
            "reconstructed_summary": summary(series["net"]),
            "exposure": exposure_diagnostics(series),
            "turnover": turnover_diagnostics(series),
            "return_drawdown": return_drawdown_diagnostics(series),
            "regimes": regime_diagnostics(series, regimes),
            "symbols": symbol,
        }
        if arm == "CONTROL":
            analyses[arm]["sleeves"] = control_sleeve_diagnostics(
                module, assets, analyses[arm], expected["symbols"]
            )
    return {
        "source": {
            "trial_id": expected["trial_id"],
            "artifact_digest": expected["artifact_digest"],
            "report_fingerprint": expected["report_fingerprint"],
            "report_path": str(report_path.relative_to(root)),
            "manifest_path": str(find_manifest(root).relative_to(root)),
            "snapshot_fingerprint": manifest.get("snapshot_fingerprint"),
            "symbols": list(expected["symbols"]),
        },
        "reconstruction": {
            "aggregate_reconstruction_exact": exact,
            "no_new_market_data": True,
            "source_runner_blob_sha": expected["runner_blob_sha"],
        },
        "arms": analyses,
        "weights_by_arm": weights_by_arm,
        "series_by_arm": series_by_arm,
        "regimes": regimes,
        "control_underwater": control_underwater,
        "overlap": overlap_diagnostics(weights_by_arm, control_underwater),
        "correlation": correlation_diagnostics(series_by_arm, control_underwater),
    }


def strip_internal(data: dict) -> dict:
    out = dict(data)
    out.pop("weights_by_arm", None)
    out.pop("series_by_arm", None)
    out.pop("regimes", None)
    out.pop("control_underwater", None)
    return out


def executive_summary(q041: dict, q045: dict) -> dict:
    def lead(report: dict) -> dict:
        arms = report["arms"]
        control = arms["CONTROL"]
        return {
            arm: {
                "research_max_drawdown_pct": v["return_drawdown"]["max_drawdown_interval"]["max_drawdown_percent"],
                "holdout_max_drawdown_pct": v["return_drawdown"]["max_drawdown_interval"]["max_drawdown_percent"],
                "mean_gross_exposure": v["exposure"]["mean_gross_exposure"],
                "mean_hhi": v["exposure"]["mean_hhi"],
                "turnover_sum": v["turnover"]["turnover_sum"],
                "base_cost_drag_simple": v["turnover"]["base_cost_drag_simple"],
            }
            for arm, v in arms.items()
        } | {
            "control_underwater_fraction": control["return_drawdown"]["underwater_fraction"],
            "control_worst_5pct_negative_loss_share": control["return_drawdown"]["worst_5pct_negative_loss_share"],
        }
    common = sorted(set(q041["arms"]) & set(q045["arms"]))
    return {
        "common_arms": common,
        "q041": lead(q041),
        "q045": lead(q045),
        "descriptive_scope": [
            "Repeated drawdown dimensions are exposure/cross-sectional concentration, adverse-period overlap/correlation and turnover cost drag only where the decomposition shows them.",
            "No causal attribution or post-hoc strategy preference is inferred from these descriptive results.",
            "The fixed 13-gate contract remains unchanged; Q066 does not authorize a new performance trial or promotion."
        ]
    }


def markdown_report(result: dict) -> str:
    lines = [
        "# Q066 — Alpha Failure-Mechanism Diagnosis",
        "",
        "Status: **COMPLETED_DIAGNOSTIC_ONLY**",
        "",
        "This report reconstructs the fixed Q041/T060 and Q045/T065 return/exposure paths from immutable Actions artifacts. It does not perform parameter search, asset selection, new market-data acquisition, a new performance trial, or promotion.",
        "",
        "## Executive summary",
        "",
    ]
    for universe in ("q041", "q045"):
        e = result["executive_summary"][universe]
        lines.append(f"### {universe.upper()}")
        lines.append("")
        for arm, m in e.items():
            if arm.startswith("control_") or arm.startswith("common_"):
                continue
            lines.append(
                f"- {arm}: mean gross exposure={m['mean_gross_exposure']:.4f}; "
                f"mean HHI={m['mean_hhi']:.4f}; turnover sum={m['turnover_sum']:.4f}; "
                f"base cost drag(simple)={m['base_cost_drag_simple']:.6f}."
            )
        lines.append(
            f"- CONTROL underwater fraction={e['control_underwater_fraction']:.4f}; "
            f"worst 5% negative-loss share={e['control_worst_5pct_negative_loss_share']:.4f}."
        )
        lines.append("")
    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "The diagnosis is descriptive. Shared exposure, overlap, correlation or turnover patterns are evidence about co-movement and transmission of risk, not proof of a causal driver.",
            "",
            "## Reconstruction",
            "",
            f"- Q041 exact aggregate reconstruction: {result['reconstruction']['q041']['aggregate_reconstruction_exact']}",
            f"- Q045 exact aggregate reconstruction: {result['reconstruction']['q045']['aggregate_reconstruction_exact']}",
            "",
            "## Governance",
            "",
            "- New performance evaluation: false",
            "- Selection/ranking: false",
            "- Holdout used for selection: false",
            "- Promotion: false",
            "- Safety: paper-only; live trading disabled; orders disabled.",
            "",
        ]
    )
    return "\n".join(lines)


def run(preregistration: Path, q041_root: Path, q045_root: Path, output: Path, markdown: Path) -> dict:
    prereg = json.loads(preregistration.read_text(encoding="utf-8"))
    if prereg.get("trial_id") != TRIAL_ID:
        raise ValueError("Q066 preregistration mismatch")
    if prereg.get("status") != "PREREGISTERED_DIAGNOSTIC_ONLY":
        raise ValueError("Q066 status mismatch")
    if prereg.get("governance", {}).get("new_performance_evaluation") is not False:
        raise ValueError("Q066 performance governance mismatch")
    from config import settings
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("Safety contract violated")
    q041 = analyze_universe(q041_root, Q041, prereg, q045=False)
    q045 = analyze_universe(q045_root, Q045, prereg, q045=True)
    result = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "status": "COMPLETED_DIAGNOSTIC_ONLY",
        "diagnostic_method": "fixed-result row-level reconstruction from immutable Q041/Q045 Actions artifacts",
        "source_artifacts": {"q041": Q041, "q045": Q045},
        "reconstruction": {
            "q041": q041["reconstruction"],
            "q045": q045["reconstruction"],
        },
        "q041": strip_internal(q041),
        "q045": strip_internal(q045),
        "executive_summary": executive_summary(q041, q045),
        "governance": {
            "diagnostic_evaluation": True,
            "new_performance_evaluation": False,
            "source_result_reconstruction": True,
            "holdout_inspection": True,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "variant_search": False,
            "family_ranking": False,
            "holdout_used_for_selection": False,
            "promotion_decision": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["diagnostic_fingerprint"] = fingerprint(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    markdown.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    markdown.write_text(markdown_report(result), encoding="utf-8")
    print("Q066_STATUS: COMPLETED_DIAGNOSTIC_ONLY")
    print("Q066_DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", required=True, type=Path)
    parser.add_argument("--q041-root", required=True, type=Path)
    parser.add_argument("--q045-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--markdown", required=True, type=Path)
    args = parser.parse_args()
    run(args.preregistration, args.q041_root, args.q045_root, args.output, args.markdown)
