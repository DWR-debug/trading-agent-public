"""Evidence-gated multi-strategy allocation primitives.

No market prediction is performed here. A future validated regime/state
component supplies suitability observations; this allocator only enforces the
evidence and exposure contract and can fail closed to cash.
"""

from dataclasses import dataclass
from typing import Mapping


class StrategyAllocationError(ValueError):
    """Raised when a strategy assessment violates the allocation contract."""


@dataclass(frozen=True)
class StrategyAssessment:
    strategy_id: str
    evidence_eligible: bool
    suitability_score: float
    signal_confidence: float
    requested_exposure: float = 1.0
    max_exposure: float = 1.0
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.strategy_id:
            raise StrategyAllocationError("Strategy ID must not be empty.")

        for name, value in (
            ("suitability_score", self.suitability_score),
            ("signal_confidence", self.signal_confidence),
            ("requested_exposure", self.requested_exposure),
            ("max_exposure", self.max_exposure),
        ):
            if not 0.0 <= value <= 1.0:
                raise StrategyAllocationError(
                    f"{name} must be between 0.0 and 1.0."
                )

        if self.max_exposure > self.requested_exposure:
            raise StrategyAllocationError(
                "max_exposure must not exceed requested_exposure."
            )


@dataclass(frozen=True)
class AllocationDecision:
    strategy_exposure: Mapping[str, float]
    cash_exposure: float
    reason: str

    @property
    def total_exposure(self) -> float:
        return sum(self.strategy_exposure.values())


class EvidenceGatedStrategyAllocator:
    """Turn validated strategy assessments into conservative allocations.

    Suitability and confidence are inputs, not a claim that the allocator can
    predict regimes. A separate research-validated state model is responsible
    for those inputs.

    If no strategy is evidence-eligible, the result is 100% cash exposure.
    """

    def __init__(self, total_exposure_cap: float = 1.0) -> None:
        if not 0.0 <= total_exposure_cap <= 1.0:
            raise StrategyAllocationError(
                "Total exposure cap must be between 0.0 and 1.0."
            )
        self.total_exposure_cap = total_exposure_cap

    def allocate(
        self,
        assessments: tuple[StrategyAssessment, ...],
    ) -> AllocationDecision:
        if not assessments:
            return AllocationDecision(
                strategy_exposure={},
                cash_exposure=1.0,
                reason="NO_STRATEGY_ASSESSMENTS",
            )

        ids = [assessment.strategy_id for assessment in assessments]
        if len(ids) != len(set(ids)):
            raise StrategyAllocationError("Strategy IDs must be unique.")

        eligible = [
            assessment
            for assessment in assessments
            if assessment.evidence_eligible
        ]
        if not eligible or self.total_exposure_cap == 0.0:
            return AllocationDecision(
                strategy_exposure={},
                cash_exposure=1.0,
                reason="NO_EVIDENCE_ELIGIBLE_STRATEGY",
            )

        scores = {
            assessment.strategy_id: (
                assessment.suitability_score
                * assessment.signal_confidence
                * assessment.requested_exposure
            )
            for assessment in eligible
        }

        score_total = sum(scores.values())
        if score_total <= 0.0:
            return AllocationDecision(
                strategy_exposure={},
                cash_exposure=1.0,
                reason="NO_POSITIVE_SUITABILITY",
            )

        scale = min(1.0, self.total_exposure_cap / score_total)
        allocations = {}
        for assessment in eligible:
            score = scores[assessment.strategy_id]
            allocations[assessment.strategy_id] = min(
                assessment.max_exposure,
                score * scale,
            )

        total = sum(allocations.values())
        if total <= 0.0:
            return AllocationDecision(
                strategy_exposure={},
                cash_exposure=1.0,
                reason="EXPOSURE_CAP_REDUCED_TO_CASH",
            )

        return AllocationDecision(
            strategy_exposure={
                strategy_id: exposure
                for strategy_id, exposure in allocations.items()
                if exposure > 0.0
            },
            cash_exposure=max(0.0, 1.0 - total),
            reason="EVIDENCE_GATED_ALLOCATION",
        )
