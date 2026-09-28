from automation.rccsm_transition_diagnostics import _fp, state_velocity


def test_state_velocity_is_mean_absolute_movement():
    previous={"trend_coherence":0.5,"breadth":0.5,"dispersion_percentile":0.2,"shock_density":0.0}
    current={"trend_coherence":0.7,"breadth":0.4,"dispersion_percentile":0.6,"shock_density":0.1}
    assert state_velocity(previous,current)==0.2


def test_state_velocity_is_deterministic():
    state={"trend_coherence":0.5,"breadth":0.5,"dispersion_percentile":0.5,"shock_density":0.5}
    assert state_velocity(state,state)==0.0


def test_fingerprint_is_stable():
    assert _fp({"x":[1,2],"y":3})==_fp({"y":3,"x":[1,2]})


def test_transition_diagnostics_are_non_performance_by_contract():
    import automation.rccsm_transition_diagnostics as module
    assert module.STATE_COMPONENTS == ("trend_coherence","breadth","dispersion_percentile","shock_density")
    assert module.CANDIDATES
