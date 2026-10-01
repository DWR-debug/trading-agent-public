from automation.q113_13f_q107_coverage import find_target, synthetic_contract

def test_q113_synthetic_contract():
    assert all(synthetic_contract().values())

def test_q113_issuer_alias():
    assert find_target("Williams Companies, Inc.") == "WMB"

def test_q113_unknown_not_inferred():
    assert find_target("Some Unlisted Company Inc.") is None
