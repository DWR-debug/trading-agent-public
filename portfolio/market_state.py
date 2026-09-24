"""Market-state observation contract for the trading agent.

This module deliberately does not implement a predictive regime model.
It defines the fail-closed interface a future validated model must satisfy.
"""

from dataclasses import dataclass
from typing import Mapping


class MarketStateError(ValueError):
    """Raised when a market-state observation is invalid."""


@dataclass(frozen=True)
class MarketStateObservation:
    state_id: str
    confidence: float
    validated: bool
    features: Mapping[str, float]
    rationale: str

    def __post_init__(self) -> None:
        if not self.state_id:
            raise MarketStateError("state_id must not be empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise MarketStateError("confidence must be between 0.0 and 1.0.")
        if not self.rationale:
            raise MarketStateError("rationale must not be empty.")
        for name, value in self.features.items():
            if not isinstance(name, str) or not name:
                raise MarketStateError("Feature names must be non-empty strings.")
            if not isinstance(value, (int, float)):
                raise MarketStateError("Feature values must be numeric.")


class UnknownMarketStateObserver:
    """Safe placeholder until a state model has independent OOS evidence."""

    def observe(self, features: Mapping[str, float] | None = None) -> MarketStateObservation:
        return MarketStateObservation(
            state_id="UNKNOWN",
            confidence=0.0,
            validated=False,
            features={} if features is None else dict(features),
            rationale="No independently validated market-state model is installed.",
        )
