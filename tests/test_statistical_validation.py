import math

import pytest

from research.statistical_validation import (
    StatisticalValidationError,
    deflated_sharpe_ratio,
    describe_returns,
    expected_maximum_sharpe,
    probabilistic_sharpe_ratio,
)


def test_describe_returns_uses_non_annualized_sharpe_and_raw_kurtosis():
    values = (-1.0, 0.0, 1.0)
    result = describe_returns(values)

    assert result.observation_count == 3
    assert abs(result.sharpe_ratio) < 1e-15
    assert abs(result.skewness) < 1e-15
    assert abs(result.kurtosis - 1.5) < 1e-15


def test_psr_increases_with_more_positive_evidence():
    weak = probabilistic_sharpe_ratio((-0.01, 0.0, 0.01, 0.0))
    strong = probabilistic_sharpe_ratio((0.01, 0.02, 0.01, 0.03))

    assert 0.0 <= weak <= 1.0
    assert 0.0 <= strong <= 1.0
    assert strong > weak


def test_expected_maximum_sharpe_is_zero_for_one_trial():
    assert expected_maximum_sharpe(
        independent_trial_count=1,
        trial_sharpe_dispersion=2.0,
    ) == 0.0


def test_expected_maximum_sharpe_rises_with_trial_count():
    low = expected_maximum_sharpe(
        independent_trial_count=10,
        trial_sharpe_dispersion=0.5,
    )
    high = expected_maximum_sharpe(
        independent_trial_count=1000,
        trial_sharpe_dispersion=0.5,
    )

    assert high > low > 0.0


def test_dsr_deflates_a_selected_sharpe_against_trial_family():
    returns = (0.01, 0.02, 0.015, 0.01, 0.025, 0.018)
    trial_sharpes = (0.10, 0.20, 0.30, 0.25, 0.15)

    result = deflated_sharpe_ratio(
        returns,
        independent_trial_count=5,
        trial_sharpes=trial_sharpes,
    )

    assert 0.0 <= result.probability <= 1.0
    assert result.benchmark_sharpe > 0.0
    assert result.expected_maximum_sharpe == result.benchmark_sharpe
    assert result.trial_sharpe_dispersion > 0.0


@pytest.mark.parametrize(
    "returns",
    [
        (),
        (1.0, 1.0),
        (1.0, 1.0, 1.0),
        (1.0, float("nan"), 2.0),
        (1.0, float("inf"), 2.0),
    ],
)
def test_invalid_return_series_is_rejected(returns):
    with pytest.raises(StatisticalValidationError):
        describe_returns(returns)


def test_invalid_trial_contract_is_rejected():
    with pytest.raises(StatisticalValidationError):
        deflated_sharpe_ratio(
            (0.01, 0.02, 0.03),
            independent_trial_count=3,
            trial_sharpes=(0.1,),
        )

    with pytest.raises(StatisticalValidationError):
        deflated_sharpe_ratio(
            (0.01, 0.02, 0.03),
            independent_trial_count=4,
            trial_sharpes=(0.1, 0.2, 0.3),
        )


def test_dsr_is_finite_for_skewed_heavy_tailed_sample():
    returns = (-0.20, 0.03, 0.02, 0.01, 0.04, 0.02, 0.03, 0.02)
    result = deflated_sharpe_ratio(
        returns,
        independent_trial_count=4,
        trial_sharpes=(-0.2, 0.1, 0.3, 0.4),
    )

    assert math.isfinite(result.probability)
    assert math.isfinite(result.benchmark_sharpe)
    assert math.isfinite(result.skewness)
    assert math.isfinite(result.kurtosis)
