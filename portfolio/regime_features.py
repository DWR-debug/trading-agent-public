"""Research-only market-regime feature extraction.

The extractor computes lagged descriptive features from already observed
returns. It deliberately does not assign a predictive regime label and does
not produce an allocation or execution instruction.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Mapping, Sequence

class RegimeFeatureError(ValueError):
    """Raised when regime feature inputs are invalid."""

@dataclass(frozen=True)
class RegimeFeatureSnapshot:
    observation_count: int
    asset_count: int
    realized_volatility: float
    positive_asset_breadth: float
    cross_sectional_dispersion: float
    downside_asset_breadth: float
    mean_pairwise_correlation: float

    def as_mapping(self) -> dict[str, float]:
        return {
            "observation_count": float(self.observation_count),
            "asset_count": float(self.asset_count),
            "realized_volatility": self.realized_volatility,
            "positive_asset_breadth": self.positive_asset_breadth,
            "cross_sectional_dispersion": self.cross_sectional_dispersion,
            "downside_asset_breadth": self.downside_asset_breadth,
            "mean_pairwise_correlation": self.mean_pairwise_correlation,
        }

def _validate(returns_by_asset: Mapping[str, Sequence[float]], window: int) -> tuple[tuple[str, ...], int]:
    names = tuple(sorted(returns_by_asset))
    if len(names) < 2:
        raise RegimeFeatureError("At least two return series are required.")
    if window < 2:
        raise RegimeFeatureError("window must be at least 2.")
    lengths = {len(returns_by_asset[name]) for name in names}
    if len(lengths) != 1:
        raise RegimeFeatureError("All return series must have equal length.")
    length = next(iter(lengths))
    if length < window:
        raise RegimeFeatureError("Insufficient history for the requested window.")
    for name in names:
        if any(not math.isfinite(float(value)) for value in returns_by_asset[name]):
            raise RegimeFeatureError(f"Non-finite return in {name}.")
    return names, length

def _correlation(a: Sequence[float], b: Sequence[float]) -> float:
    ma, mb = mean(a), mean(b)
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    va = sum(x * x for x in da)
    vb = sum(x * x for x in db)
    if va == 0.0 or vb == 0.0:
        return 0.0
    return sum(x * y for x, y in zip(da, db)) / math.sqrt(va * vb)

def extract_regime_features(
    returns_by_asset: Mapping[str, Sequence[float]],
    *,
    market_returns: Sequence[float] | None = None,
    window: int = 63,
) -> RegimeFeatureSnapshot:
    """Extract lagged descriptive features; never labels or ranks regimes."""
    names, length = _validate(returns_by_asset, window)
    sample = {name: tuple(float(x) for x in returns_by_asset[name][-window:]) for name in names}
    if market_returns is None:
        market = tuple(
            sum(sample[name][i] for name in names) / len(names)
            for i in range(window)
        )
    else:
        if len(market_returns) != length:
            raise RegimeFeatureError("market_returns must match asset-series length.")
        if any(not math.isfinite(float(x)) for x in market_returns):
            raise RegimeFeatureError("market_returns must be finite.")
        market = tuple(float(x) for x in market_returns[-window:])

    annualized_vol = pstdev(market) * math.sqrt(252.0)
    latest = tuple(sample[name][-1] for name in names)
    breadth = sum(value > 0.0 for value in latest) / len(latest)
    downside = sum(value < 0.0 for value in latest) / len(latest)
    dispersion = pstdev(latest)

    correlations = []
    for left_index, left in enumerate(names):
        for right in names[left_index + 1:]:
            correlations.append(_correlation(sample[left], sample[right]))

    return RegimeFeatureSnapshot(
        observation_count=window,
        asset_count=len(names),
        realized_volatility=annualized_vol,
        positive_asset_breadth=breadth,
        cross_sectional_dispersion=dispersion,
        downside_asset_breadth=downside,
        mean_pairwise_correlation=mean(correlations) if correlations else 0.0,
    )
