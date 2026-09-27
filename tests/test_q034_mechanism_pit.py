from __future__ import annotations

from portfolio.q030_risk_mechanisms import (
    Bar,
    common_mode_exposure_scale,
    drawdown_throttle_scale,
    position_lifecycle_exit_trigger,
    sleeve_volatility_scale,
)


def test_risk_a_bounds_and_history() -> None:
    assert sleeve_volatility_scale([0.0] * 10) == 1.0
    scale=sleeve_volatility_scale([0.05 if i % 2 == 0 else -0.05 for i in range(63)])
    assert 0.25 <= scale <= 1.0


def test_risk_b_state_thresholds() -> None:
    assert drawdown_throttle_scale([-0.06]) == 0.50
    assert drawdown_throttle_scale([-0.10]) == 0.25


def test_risk_c_common_mode_trigger() -> None:
    a=[0.01,-0.02,0.03,-0.01,0.02]*13
    b=list(a)
    weights={"A":0.5,"B":0.5}
    assert common_mode_exposure_scale({"A":a,"B":b},weights) == 0.50


def test_risk_d_future_data_isolation() -> None:
    bars=[]
    for i in range(25):
        close=100.0+i
        bars.append(Bar(str(i),close-0.5,close+1.0,close-1.0,close))
    highest=max(x.close for x in bars[4:20])
    baseline=position_lifecycle_exit_trigger(bars,20,highest_close_since_entry=highest)
    mutated=[Bar(x.timestamp,x.open,x.high,x.low,x.close) for x in bars]
    for i in range(21,25):
        mutated[i]=Bar(mutated[i].timestamp,9000,9001,1,9000)
    assert position_lifecycle_exit_trigger(mutated,20,highest_close_since_entry=highest)==baseline


def test_q034_future_mutation_uses_replacement_for_frozen_bars() -> None:
    from dataclasses import FrozenInstanceError
    from portfolio.q030_risk_mechanisms import Bar

    bar = Bar("0", 100.0, 101.0, 99.0, 100.0)
    try:
        bar.close = 101.0
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Q034 regression fixture requires immutable Bar instances")

    replacement = Bar(bar.timestamp, bar.open * 0.2, bar.high * 1.3, bar.low * 0.4, bar.close * 1.7)
    assert replacement.close == 170.0
