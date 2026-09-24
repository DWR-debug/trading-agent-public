"""Fixed, research-only event-driven relative-value alpha family."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from research.event_intelligence import EventFeatures

class EventAlphaError(ValueError):
    """Raised for malformed event-alpha policy inputs."""

@dataclass(frozen=True)
class EventRelativeValuePolicy:
    """Single preregisterable event response; no optimisation is performed."""
    risk_asset: str = "IWB"
    defensive_asset_a: str = "GDX"
    defensive_asset_b: str = "BIL"
    risk_weight: float = -0.50
    defensive_weight_a: float = 0.25
    defensive_weight_b: float = 0.25

    def __post_init__(self) -> None:
        names = (self.risk_asset, self.defensive_asset_a, self.defensive_asset_b)
        if any(not name.strip() for name in names):
            raise EventAlphaError("Asset names must not be empty.")
        if len(set(names)) != 3:
            raise EventAlphaError("Event relative-value assets must be distinct.")
        weights = (self.risk_weight, self.defensive_weight_a, self.defensive_weight_b)
        if abs(sum(weights)) > 1e-12:
            raise EventAlphaError("Policy must be market-neutral at zero transaction cost.")
        if abs(sum(abs(weight) for weight in weights) - 1.0) > 1e-12:
            raise EventAlphaError("Policy gross exposure must equal 1.0x.")

    @property
    def symbols(self) -> tuple[str, str, str]:
        return self.risk_asset, self.defensive_asset_a, self.defensive_asset_b

    @property
    def weights(self) -> Mapping[str, float]:
        return {
            self.risk_asset: self.risk_weight,
            self.defensive_asset_a: self.defensive_weight_a,
            self.defensive_asset_b: self.defensive_weight_b,
        }

def qualifying_event(features: EventFeatures) -> bool:
    """Fixed event condition using only already aggregated PIT event features."""
    return (
        features.international_material_conflict_count > 0
        and features.high_confidence_international_count > 0
    )

def target_weights(
    features: EventFeatures,
    policy: EventRelativeValuePolicy | None = None,
) -> dict[str, float]:
    """Return the fixed position map or an empty map for a neutral day."""
    policy = policy or EventRelativeValuePolicy()
    return dict(policy.weights) if qualifying_event(features) else {}

def gross_exposure(weights: Mapping[str, float]) -> float:
    return sum(abs(float(value)) for value in weights.values())

def net_exposure(weights: Mapping[str, float]) -> float:
    return sum(float(value) for value in weights.values())
