from automation.trial_034_relative_value_etf_pairs_2026_09_24 import (
    ADF_PVALUE,
    ENTRY_Z,
    EXIT_ABS_Z,
    FORMATION_WINDOW,
    SYMBOLS,
    _transition_state,
    _weights_from_states,
    PairState,
)

def _state(states, eligible=None, z=None, left="A", right="B"):
    states=tuple(states)
    eligible=tuple(True for _ in states) if eligible is None else tuple(eligible)
    z=tuple(None for _ in states) if z is None else tuple(z)
    return PairState(left=left,right=right,economic_group="test",
                     state_by_index=states,eligible_by_index=eligible,z_by_index=z,
                     adf_pvalue_by_rebalance=(),entry_count=0,exit_count=0)

def test_fixed_parameters_are_frozen():
    assert FORMATION_WINDOW==200
    assert (ENTRY_Z,EXIT_ABS_Z)==(1.65,0.75)
    assert ADF_PVALUE==0.05
    assert len(SYMBOLS)==10

def test_short_entry_above_threshold():
    assert _transition_state(0,2.1,True)==-1

def test_long_entry_below_threshold():
    assert _transition_state(0,-2.1,True)==1

def test_exit_inside_abs_075():
    assert _transition_state(-1,0.70,True)==0
    assert _transition_state(1,-0.70,True)==0

def test_ineligible_pair_forces_flat():
    assert _transition_state(1,-3.0,False)==0

def test_weights_are_market_neutral_and_gross_capped():
    pair_states=(
        _state((1,),left="A",right="B"),
        _state((-1,),left="C",right="D"),
    )
    weights=_weights_from_states(pair_states,0)
    assert abs(sum(weights.values())) < 1e-12
    assert abs(sum(abs(x) for x in weights.values())-1.0) < 1e-12
    assert weights["A"]>0 and weights["B"]<0
    assert weights["C"]<0 and weights["D"]>0

def test_no_active_pairs_means_cash():
    pair_states=(
        _state((0,),left="A",right="B"),
        _state((0,),left="C",right="D"),
    )
    weights=_weights_from_states(pair_states,0)
    assert all(abs(v)<1e-12 for v in weights.values())

def test_two_active_pairs_split_gross_equally():
    pair_states=(
        _state((1,),left="A",right="B"),
        _state((1,),left="C",right="D"),
    )
    weights=_weights_from_states(pair_states,0)
    assert abs(sum(abs(x) for x in weights.values())-1.0)<1e-12
    assert abs(weights["A"]-0.25)<1e-12
    assert abs(weights["B"]+0.25)<1e-12
