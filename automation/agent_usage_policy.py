"""Fail-closed policy for optional agent usage.

The repository never initiates paid agent/API consumption.
"""

from __future__ import annotations

from dataclasses import dataclass


class AgentUsagePolicyError(ValueError):
    pass


@dataclass(frozen=True)
class AgentUsageDecision:
    allowed: bool
    reason: str


def authorize_agent_usage(*,
    free_quota_available: bool,
    estimated_paid_cost_usd: float = 0.0,
) -> AgentUsageDecision:
    if estimated_paid_cost_usd < 0:
        raise AgentUsagePolicyError(
            "estimated_paid_cost_usd must be non-negative."
        )
    if estimated_paid_cost_usd > 0:
        return AgentUsageDecision(
            False,
            "Paid agent usage is disabled by project policy.",
        )
    if not free_quota_available:
        return AgentUsageDecision(
            False,
            "No externally verified free quota was supplied.",
        )
    return AgentUsageDecision(
        True,
        "Free agent quota explicitly asserted by caller.",
    )
