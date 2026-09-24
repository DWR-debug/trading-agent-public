from automation.trial_031_risk_adjusted_momentum_2026_09_24 import _gates, _risk_adjusted_cs_weights, CS_LOOKBACK, CS_SKIP
from validation.research_gates import ResearchGateConfig

def _bars(n=300):
    from types import SimpleNamespace
    return tuple(SimpleNamespace(close=100.0,timestamp=i) for i in range(n))

def test_risk_adjusted_weights_warmup_is_empty():
    bars=_bars(CS_LOOKBACK+CS_SKIP)
    weights,_=_risk_adjusted_cs_weights({"A":bars,"B":bars,"C":bars})
    assert all(sum(v.values())==0.0 for v in weights[:CS_LOOKBACK+CS_SKIP])

def _mode(r=.2,dd=5.0,pf=1.2,rpf=1.2,ratio=.6,rdd=5.0,oos=.5,h=.1,hdd=5.0,hpf=1.2):
    return {"research":{"period_return":r,"max_drawdown_percent":dd,"profit_factor":pf},
            "rolling_summary":{"overall_profit_factor":rpf,"profitable_window_ratio":ratio,"average_drawdown_percent":rdd},
            "oos_to_is_return_ratio":oos,
            "holdout":{"period_return":h,"max_drawdown_percent":hdd,"profit_factor":hpf}}

def _scenario():
    m=_mode()
    wrap={"price_only":m,"total_return_sensitivity":m}
    return {"base":{"fixed_candidate":{"price_only":m},"risk_adjusted_candidate":wrap},
            "stress_1_5x_cost":{"fixed_candidate":{"price_only":m},"risk_adjusted_candidate":wrap},
            "stress_2x_cost":{"fixed_candidate":{"price_only":m},"risk_adjusted_candidate":wrap}}

def test_gate_contract_passes_for_equal_strong_candidate():
    r=_gates(_scenario(),ResearchGateConfig())
    assert r["all_absolute_passed"]
    assert r["all_non_worsening_passed"]
    assert r["all_checks_passed"]

def test_gate_contract_blocks_research_return_deterioration():
    s=_scenario()
    s["base"]["risk_adjusted_candidate"]["price_only"]["research"]["period_return"]=0.1
    r=_gates(s,ResearchGateConfig())
    assert not r["non_worsening_vs_fixed_candidate"]["research_return_not_below_fixed"]
    assert not r["all_checks_passed"]

def test_fixed_definition():
    assert (CS_LOOKBACK,CS_SKIP)==(252,21)
