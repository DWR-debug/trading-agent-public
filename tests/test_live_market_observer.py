from automation.live_market_observer import _corr, _lagged_corr


def test_corr_identical_series():
    assert _corr([1, 2, 3, 4], [1, 2, 3, 4]) == 1.0


def test_lagged_corr_uses_past_peer_values():
    assert _lagged_corr([1, 2, 4, 8, 16], [1, 2, 4, 8, 16], 1) > 0.99
