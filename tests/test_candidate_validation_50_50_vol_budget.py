from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from types import SimpleNamespace

from automation.candidate_validation_50_50_vol_budget import (
    HOLDOUT_COUNT,
    RESEARCH_COUNT,
    TARGET_COUNT,
    _cs_weights,
    _gates,
    _summary,
    _delta,
)
from validation.research_gates import ResearchGateConfig


def _bar(close: float):
    return SimpleNamespace(close=close)


def _series(value_at_anchor: float):
    bars = [_bar(1.0) for _ in range(274)]
    bars[252] = _bar(value_at_anchor)
    return tuple(bars)


def test_cs_selection_is_top_two_and_deterministic():
    assets = {
        "A": _series(2.0),
        "B": _series(6.0),
        "C": _series(3.0),
        "D": _series(5.0),
        "E": _series(4.0),
    }
    weights = _cs_weights({**assets}, )
    # The first 273 sessions are inactive; test helper at a rebalance point
    # through the generated path.
    assert sum(weights[273].values()) == 1.0
    assert weights[273]["B"] == 0.5
    assert weights[273]["D"] == 0.5


def test_summary_uses_actual_daily_profit_factor():
    returns = [{"net_return": 0.10}, {"net_return": -0.05}, {"net_return": 0.02}]
    windows = [
        {"period_return": 0.10, "max_drawdown_percent": 0.0},
        {"period_return": -0.05, "max_drawdown_percent": 5.0},
        {"period_return": 0.02, "max_drawdown_percent": 1.0},
    ]
    result = _summary(returns, windows)
    assert result["profitable_windows"] == 2
    assert abs(result["overall_profit_factor"] - (0.12 / 0.05)) < 1e-12
    assert result["total_net_return"] > 0


def _scenario(
    holdout_return=0.08,
    research_return=0.20,
    dd=5.0,
    pf=1.2,
    ratio=0.4,
    stress15=0.03,
    stress2=0.01,
    total_return=0.09,
):
    mode = {
        "research": {
            "period_return": research_return,
            "max_drawdown_percent": dd,
            "profit_factor": pf,
        },
        "holdout": {
            "period_return": holdout_return,
            "max_drawdown_percent": dd,
            "profit_factor": pf,
        },
        "oos_to_is_return_ratio": ratio,
        "rolling_summary": {
            "total_net_return": 0.25,
            "overall_profit_factor": pf,
            "profitable_window_ratio": 0.6,
            "average_drawdown_percent": dd,
        },
    }
    return {
        "base": {
            "vol_budget_10pct": {
                "price_only": mode,
                "total_return_sensitivity": {
                    **mode,
                    "holdout": {**mode["holdout"], "period_return": total_return},
                },
            }
        },
        "stress_1_5x_cost": {
            "vol_budget_10pct": {
                "price_only": {
                    **mode,
                    "holdout": {**mode["holdout"], "period_return": stress15},
                },
                "total_return_sensitivity": mode,
            }
        },
        "stress_2x_cost": {
            "vol_budget_10pct": {
                "price_only": {
                    **mode,
                    "holdout": {**mode["holdout"], "period_return": stress2},
                },
                "total_return_sensitivity": mode,
            }
        },
    }


def test_gate_contract_passes_for_strong_candidate():
    assert _gates(_scenario(), ResearchGateConfig())["all_relevant_checks_passed"] is True


def test_gate_contract_blocks_negative_holdout():
    result = _gates(_scenario(holdout_return=-0.01), ResearchGateConfig())
    assert result["checks"]["holdout_return_positive"] is False
    assert result["all_relevant_checks_passed"] is False


def test_total_return_delta_is_explicit():
    price = {
        "holdout": {
            "period_return": 0.05,
            "max_drawdown_percent": 4.0,
            "profit_factor": 1.20,
        }
    }
    total = {
        "holdout": {
            "period_return": 0.06,
            "max_drawdown_percent": 3.5,
            "profit_factor": 1.25,
        }
    }
    delta = _delta(price, total)
    assert abs(delta["holdout_return_delta_percentage_points"] - 1.0) < 1e-12
    assert abs(delta["holdout_drawdown_delta_percentage_points"] + 0.5) < 1e-12
    assert abs(delta["holdout_profit_factor_delta"] - 0.05) < 1e-12


def test_raw_candle_return_split_is_exact():
    assert TARGET_COUNT - 2 == RESEARCH_COUNT + HOLDOUT_COUNT
    assert HOLDOUT_COUNT == 700


from automation.candidate_validation_50_50_vol_budget import _align_assets_by_latest_start

def test_latest_start_calendar_preserves_target_length():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    early = tuple(SimpleNamespace(timestamp=start + timedelta(days=i), open=100.0, close=100.0) for i in range(6))
    late = tuple(SimpleNamespace(timestamp=start + timedelta(days=i), open=100.0, close=100.0) for i in range(1, 6))
    aligned = _align_assets_by_latest_start({"early": early, "late": late})
    assert all(len(series) == 5 for series in aligned.values())
    assert [bar.timestamp for bar in aligned["early"]] == [bar.timestamp for bar in late]
