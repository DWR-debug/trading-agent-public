from automation.microtrading_15m_sidecar_2026_09_23 import _stats

def test_stats_empty_is_safe():
    assert _stats([], 0, 0) == {"bar_count": 0}

def test_stats_contains_core_risk_fields():
    rows = [
        {
            "net_return": 0.01,
            "turnover": 0.0,
            "gross_exposure": 1.0,
            "trade_opened": 1,
        },
        {
            "net_return": -0.005,
            "turnover": 0.0,
            "gross_exposure": 1.0,
            "trade_opened": 0,
        },
    ]
    result = _stats(rows, 0, 2)
    assert result["bar_count"] == 2
    assert result["trade_open_count"] == 1
    assert result["max_drawdown_percent"] > 0.0
