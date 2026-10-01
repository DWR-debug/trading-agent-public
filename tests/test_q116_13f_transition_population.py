from automation.q116_13f_transition_population import synthetic_contract, find_target

def test_q116_synthetic():
    assert all(synthetic_contract().values())

def test_q116_alias():
    assert find_target("Williams Companies, Inc.") == "WMB"
