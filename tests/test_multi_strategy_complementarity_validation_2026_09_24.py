import pytest

from automation.multi_strategy_complementarity_validation_2026_09_24 import (
    _blend_rows,
    _complementarity_diagnostics,
)


def row(timestamp, value, turnover=0.1):
    return {
        "timestamp": timestamp,
        "gross_open": value,
        "gross_close": value,
        "gross_adjusted_close": value,
        "turnover": turnover,
    }


def metric(period_return, drawdown, pf):
    return {
        "period_return": period_return,
        "max_drawdown_percent": drawdown,
        "profit_factor": pf,
    }


def test_blend_rows_is_fixed_fifty_fifty():
    trend = {1: row(1, 0.02), 2: row(2, -0.01)}
    cs = {1: row(1, 0.04), 2: row(2, 0.02)}

    blended = _blend_rows(trend, cs)

    assert blended[0]["gross_open"] == pytest.approx(0.03)
    assert blended[1]["gross_open"] == pytest.approx(0.005)


def test_complementarity_diagnostics_accepts_stronger_blend_on_risk_metrics():
    families = {
        "trend": {
            "research": metric(0.10, 20.0, 1.10),
            "holdout": metric(0.04, 10.0, 1.10),
            "rolling_summary": {"overall_profit_factor": 1.05},
        },
        "cross_sectional": {
            "research": metric(0.15, 18.0, 1.12),
            "holdout": metric(0.03, 9.0, 1.08),
            "rolling_summary": {"overall_profit_factor": 1.08},
        },
        "blend_50_50": {
            "research": metric(0.12, 17.0, 1.11),
            "holdout": metric(0.035, 8.0, 1.12),
            "rolling_summary": {"overall_profit_factor": 1.09},
        },
    }

    diagnostics = _complementarity_diagnostics(families)

    assert diagnostics["research_drawdown_not_worse_than_both"] is True
    assert diagnostics["holdout_drawdown_not_worse_than_both"] is True
    assert diagnostics["blend_positive_research"] is True
    assert diagnostics["blend_positive_holdout"] is True


def test_complementarity_diagnostics_does_not_hide_return_failure():
    families = {
        "trend": {
            "research": metric(0.20, 10.0, 1.20),
            "holdout": metric(0.05, 8.0, 1.15),
            "rolling_summary": {"overall_profit_factor": 1.12},
        },
        "cross_sectional": {
            "research": metric(0.10, 15.0, 1.10),
            "holdout": metric(-0.01, 9.0, 0.95),
            "rolling_summary": {"overall_profit_factor": 1.02},
        },
        "blend_50_50": {
            "research": metric(-0.01, 8.0, 1.05),
            "holdout": metric(-0.02, 7.0, 1.00),
            "rolling_summary": {"overall_profit_factor": 1.01},
        },
    }

    diagnostics = _complementarity_diagnostics(families)

    assert diagnostics["research_drawdown_not_worse_than_both"] is True
    assert diagnostics["blend_positive_research"] is False
    assert diagnostics["blend_positive_holdout"] is False
