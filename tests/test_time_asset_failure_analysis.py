from automation.time_asset_failure_analysis import analyze, _phase_label


def _candidate(momentum=8, window=20, threshold=0.02, risk=0.01, leverage=1.0):
    return {
        "risk_per_trade": risk,
        "leverage": leverage,
        "strategy": {
            "momentum": {"lookback": momentum},
            "mean_reversion": {"window": window, "threshold": threshold},
        },
    }


def _window(index, candidate, profit, pf, trades=10):
    return {
        "window_index": index,
        "test_start": f"2020-01-{index + 1:02d}T00:00:00+00:00",
        "test_end": f"2020-01-{index + 2:02d}T00:00:00+00:00",
        "candidate": candidate,
        "net_profit_eur": profit,
        "profit_factor": pf,
        "max_drawdown_percent": 2.0,
        "trade_count": trades,
    }


def _gate(windows, failed):
    return {
        "geometry": "small",
        "window_count": len(windows),
        "gate": {
            "passed": not failed,
            "failed_criteria": failed,
            "details": {
                "window_count": len(windows),
                "total_trade_count": sum(w["trade_count"] for w in windows),
                "overall_profit_factor": 1.0,
                "profitable_window_ratio": 0.5,
                "total_net_profit_eur": sum(w["net_profit_eur"] for w in windows),
            },
        },
        "windows": windows,
    }


def test_phase_split_is_deterministic():
    assert [_phase_label(i, 15) for i in range(1, 16)] == (
        ["early"] * 5 + ["middle"] * 5 + ["recent"] * 5
    )
    assert [_phase_label(i, 5) for i in range(1, 6)] == (
        ["early", "early", "middle", "recent", "recent"]
    )


def test_analysis_extracts_failures_and_migration_state():
    c1 = _candidate()
    c2 = _candidate(momentum=10)
    small_windows = [
        _window(1, c1, 1.0, 1.2),
        _window(2, c2, -2.0, 0.8),
        _window(3, c2, 2.0, 1.2),
    ]
    large_windows = [
        _window(1, c1, -1.0, 0.9),
        _window(2, c1, 1.0, 1.2),
    ]
    rolling = {
        "diagnostic_type": "rolling_geometry_time_phase_control",
        "diagnostic_fingerprint": "source",
        "code_version": "code",
        "datasets": [{
            "symbol": "TEST",
            "profiles": [{
                "selection_profile": "profile",
                "small": _gate(small_windows, ["profit_factor"]),
                "large": _gate(large_windows, ["nonpositive_total_profit"]),
            }],
        }],
    }
    migration = {
        "analysis_fingerprint": "migration-analysis",
        "source_diagnostic_fingerprint": "source",
        "transition_count_total": 3,
        "transitions": [
            {
                "symbol": "TEST",
                "selection_profile": "profile",
                "geometry": "small",
                "destination_window": 2,
                "changed_parameters": ["momentum.lookback"],
            },
            {
                "symbol": "TEST",
                "selection_profile": "profile",
                "geometry": "small",
                "destination_window": 3,
                "changed_parameters": [],
            },
            {
                "symbol": "TEST",
                "selection_profile": "profile",
                "geometry": "large",
                "destination_window": 2,
                "changed_parameters": [],
            },
        ],
    }

    result = analyze(rolling, migration)

    assert result["window_count"] == 5
    assert result["evaluation_count"] == 2
    assert result["formal_failure_summary"]["profit_factor"]["failed_count"] == 1
    assert result["formal_failure_summary"]["nonpositive_total_profit"]["failed_count"] == 1
    assert result["windows"][0]["migration_status"] == "first_window"
    assert result["windows"][1]["migration_status"] == "migration"
    assert result["windows"][2]["migration_status"] == "stable"


def test_analysis_rejects_provenance_mismatch():
    rolling = {
        "diagnostic_type": "rolling_geometry_time_phase_control",
        "diagnostic_fingerprint": "rolling",
        "datasets": [],
    }
    migration = {
        "source_diagnostic_fingerprint": "other",
        "transition_count_total": 0,
        "transitions": [],
    }
    try:
        analyze(rolling, migration)
    except ValueError as exc:
        assert "fingerprint" in str(exc)
    else:
        raise AssertionError("expected provenance mismatch to fail closed")
