from automation.risk_layer_persistence_control_2026_09_23 import _cum_return

def test_forward_return_requires_complete_window():
    assert _cum_return([{"net_return":0.01}], 0, 2) is None

def test_forward_return_compounds():
    value = _cum_return([{"net_return":0.01},{"net_return":0.02}], 0, 2)
    assert abs(value - 0.0302) < 1e-12
