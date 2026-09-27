
"""T060/Q041 fixed multi-arm alpha performance evaluation."""
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

from automation.candidate_validation_50_50_vol_budget import _cs_weights
from automation.cross_asset_trend_replication import _build_weight_path
from config import settings
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility

TRIAL_ID = "T-2026-09-27-060"
UNIVERSE = "validation_2026_09_27_q039_price_only_alpha_pit"
SYMBOLS = ("IVE", "IWL", "DLN", "DHS", "DON", "DES", "USRT", "ITB")
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
EXPECTED_RETURNS = 3498
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_SCENARIOS = (("base", 1.0), ("stress_1_5x_cost", 1.5), ("stress_2x_cost", 2.0))
INITIAL_CAPITAL_EUR = 2000.0
YAHOO_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fp(value):
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _pf(value):
    return float("inf") if value == "inf" else float(value)


def _find_manifest(root):
    paths = sorted(Path(root).rglob("coverage_preflight_*.json"))
    if not paths:
        raise FileNotFoundError("Q041 coverage manifest not found")
    return paths[-1]


def _load_assets(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("status") not in {"coverage_passed", "COVERAGE_PASSED"}:
        raise ValueError("Q041 coverage manifest is not passed")
    if manifest.get("universe") != UNIVERSE:
        raise ValueError("Q041 universe mismatch")
    if tuple(manifest.get("symbols", ())) != SYMBOLS:
        raise ValueError("Q041 symbols mismatch")
    if int(manifest.get("target_common_calendar", -1)) != TARGET_COUNT:
        raise ValueError("Q041 target common calendar mismatch")
    if int(manifest.get("common_calendar_count", 0)) < TARGET_COUNT:
        raise ValueError("Q041 common calendar below target")
    expected = {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False}
    if manifest.get("safety") != expected:
        raise RuntimeError("Q041 coverage safety mismatch")
    assets = load_frozen_snapshot(manifest_path)
    if tuple(assets) != SYMBOLS:
        raise ValueError("Q041 frozen symbols mismatch")
    if any(len(v) != TARGET_COUNT for v in assets.values()):
        raise ValueError("Q041 frozen geometry mismatch")
    return assets, manifest


def _returns(closes):
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]


def _a1_signal(closes, index):
    if index < 252:
        return 0
    votes = 0
    for lookback in (21, 63, 252):
        change = closes[index] / closes[index - lookback] - 1.0
        votes += 1 if change > 0 else -1 if change < 0 else 0
    return 1 if votes > 0 else -1 if votes < 0 else 0


def _a1_weights(assets):
    closes = {s: [b.close for b in assets[s]] for s in SYMBOLS}
    output = []
    for index in range(TARGET_COUNT):
        active = [s for s in SYMBOLS if _a1_signal(closes[s], index) > 0]
        weight = 1.0 / len(active) if active else 0.0
        output.append({s: weight if s in active else 0.0 for s in SYMBOLS})
    return tuple(output)


def _a2_weights(assets):
    closes = {s: [b.close for b in assets[s]] for s in SYMBOLS}
    current = {s: 0.0 for s in SYMBOLS}
    output = []
    for index in range(TARGET_COUNT):
        anchor = index - 21
        if anchor >= 252:
            scores = {s: closes[s][anchor] / closes[s][anchor - 252] - 1.0 for s in SYMBOLS}
            winners = sorted(scores, key=lambda s: (-scores[s], s))[:2]
            current = {s: 0.5 if s in winners else 0.0 for s in SYMBOLS}
        output.append(dict(current))
    return tuple(output)


def _beta(asset_returns, market_returns):
    if len(asset_returns) != len(market_returns) or not asset_returns:
        return 0.0
    am = sum(asset_returns) / len(asset_returns)
    mm = sum(market_returns) / len(market_returns)
    var = sum((v - mm) ** 2 for v in market_returns)
    if var <= 0.0:
        return 0.0
    cov = sum((x - am) * (y - mm) for x, y in zip(asset_returns, market_returns))
    return cov / var


