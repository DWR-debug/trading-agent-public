"""Research execution-cost compatibility contract.

This contract detects cost-semantic drift without changing legacy broker defaults.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


class ExecutionCostCompatibilityError(ValueError):
    """Raised when an execution component cannot represent the research cost contract."""


@dataclass(frozen=True)
class ResearchExecutionCostContract:
    """Canonical cost assumptions used by the current research controls."""

    fee_bps: float = 10.0
    slippage_bps: float = 5.0

    @property
    def total_one_way_bps(self) -> float:
        return self.fee_bps + self.slippage_bps

    @property
    def total_round_trip_bps(self) -> float:
        return 2.0 * self.total_one_way_bps

    def validate(self) -> None:
        for name, value in (
            ("fee_bps", self.fee_bps),
            ("slippage_bps", self.slippage_bps),
        ):
            if not isfinite(value) or value < 0.0:
                raise ExecutionCostCompatibilityError(
                    f"{name} must be finite and non-negative."
                )


def validate_research_cost_compatibility(
    *,
    fee_rate: float,
    slippage_rate: float,
    contract: ResearchExecutionCostContract | None = None,
) -> None:
    """Fail closed unless execution assumptions equal the research contract."""
    contract = contract or ResearchExecutionCostContract()
    contract.validate()

    actual_fee_bps = float(fee_rate) * 10_000.0
    actual_slippage_bps = float(slippage_rate) * 10_000.0

    if abs(actual_fee_bps - contract.fee_bps) > 1e-12:
        raise ExecutionCostCompatibilityError(
            f"Fee mismatch: {actual_fee_bps:.8f} bps vs "
            f"research contract {contract.fee_bps:.8f} bps."
        )
    if abs(actual_slippage_bps - contract.slippage_bps) > 1e-12:
        raise ExecutionCostCompatibilityError(
            f"Slippage mismatch: {actual_slippage_bps:.8f} bps vs "
            f"research contract {contract.slippage_bps:.8f} bps."
        )


def paper_broker_research_compatibility() -> dict[str, object]:
    """Report the legacy PaperBroker default without mutating it."""
    from execution.paper_broker import PaperBroker

    defaults = PaperBroker.__init__.__defaults__ or ()
    if len(defaults) < 3:
        raise ExecutionCostCompatibilityError(
            "PaperBroker constructor defaults are not introspectable."
        )

    _, fee_rate, slippage_rate = defaults
    contract = ResearchExecutionCostContract()
    return {
        "research_fee_bps": contract.fee_bps,
        "research_slippage_bps": contract.slippage_bps,
        "paper_broker_default_fee_bps": float(fee_rate) * 10_000.0,
        "paper_broker_default_slippage_bps": float(slippage_rate) * 10_000.0,
        "research_compatible": (
            abs(float(fee_rate) * 10_000.0 - contract.fee_bps) <= 1e-12
            and abs(float(slippage_rate) * 10_000.0 - contract.slippage_bps) <= 1e-12
        ),
        "status": "LEGACY_BROKER_DEFAULT_NOT_RESEARCH_COMPATIBLE",
    }
