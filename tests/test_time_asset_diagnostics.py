import importlib.util
import json
import sys
import types


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "time_asset_diagnostics", "automation/time_asset_diagnostics.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _report(symbol, profile, universe, profits):
    candidate = {
        "risk_per_trade": 0.0025,
        "leverage": 1.0,
        "strategy": {
            "momentum": {"lookback": 8},
            "mean_reversion": {"window": 10, "threshold": 0.02},
        },
    }
    windows = [
        {
            "window_index": i,
            "selected_candidate": candidate,
            "test_net_profit_eur": profit,
            "test_profit_factor": 1.1 if profit > 0 else 0.8,
            "test_max_drawdown_percent": 2.0,
            "test_trade_count": 10,
        }
        for i, profit in enumerate(profits, 1)
    ]
    return {
        "datasets": [{
            "symbol": symbol,
            "interval": "1d",
            "walk_forward": {"selected_candidate": candidate},
            "rolling_walk_forward": {"windows": windows},
            "research_gates": {
                "gates": [
                    {
                        "name": "walk_forward",
                        "passed": False,
                        "scope": "selected_candidate_oos",
                    }
                ]
            },
            "statistical_diagnostics": {
                "multiple_testing": {"selection_profile": profile}
            },
        }],
        "run_manifest": {
            "run_fingerprint": f"run-{universe}-{profile}",
            "data_manifest": {"universe": universe},
        },
        "result_fingerprint": f"result-{universe}-{profile}",
        "safety": {"paper_only": True, "live_trading_enabled": False},
    }


def _install_verify_stub():
    workflow = types.ModuleType("automation.research_workflow")
    workflow.verify_result_fingerprint = lambda report: None
    automation = types.ModuleType("automation")
    automation.__path__ = []
    sys.modules["automation"] = automation
    sys.modules["automation.research_workflow"] = workflow


def test_build_time_asset_diagnostics():
    _install_verify_stub()
    module = _load_module()
    out = module.build_time_asset_diagnostics([
        _report("AAA", "score_max", "u1", [1, -1, 2, -2, 1]),
        _report("BBB", "score_max", "u1", [-1, -2, 1, 1, -1]),
    ])
    assert out["dataset_profile_count"] == 2
    assert out["rolling_window_count"] == 10
    phase = {x["window_index"]: x for x in out["phase_summary"]}
    assert phase[1]["positive_profit_count"] == 1
    assert phase[4]["positive_profit_count"] == 1
    assert out["candidate_persistence"][0]["same_as_fixed_wfo_rate"] == 1.0
    assert len(out["diagnostic_fingerprint"]) == 64


def test_fingerprint_changes_with_content():
    _install_verify_stub()
    module = _load_module()
    one = module.build_time_asset_diagnostics([
        _report("AAA", "score_max", "u1", [1, 1, 1, 1, 1])
    ])
    two = module.build_time_asset_diagnostics([
        _report("AAA", "score_max", "u1", [1, 1, 1, 1, 2])
    ])
    assert one["diagnostic_fingerprint"] != two["diagnostic_fingerprint"]
