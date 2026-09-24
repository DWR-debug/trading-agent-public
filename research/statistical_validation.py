"""Selection-aware statistical diagnostics for Research validation.

Research-only helpers implementing the Probabilistic Sharpe Ratio (PSR) and
the Deflated Sharpe Ratio (DSR) approximation described by Bailey and
Lopez de Prado (2014).

The functions require an explicit return series and an explicit trial set.
They do not infer independent trials from a raw parameter count and never
produce a production decision.

No network access.
No order execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, sqrt
from statistics import NormalDist
from typing import Iterable


_EULER_MASCHERONI = 0.5772156649015329
_STANDARD_NORMAL = NormalDist()


class StatisticalValidationError(ValueError):
    """Raised when the statistical input contract is violated."""


@dataclass(frozen=True)
class SharpeDistribution:
    """Descriptive statistics of an observed per-period return series."""

    observation_count: int
    sharpe_ratio: float
    skewness: float
    kurtosis: float


@dataclass(frozen=True)
class DeflatedSharpeResult:
    """Selection-aware Sharpe diagnostic.

    probability is the DSR probability associated with the observed Sharpe
    against the supplied selection-aware benchmark.
    """

    probability: float
    observed_sharpe: float
    benchmark_sharpe: float
    expected_maximum_sharpe: float
    observation_count: int
    independent_trial_count: int
    trial_sharpe_dispersion: float
    skewness: float
    kurtosis: float


def _finite_returns(returns: Iterable[float]) -> tuple[float, ...]:
    values = tuple(float(value) for value in returns)
    if len(values) < 3:
        raise StatisticalValidationError(
            "Mindestens 3 Return-Beobachtungen werden benötigt."
        )
    if not all(isfinite(value) for value in values):
        raise StatisticalValidationError(
            "Return-Serie darf keine NaN/Infinity-Werte enthalten."
        )
    return values


def _sample_moments(
    values: tuple[float, ...],
) -> tuple[float, float, float, float]:
    mean = sum(values) / len(values)
    centered = tuple(value - mean for value in values)
    second = sum(value * value for value in centered) / len(values)

    if second <= 0.0 or not isfinite(second):
        raise StatisticalValidationError(
            "Return-Serie muss positive Varianz besitzen."
        )

    scale = sqrt(second)
    third = sum(value**3 for value in centered) / len(values)
    fourth = sum(value**4 for value in centered) / len(values)
    skewness = third / scale**3
    kurtosis = fourth / scale**4

    if not isfinite(skewness) or not isfinite(kurtosis):
        raise StatisticalValidationError(
            "Skewness/Kurtosis konnten nicht stabil berechnet werden."
        )

    return mean, scale, skewness, kurtosis


def describe_returns(returns: Iterable[float]) -> SharpeDistribution:
    """Return the non-annualized Sharpe and raw Pearson kurtosis."""

    values = _finite_returns(returns)
    mean, scale, skewness, kurtosis = _sample_moments(values)
    return SharpeDistribution(
        observation_count=len(values),
        sharpe_ratio=mean / scale,
        skewness=skewness,
        kurtosis=kurtosis,
    )


def _psr_z_score(
    stats: SharpeDistribution,
    benchmark_sharpe: float,
) -> float:
    denominator_squared = (
        1.0
        - stats.skewness * stats.sharpe_ratio
        + ((stats.kurtosis - 1.0) / 4.0)
        * stats.sharpe_ratio**2
    )

    if denominator_squared <= 0.0 or not isfinite(denominator_squared):
        raise StatisticalValidationError(
            "Sharpe-Varianzkorrektur ist nicht positiv."
        )

    return (
        (stats.sharpe_ratio - benchmark_sharpe)
        * sqrt(stats.observation_count - 1)
        / sqrt(denominator_squared)
    )


def probabilistic_sharpe_ratio(
    returns: Iterable[float],
    *,
    benchmark_sharpe: float = 0.0,
) -> float:
    """Estimate PSR for the true Sharpe exceeding benchmark_sharpe."""

    if not isfinite(benchmark_sharpe):
        raise StatisticalValidationError(
            "benchmark_sharpe muss endlich sein."
        )

    stats = describe_returns(returns)
    return _STANDARD_NORMAL.cdf(
        _psr_z_score(stats, benchmark_sharpe)
    )


def _expected_maximum_standard_normal(trial_count: int) -> float:
    if trial_count <= 1:
        return 0.0

    first_tail = 1.0 - (1.0 / trial_count)
    second_tail = 1.0 - (1.0 / (trial_count * exp(1.0)))

    return (
        (1.0 - _EULER_MASCHERONI)
        * _STANDARD_NORMAL.inv_cdf(first_tail)
        + _EULER_MASCHERONI
        * _STANDARD_NORMAL.inv_cdf(second_tail)
    )


def expected_maximum_sharpe(
    *,
    independent_trial_count: int,
    trial_sharpe_dispersion: float,
    null_mean_sharpe: float = 0.0,
) -> float:
    """Return the DSR selection benchmark for the declared trials.

    The caller must distinguish independent trials from raw parameter
    combinations. Correlated candidates can contain less independent
    information than their raw count suggests.
    """

    if independent_trial_count < 1:
        raise StatisticalValidationError(
            "independent_trial_count muss mindestens 1 sein."
        )
    if not isfinite(trial_sharpe_dispersion) or trial_sharpe_dispersion < 0.0:
        raise StatisticalValidationError(
            "trial_sharpe_dispersion muss endlich und nicht-negativ sein."
        )
    if not isfinite(null_mean_sharpe):
        raise StatisticalValidationError(
            "null_mean_sharpe muss endlich sein."
        )

    return (
        null_mean_sharpe
        + trial_sharpe_dispersion
        * _expected_maximum_standard_normal(independent_trial_count)
    )


def deflated_sharpe_ratio(
    returns: Iterable[float],
    *,
    independent_trial_count: int,
    trial_sharpes: Iterable[float],
    null_mean_sharpe: float = 0.0,
) -> DeflatedSharpeResult:
    """Compute DSR from one observed return series and retained trial Sharpes.

    trial_sharpes must represent the trial family that underpinned selection.
    independent_trial_count is an explicit model input and is never inferred
    from a parameter-grid size.
    """

    values = _finite_returns(returns)
    trials = tuple(float(value) for value in trial_sharpes)

    if len(trials) < 2:
        raise StatisticalValidationError(
            "Mindestens zwei Trial-Sharpes werden für DSR benötigt."
        )
    if not all(isfinite(value) for value in trials):
        raise StatisticalValidationError(
            "Trial-Sharpes dürfen keine NaN/Infinity-Werte enthalten."
        )
    if independent_trial_count > len(trials):
        raise StatisticalValidationError(
            "independent_trial_count darf die gespeicherte Trial-Anzahl "
            "nicht überschreiten."
        )

    stats = describe_returns(values)
    trial_mean = sum(trials) / len(trials)
    trial_variance = sum(
        (value - trial_mean) ** 2 for value in trials
    ) / len(trials)
    trial_dispersion = sqrt(trial_variance)

    benchmark = expected_maximum_sharpe(
        independent_trial_count=independent_trial_count,
        trial_sharpe_dispersion=trial_dispersion,
        null_mean_sharpe=null_mean_sharpe,
    )

    probability = _STANDARD_NORMAL.cdf(
        _psr_z_score(stats, benchmark)
    )

    return DeflatedSharpeResult(
        probability=probability,
        observed_sharpe=stats.sharpe_ratio,
        benchmark_sharpe=benchmark,
        expected_maximum_sharpe=benchmark,
        observation_count=stats.observation_count,
        independent_trial_count=independent_trial_count,
        trial_sharpe_dispersion=trial_dispersion,
        skewness=stats.skewness,
        kurtosis=stats.kurtosis,
    )
