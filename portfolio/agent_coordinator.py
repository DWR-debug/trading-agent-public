"""Fail-closed decision coordinator for the adaptive agent architecture."""

from dataclasses import dataclass

from portfolio.market_state import MarketStateObservation
from portfolio.strategy_allocator import (
    AllocationDecision,
    EvidenceGatedStrategyAllocator,
    StrategyAssessment,
)


@dataclass(frozen=True)
class AgentDecision:
    market_state: MarketStateObservation
    allocation: AllocationDecision
    action: str


class EvidenceGatedAgentCoordinator:
    """Connect state recognition and strategy allocation without execution."""

    def __init__(self, allocator: EvidenceGatedStrategyAllocator | None = None) -> None:
        self.allocator = allocator or EvidenceGatedStrategyAllocator()

    def decide(
        self,
        market_state: MarketStateObservation,
        assessments: tuple[StrategyAssessment, ...],
    ) -> AgentDecision:
        if not market_state.validated:
            allocation = AllocationDecision(
                strategy_exposure={},
                cash_exposure=1.0,
                reason="UNVALIDATED_MARKET_STATE",
            )
            return AgentDecision(
                market_state=market_state,
                allocation=allocation,
                action="HOLD_CASH",
            )

        allocation = self.allocator.allocate(assessments)
        action = "ALLOCATE_STRATEGIES" if allocation.strategy_exposure else "HOLD_CASH"
        return AgentDecision(
            market_state=market_state,
            allocation=allocation,
            action=action,
        )