def _beta_inputs(assets, index):
    anchor = index - 21
    if anchor < 273:
        return {}
    returns = {s: _returns([b.close for b in assets[s]]) for s in SYMBOLS}
    start = anchor - 273
    end = anchor - 21
    market = [sum(returns[s][i] for s in SYMBOLS) / len(SYMBOLS) for i in range(start, end)]
    return {s: _beta(returns[s][start:end], market) for s in SYMBOLS}


def _a3_weights(assets):
    closes = {s: [b.close for b in assets[s]] for s in SYMBOLS}
    returns = {s: _returns(closes[s]) for s in SYMBOLS}
    current = {s: 0.0 for s in SYMBOLS}
    output = []
    for index in range(TARGET_COUNT):
        anchor = index - 21
        if anchor >= 273:
            start = anchor - 273
            end = anchor - 21
            market = [sum(returns[s][i] for s in SYMBOLS) / len(SYMBOLS) for i in range(start, end)]
            betas = {s: _beta(returns[s][start:end], market) for s in SYMBOLS}
            scores = {}
            for s in SYMBOLS:
                scores[s] = sum(x - betas[s] * m for x, m in zip(returns[s][start:end], market))
            winners = sorted(scores, key=lambda s: (-scores[s], s))[:2]
            current = {s: 0.5 if s in winners else 0.0 for s in SYMBOLS}
        output.append(dict(current))
    return tuple(output)


def _a5_weights(assets):
    current = {s: 0.0 for s in SYMBOLS}
    output = []
    for index in range(TARGET_COUNT):
        betas = _beta_inputs(assets, index)
        if betas:
            winners = sorted(betas, key=lambda s: (betas[s], s))[:2]
            current = {s: 0.5 if s in winners else 0.0 for s in SYMBOLS}
        output.append(dict(current))
    return tuple(output)


def _control_weights(assets):
    trend = _build_weight_path(assets, "sma_50_200_inverse_vol")
    cs = _cs_weights(assets)
    return tuple({
        s: 0.5 * float(trend[i].get(s, 0.0)) + 0.5 * float(cs[i].get(s, 0.0))
        for s in SYMBOLS
    } for i in range(TARGET_COUNT))


def _return_rows(assets, weights):
    previous = {s: 0.0 for s in SYMBOLS}
    rows = []
    for index in range(TARGET_COUNT - 2):
        target = weights[index]
        gross = 0.0
        turnover = 0.0
        for s in SYMBOLS:
            bars = assets[s]
            r = bars[index + 2].open / bars[index + 1].open - 1.0
            w = float(target.get(s, 0.0))
            gross += w * r
            turnover += abs(w - previous[s])
            previous[s] = w
        rows.append({"timestamp": assets[SYMBOLS[0]][index + 2].timestamp, "gross": gross, "turnover": turnover})
    if len(rows) != EXPECTED_RETURNS:
        raise ValueError(f"Expected {EXPECTED_RETURNS} returns, got {len(rows)}")
    return tuple(rows)


def _yahoo_adjclose(symbol, start, end):
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
            req = urllib.request.Request(url, headers={"User-Agent": "trading-agent-research/1.0"})
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode())
            result = payload["chart"]["result"][0]
            return {
                datetime.fromtimestamp(int(ts), tz=timezone.utc): float(v)
                for ts, v in zip(result["timestamp"], result["indicators"]["adjclose"][0]["adjclose"])
                if v is not None
            }
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError, ValueError) as exc:
            if attempt == 3:
                raise RuntimeError(f"Adjusted close unavailable for {symbol}: {exc}") from exc
            time.sleep(2 ** attempt)
    raise RuntimeError("Unexpected adjusted-close failure")


def _stats(values, start, end):
    seg = values[start:end]
    if not seg:
        return {"period_return": 0.0, "max_drawdown_percent": 0.0, "profit_factor": 0.0, "positive_day_ratio": 0.0, "day_count": 0}
    equity = peak = 1.0
    gp = gl = 0.0
    positives = 0
    max_dd = 0.0
    for value in seg:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0.0 else 1.0)
        if value > 0:
            gp += value
            positives += 1
        elif value < 0:
            gl -= value
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gp / gl if gl > 0 else ("inf" if gp > 0 else 0.0),
        "positive_day_ratio": positives / len(seg),
        "day_count": len(seg),
    }


