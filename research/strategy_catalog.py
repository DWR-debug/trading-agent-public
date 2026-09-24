"""Canonical research-status snapshot for current strategy families.

This catalog is governance metadata only. It never changes production settings
and never authorizes orders.
"""
from __future__ import annotations

from research.strategy_lifecycle import StrategyRecord, StrategyRegistry


def current_strategy_registry() -> StrategyRegistry:
    return StrategyRegistry(
        (
            StrategyRecord(
                "CORE_50_50_VOL_BUDGET",
                "multi_asset",
                status="BLOCKED",
                evidence_ids=("candidate-validation-50-50-vol-budget",),
                notes="Robustness candidate remains blocked; no production promotion.",
            ),
            StrategyRecord(
                "TRIAL_014_LONG_SHORT_LEVERAGE",
                "long_short_leverage",
                status="REJECTED",
                evidence_ids=("trial-014",),
                notes="Leverage/short exposure amplified drawdown and did not establish robust alpha.",
            ),
            StrategyRecord(
                "TRIAL_015_MEAN_REVERSION_GLOBAL_ETFS",
                "mean_reversion",
                status="REJECTED",
                evidence_ids=("trial-015",),
                notes="Holdout was positive but Research/Rolling robustness was insufficient.",
            ),
            StrategyRecord(
                "TRIAL_016_CROSS_ASSET_MOMENTUM",
                "cross_sectional_momentum",
                status="REJECTED",
                evidence_ids=("trial-016",),
                notes="Holdout was positive but Research/Rolling evidence remained insufficient.",
            ),
            StrategyRecord(
                "TRIAL_017_POLITICAL_EVENT_INTELLIGENCE",
                "event_intelligence",
                status="RESEARCH",
                evidence_ids=("trial-017-baseline",),
                inspirations=("GDELT 2.0",),
                notes="Descriptive point-in-time baseline; no trading selection.",
            ),
        )
    )
