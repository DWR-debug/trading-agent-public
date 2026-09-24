import pytest
from portfolio.regime_features import RegimeFeatureError, extract_regime_features


def test_feature_snapshot_is_deterministic_and_descriptive():
    returns = {
        "a": (0.01, 0.02, -0.01, 0.03),
        "b": (0.00, 0.01, -0.02, 0.02),
        "c": (-0.01, 0.02, 0.00, 0.01),
    }
    first = extract_regime_features(returns, window=4)
    second = extract_regime_features(returns, window=4)
    assert first == second
    assert first.observation_count == 4
    assert first.asset_count == 3
    assert 0.0 <= first.positive_asset_breadth <= 1.0
    assert 0.0 <= first.downside_asset_breadth <= 1.0
    assert first.realized_volatility >= 0.0
    assert first.cross_sectional_dispersion >= 0.0
    assert -1.0 <= first.mean_pairwise_correlation <= 1.0


def test_explicit_market_series_is_used_without_future_access():
    returns = {"a": (0.01, -0.01, 0.02), "b": (0.00, 0.01, -0.02)}
    market = (0.005, 0.0, -0.001)
    result = extract_regime_features(returns, market_returns=market, window=3)
    assert result.observation_count == 3
    assert result.realized_volatility == pytest.approx(
        (sum((x - sum(market) / 3) ** 2 for x in market) / 3) ** 0.5 * 252 ** 0.5
    )


def test_rejects_misaligned_series():
    with pytest.raises(RegimeFeatureError):
        extract_regime_features({"a": (0.01, 0.02), "b": (0.01,)}, window=2)


def test_rejects_insufficient_history():
    with pytest.raises(RegimeFeatureError):
        extract_regime_features({"a": (0.01,), "b": (0.02,)}, window=2)


def test_rejects_non_finite_returns():
    with pytest.raises(RegimeFeatureError):
        extract_regime_features({"a": (0.01, float("nan")), "b": (0.02, 0.03)}, window=2)


def test_rejects_misaligned_market_series():
    with pytest.raises(RegimeFeatureError):
        extract_regime_features({"a": (0.01, 0.02), "b": (0.02, 0.03)}, market_returns=(0.01,), window=2)