def _summary(values):
    research = _stats(values, 0, RESEARCH_COUNT)
    holdout = _stats(values, RESEARCH_COUNT, EXPECTED_RETURNS)
    width = RESEARCH_COUNT // 5
    windows = []
    for k in range(5):
        start = k * width
        end = RESEARCH_COUNT if k == 4 else (k + 1) * width
        windows.append({"window_index": k + 1, **_stats(values, start, end)})
    positives = sum(w["period_return"] > 0.0 for w in windows)
    gain = sum(max(w["period_return"], 0.0) for w in windows)
    loss = -sum(min(w["period_return"], 0.0) for w in windows)
    return {
        "research": research,
        "holdout": holdout,
        "rolling_windows": windows,
        "rolling_profit_factor": gain / loss if loss > 0 else ("inf" if gain > 0 else 0.0),
        "rolling_profitable_window_ratio": positives / len(windows),
        "rolling_average_drawdown_percent": sum(w["max_drawdown_percent"] for w in windows) / len(windows),
        "oos_to_is_return_ratio": holdout["period_return"] / research["period_return"] if research["period_return"] > 0.0 else 0.0,
    }


def _evaluate_arm(assets, weights, adjusted):
    rows = _return_rows(assets, weights)
    turnover = [r["turnover"] for r in rows]
    gross = [r["gross"] for r in rows]
    scenarios = {}
    for name, multiplier in COST_SCENARIOS:
        rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier
        scenarios[name] = _summary([g - rate * t for g, t in zip(gross, turnover)])
    total = []
    for j, row in enumerate(rows):
        current_ts = row["timestamp"]
        previous_ts = assets[SYMBOLS[0]][j + 1].timestamp
        value = 0.0
        for s in SYMBOLS:
            cur = adjusted[s].get(current_ts)
            prev = adjusted[s].get(previous_ts)
            if cur is None or prev is None:
                raise ValueError(f"{s}: missing adjusted-close sensitivity point")
            bars = assets[s]
            open_return = bars[j + 2].open / bars[j + 1].open - 1.0
            close_return = bars[j + 2].close / bars[j + 1].close - 1.0
            adjusted_return = cur / prev - 1.0
            value += float(weights[j].get(s, 0.0)) * (open_return + adjusted_return - close_return)
        total.append(value - (FEE_RATE + SLIPPAGE_RATE) * turnover[j])
    base = scenarios["base"]
    gates = {
        "research_return_positive": base["research"]["period_return"] > 0.0,
        "research_drawdown_lte_10pct": base["research"]["max_drawdown_percent"] <= 10.0,
        "research_profit_factor_gte_1_10": _pf(base["research"]["profit_factor"]) >= 1.10,
        "rolling_profit_factor_gte_1_10": _pf(base["rolling_profit_factor"]) >= 1.10,
        "rolling_profitable_window_ratio_gte_0_50": base["rolling_profitable_window_ratio"] >= 0.50,
        "rolling_average_drawdown_lte_10pct": base["rolling_average_drawdown_percent"] <= 10.0,
        "oos_to_is_return_ratio_gte_0_25": base["oos_to_is_return_ratio"] >= 0.25,
        "holdout_return_positive": base["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor_gte_1_10": _pf(base["holdout"]["profit_factor"]) >= 1.10,
        "holdout_drawdown_lte_10pct": base["holdout"]["max_drawdown_percent"] <= 10.0,
        "stress_1_5x_holdout_nonnegative": scenarios["stress_1_5x_cost"]["holdout"]["period_return"] >= 0.0,
        "stress_2x_holdout_nonnegative": scenarios["stress_2x_cost"]["holdout"]["period_return"] >= 0.0,
        "total_return_sensitivity_holdout_nonnegative": _summary(total)["holdout"]["period_return"] >= 0.0,
    }
    return {
        "base": base,
        "stress_1_5x_cost": scenarios["stress_1_5x_cost"],
        "stress_2x_cost": scenarios["stress_2x_cost"] if "stress_2x_cost" in scenarios else scenarios["stress_2x_cost"],
        "total_return_sensitivity": _summary(total),
        "gates": gates,
        "gates_passed": sum(gates.values()),
        "gates_total": len(gates),
        "all_gates_passed": all(gates.values()),
        "turnover": {"mean": sum(turnover) / len(turnover), "sum": sum(turnover)},
        "gross_exposure": {
            "max": max(sum(abs(v) for v in weights[i].values()) for i in range(TARGET_COUNT)),
            "mean": sum(sum(abs(v) for v in weights[i].values()) for i in range(TARGET_COUNT)) / TARGET_COUNT,
        },
    }


def run(preregistration, coverage_root, output):
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("Safety contract violated")
    spec = json.loads(Path(preregistration).read_text(encoding="utf-8"))
    if spec.get("trial_id") != TRIAL_ID or spec.get("status") != "PREREGISTERED_PERFORMANCE":
        raise ValueError("Q041 preregistration mismatch")
    gov = spec.get("governance", {})
    forbidden = ("parameter_search", "asset_search", "threshold_search", "horizon_search", "variant_search", "family_ranking", "selection", "holdout_used_for_selection", "promotion_decision", "automatic_promotion")
    if any(gov.get(k) is not False for k in forbidden):
        raise RuntimeError("Q041 selection/promotion governance mismatch")
    validate_research_cost_compatibility(fee_rate=FEE_RATE, slippage_rate=SLIPPAGE_RATE)
    manifest_path = _find_manifest(coverage_root)
    assets, manifest = _load_assets(manifest_path)
    adjusted = {
        s: _yahoo_adjclose(s, assets[s][0].timestamp, assets[s][-1].timestamp)
        for s in SYMBOLS
    }
    weights = {
        "CONTROL": _control_weights(assets),
        "A1_TSM_CONSENSUS": _a1_weights(assets),
        "A2_CS_MOMENTUM_TOP2": _a2_weights(assets),
        "A3_RESIDUAL_MOMENTUM_TOP2": _a3_weights(assets),
        "A5_LOW_BETA_TOP2": _a5_weights(assets),
    }
    reports = {arm: _evaluate_arm(assets, w, adjusted) for arm, w in weights.items()}
    result = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "code_version": os.getenv("GITHUB_SHA", "UNVERIFIED_LOCAL_CODE"),
        "universe": UNIVERSE,
        "symbols": list(SYMBOLS),
        "requested_candles": 4000,
        "target_common_candles": TARGET_COUNT,
        "research_periods": RESEARCH_COUNT,
        "holdout_periods": HOLDOUT_COUNT,
        "initial_capital_eur": INITIAL_CAPITAL_EUR,
        "coverage_manifest": str(manifest_path),
        "coverage_snapshot_fingerprint": manifest.get("snapshot_fingerprint"),
        "pit_prerequisite": "T-2026-09-27-059",
        "arms": reports,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "parameter_search": False,
        "asset_search": False,
        "threshold_search": False,
        "horizon_search": False,
        "variant_search": False,
        "family_ranking": False,
        "performance_evaluation": True,
        "oos_evaluation": True,
        "holdout_evaluation": True,
        "governance": {
            "performance_trial_authorized": True,
            "promotion_decision": False,
            "automatic_promotion": False,
            "family_ranking": False,
            "selection": False,
            "holdout_used_for_selection": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["report_fingerprint"] = _fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print("Q041_STATUS: COMPLETED")
    for arm, report in reports.items():
        print(f"{arm}_GATES: {report['gates_passed']}/{report['gates_total']}")
    print("Q041_REPORT_FINGERPRINT:", result["report_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", required=True)
    parser.add_argument("--coverage-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(Path(args.preregistration), Path(args.coverage_root), Path(args.output))
