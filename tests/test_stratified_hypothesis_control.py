from automation.stratified_hypothesis_control import analyze


def _row(signature, window, profit, pf, phase, vol, structure, symbol):
    return {
        "symbol": symbol,
        "selection_profile": "trade_rich",
        "geometry": "small",
        "window_index": ({"early": 1, "middle": 2, "recent": 3}[phase]
                         + (10 if window == 5 else 0)),
        "candidate_signature": signature,
        "candidate": {},
        "parameter_values": {
            "risk_per_trade": 0.0025,
            "leverage": 1.0,
            "momentum.lookback": 3,
            "mean_reversion.window": window,
            "mean_reversion.threshold": 0.01,
        },
        "phase": phase,
        "pre_test_vol_regime": vol,
        "pre_test_structure_regime": structure,
        "net_profit_eur": profit,
        "profit_factor": pf,
    }


def _source(rows, signatures):
    return {
        "diagnostic_type": "rolling_regime_parameter_failure_matrix",
        "analysis_fingerprint": (
            "9aa88bf691bfcfc94b5e4de5cbabae950a606af1d7a80645e61b3ab8be960f2f"
        ),
        "source_target_count": 5000,
        "source_research_candle_count": 4500,
        "source_universe": "benchmark",
        "recurrent_candidates": [
            {"candidate_signature": signature} for signature in signatures
        ],
        "interpretation_scope": {
            "no_selection_rule": True,
            "no_parameter_change": True,
            "no_gate_change": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
        "rows": rows,
    }


def test_identifies_one_cross_asset_single_parameter_hypothesis():
    rows = []
    for symbol, offset in (("IWM", 0), ("QQQ", 10)):
        phase_regimes = [
            ("early", "low", "choppy"),
            ("middle", "middle", "mixed"),
            ("recent", "high", "trending"),
        ]
        for phase, vol, structure in phase_regimes:
            rows.append(
                _row("a", 10, -1.0 - offset, 0.8, phase, vol, structure, symbol)
            )
            rows.append(
                _row("b", 5, 2.0 + offset, 1.3, phase, vol, structure, symbol)
            )

    result = analyze(_source(rows, ["a", "b"]))

    assert result["status"] == "one_experiment_ready_hypothesis"
    assert result["eligible_hypothesis_count"] == 1
    hypothesis = result["experiment_ready_hypothesis"]
    assert hypothesis["selection_profile"] == "trade_rich"
    assert hypothesis["geometry"] == "small"
    assert hypothesis["parameter"] == "mean_reversion.window"
    assert hypothesis["supported_value"] == 5
    assert hypothesis["assets"] == ["IWM", "QQQ"]
    assert hypothesis["fixed_parameters"] == {
        "risk_per_trade": 0.0025,
        "leverage": 1.0,
        "momentum.lookback": 3,
        "mean_reversion.threshold": 0.01,
    }


def test_rejects_mixed_primary_direction():
    rows = []
    for symbol, a_profit, b_profit, a_pf, b_pf in (
        ("IWM", 2.0, -1.0, 1.3, 0.8),
        ("QQQ", -2.0, 1.0, 0.8, 1.3),
    ):
        phase_regimes = [
            ("early", "low", "choppy"),
            ("middle", "middle", "mixed"),
            ("recent", "high", "trending"),
        ]
        for phase, vol, structure in phase_regimes:
            rows.append(
                _row("a", 10, a_profit, a_pf, phase, vol, structure, symbol)
            )
            rows.append(
                _row("b", 5, b_profit, b_pf, phase, vol, structure, symbol)
            )

    result = analyze(_source(rows, ["a", "b"]))
    assert result["eligible_hypothesis_count"] == 0
    assert result["status"] == "no_experiment_ready_hypothesis"
    assert result["experiment_ready_hypothesis"] is None


def test_source_safety_is_fail_closed():
    row = _row("a", 10, 1.0, 1.2, "early", "low", "choppy", "IWM")
    source = _source([row], ["a"])
    source["safety"]["live_trading_enabled"] = True

    try:
        analyze(source)
    except ValueError as exc:
        assert "Paper-Only" in str(exc)
    else:
        raise AssertionError("unsafe source must be rejected")
