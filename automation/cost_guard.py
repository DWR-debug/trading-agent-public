"""Cost and compute guardrails for autonomous research.

This module is a local policy gate, not a billing meter. Actual provider
billing must be enforced and verified independently at the provider/project
level. Deterministic research must run locally without API calls whenever
possible.
"""

from dataclasses import dataclass
import math


@dataclass
class ResearchBudget:
    total_usd: float = 1.00
    max_round_usd: float = 0.25
    max_rounds: int = 4
    rounds_used: int = 0
    committed_usd: float = 0.0

    def __post_init__(self):
        for name, value in (
            ("total_usd", self.total_usd),
            ("max_round_usd", self.max_round_usd),
            ("committed_usd", self.committed_usd),
        ):
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} muss endlich und nicht negativ sein.")

        if self.total_usd <= 0:
            raise ValueError("total_usd muss positiv sein.")

        if self.max_round_usd <= 0:
            raise ValueError("max_round_usd muss positiv sein.")

        if self.max_round_usd > self.total_usd:
            raise ValueError("max_round_usd darf total_usd nicht überschreiten.")

        if self.max_rounds < 1:
            raise ValueError("max_rounds muss mindestens 1 sein.")

        if self.rounds_used < 0 or self.rounds_used > self.max_rounds:
            raise ValueError("rounds_used muss zwischen 0 und max_rounds liegen.")

        if self.committed_usd > self.total_usd:
            raise ValueError("committed_usd darf total_usd nicht überschreiten.")

    def approve_round(self, estimated_usd: float) -> bool:
        """Reserve one research round against the local policy budget."""
        if not math.isfinite(estimated_usd) or estimated_usd < 0:
            raise ValueError("estimated_usd muss endlich und nicht negativ sein.")

        if self.rounds_used >= self.max_rounds:
            return False

        if estimated_usd > self.max_round_usd:
            return False

        if self.committed_usd + estimated_usd > self.total_usd:
            return False

        self.rounds_used += 1
        self.committed_usd += estimated_usd
        return True


DEFAULT_BUDGET = ResearchBudget()


def deterministic_research_allowed() -> bool:
    return True
