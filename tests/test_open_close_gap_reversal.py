import pytest

from research.open_close_gap_reversal import (
    OpenCloseGapReversalError,
    OpenCloseGapReversalPolicy,
)


def test_policy_has_eight_equal_weight_symbols():
    policy = OpenCloseGapReversalPolicy()
    assert len(policy.symbols) == 8
    assert len(set(policy.symbols)) == 8
    assert policy.weight == pytest.approx(0.125)


def test_negative_gap_is_long():
    policy = OpenCloseGapReversalPolicy()
    assert policy.signal(-0.01) == 1
    assert policy.target_weight(-0.01, "SPYM") == pytest.approx(0.125)


def test_positive_gap_is_short():
    policy = OpenCloseGapReversalPolicy()
    assert policy.signal(0.01) == -1
    assert policy.target_weight(0.01, "SPYM") == pytest.approx(-0.125)


def test_zero_gap_is_flat():
    policy = OpenCloseGapReversalPolicy()
    assert policy.signal(0.0) == 0
    assert policy.target_weight(0.0, "SPYM") == pytest.approx(0.0)


def test_unknown_symbol_is_rejected():
    with pytest.raises(OpenCloseGapReversalError):
        OpenCloseGapReversalPolicy().target_weight(0.01, "UNKNOWN")
