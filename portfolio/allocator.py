"""Deterministic portfolio exposure validation and sleeve composition."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping


class PortfolioAllocationError(ValueError):
    """Raised when a portfolio allocation violates explicit constraints."""


@dataclass(frozen=True)
class PortfolioConstraints:
    """Explicit, non-optimizing exposure limits."""

    gross_exposure_limit: float = 1.0
    net_exposure_limit: float = 1.0
    per_symbol_limit: float = 1.0

    def __post_init__(self) -> None:
        for name, value in (
            ("gross_exposure_limit", self.gross_exposure_limit),
            ("net_exposure_limit", self.net_exposure_limit),
            ("per_symbol_limit", self.per_symbol_limit),
        ):
            if not isfinite(value) or value < 0.0:
                raise PortfolioAllocationError(
                    f"{name} must be finite and non-negative."
                )


@dataclass(frozen=True)
class FixedPortfolioAllocator:
    """Validate or compose already-selected signed exposures.

    The allocator deliberately does not rank assets, optimize weights, normalize
    exposures, or infer risk budgets. Any constraint breach fails closed.
    """

    constraints: PortfolioConstraints = PortfolioConstraints()

    def validate(self, weights: Mapping[str, float]) -> dict[str, float]:
        if weights is None:
            raise PortfolioAllocationError("weights must not be None.")

        normalized: dict[str, float] = {}
        for symbol, value in weights.items():
            if not isinstance(symbol, str) or not symbol.strip():
                raise PortfolioAllocationError("Symbol names must be non-empty strings.")
            if not isfinite(float(value)):
                raise PortfolioAllocationError(f"Weight for {symbol} must be finite.")
            weight = float(value)
            if abs(weight) > self.constraints.per_symbol_limit + 1e-12:
                raise PortfolioAllocationError(
                    f"{symbol}: per-symbol exposure exceeds the configured limit."
                )
            normalized[symbol] = weight

        gross = sum(abs(value) for value in normalized.values())
        net = abs(sum(normalized.values()))
        if gross > self.constraints.gross_exposure_limit + 1e-12:
            raise PortfolioAllocationError(
                f"Gross exposure {gross:.10f} exceeds "
                f"limit {self.constraints.gross_exposure_limit:.10f}."
            )
        if net > self.constraints.net_exposure_limit + 1e-12:
            raise PortfolioAllocationError(
                f"Net exposure {net:.10f} exceeds "
                f"limit {self.constraints.net_exposure_limit:.10f}."
            )
        return dict(sorted(normalized.items()))

    def compose(
        self,
        sleeves: Mapping[str, Mapping[str, float]],
    ) -> dict[str, float]:
        if sleeves is None:
            raise PortfolioAllocationError("sleeves must not be None.")

        combined: dict[str, float] = {}
        for sleeve_name, weights in sleeves.items():
            if not isinstance(sleeve_name, str) or not sleeve_name.strip():
                raise PortfolioAllocationError("Sleeve names must be non-empty strings.")
            for symbol, weight in weights.items():
                combined[symbol] = combined.get(symbol, 0.0) + float(weight)

        return self.validate(combined)
