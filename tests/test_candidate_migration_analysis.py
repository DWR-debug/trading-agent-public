from automation.candidate_migration_analysis import analyze


def _candidate(risk=0.01, leverage=1.0, momentum=8, window=20, threshold=0.02):
    return {
        "risk_per_trade": risk,
        "leverage": leverage,
        "strategy": {
            "momentum": {"lookback": momentum},
            "mean_reversion": {"window": window, "threshold": threshold},
        },
    }


def _window(index, candidate, profit, pf, dd=2.0, trades=10):
    return {
        "window_index": index,
        "candidate": candidate,
        "net_profit_eur": profit,
        "profit_factor": pf,
        "max_drawdown_percent": dd,
        "trade_count": trades,
    }


def test_analyze_separates_migration_and_stable_transitions():
    report = {
        "diagnostic_type": "rolling_geometry_time_phase_control",
        "diagnostic_fingerprint": "source",
        "code_version": "code",
        "target_count": 5000,
        "research_candle_count": 4500,
        "universe": "benchmark",
        "datasets": [
            {
                "symbol": "TEST",
                "profiles": [
                    {
                        "selection_profile": "profile",
                        "small": {
                            "windows": [
                                _window(1, _candidate(), 1.0, 1.2),
                                _window(2, _candidate(momentum=10), -2.0, 0.8),
                                _window(3, _candidate(momentum=10), 3.0, 1.3),
                            ]
                        },
                        "large": {
                            "windows": [
                                _window(1, _candidate(), 1.0, 1.2),
                                _window(2, _candidate(), -1.0, 0.9),
                            ]
                        },
                    }
                ],
            }
        ],
    }

    result = analyze(report)

    assert result["transition_count_total"] == 3
    assert result["transition_count_migration"] == 1
    assert result["transition_count_stable"] == 2
    assert result["parameter_summary"]["momentum.lookback"]["change_count"] == 1


def test_destination_flags_are_window_level():
    report = {
        "diagnostic_type": "rolling_geometry_time_phase_control",
        "diagnostic_fingerprint": "source",
        "datasets": [{
            "symbol": "TEST",
            "profiles": [{
                "selection_profile": "profile",
                "small": {
                    "windows": [
                        _window(1, _candidate(), 1.0, 1.2),
                        _window(2, _candidate(), -1.0, 0.9, dd=11.0),
                    ]
                },
                "large": {
                    "windows": [
                        _window(1, _candidate(), 1.0, 1.2),
                        _window(2, _candidate(), -1.0, 0.9, dd=11.0),
                    ]
                },
            }]
        }],
    }
    result = analyze(report)
    transition = result["transitions"][0]
    assert transition["flags"]["nonpositive_profit"] is True
    assert transition["flags"]["profit_factor_failure"] is True
    assert transition["flags"]["drawdown_failure"] is True
