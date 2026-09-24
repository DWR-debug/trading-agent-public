"""Fixed lagged inverse-volatility allocator for the two established sleeves."""
from __future__ import annotations

from math import isfinite, sqrt


class SleeveRiskParityError(ValueError):
    """Raised for invalid sleeve-return inputs."""


WINDOW = 63
FALLBACK = (0.5, 0.5)


def _vol(values: list[float]) -> float | None:
    if len(values) < WINDOW:
        return None
    sample = values[-WINDOW:]
    if any(not isfinite(value) for value in sample):
        raise SleeveRiskParityError("Sleeve return history must be finite.")
    mean = sum(sample) / WINDOW
    variance = sum((value - mean) ** 2 for value in sample) / WINDOW
    return sqrt(variance)


def lagged_inverse_vol_weights(
    trend_returns: tuple[float, ...],
    cross_sectional_returns: tuple[float, ...],
) -> tuple[dict[str, float], ...]:
    """Allocate using only returns strictly prior to the current observation."""
    if len(trend_returns) != len(cross_sectional_returns):
        raise SleeveRiskParityError("Sleeve return series must have equal length.")
    if not trend_returns:
        return ()

    trend_history: list[float] = []
    cs_history: list[float] = []
    output: list[dict[str, float]] = []

    for index in range(len(trend_returns)):
        trend_vol = _vol(trend_history)
        cs_vol = _vol(cs_history)

        if trend_vol is None or cs_vol is None or trend_vol <= 0.0 or cs_vol <= 0.0:
            trend_weight, cs_weight = FALLBACK
        else:
            trend_inverse = 1.0 / trend_vol
            cs_inverse = 1.0 / cs_vol
            denominator = trend_inverse + cs_inverse
            trend_weight = trend_inverse / denominator
            cs_weight = cs_inverse / denominator

        if not (isfinite(trend_weight) and isfinite(cs_weight)):
            raise SleeveRiskParityError("Allocator produced non-finite weights.")
        if abs((trend_weight + cs_weight) - 1.0) > 1e-12:
            raise SleeveRiskParityError("Allocator weights must sum to 1.0.")
        if trend_weight < 0.0 or cs_weight < 0.0:
            raise SleeveRiskParityError("Allocator produced a negative sleeve weight.")

        output.append({"trend": trend_weight, "cross_sectional": cs_weight})
        trend_history.append(float(trend_returns[index]))
        cs_history.append(float(cross_sectional_returns[index]))

    return tuple(output)
