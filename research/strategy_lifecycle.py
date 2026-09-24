"""Fail-closed lifecycle and strategy registry primitives."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable

class LifecycleError(ValueError):
    """Raised when a strategy lifecycle transition is invalid."""

STATUSES = (
    "IDEA", "RESEARCH", "WALK_FORWARD", "HOLDOUT", "CANDIDATE",
    "PAPER", "PROMOTED", "REJECTED", "BLOCKED",
)
_TRANSITIONS = {
    "IDEA": {"RESEARCH", "REJECTED"},
    "RESEARCH": {"WALK_FORWARD", "REJECTED", "BLOCKED"},
    "WALK_FORWARD": {"HOLDOUT", "REJECTED", "BLOCKED"},
    "HOLDOUT": {"CANDIDATE", "REJECTED", "BLOCKED"},
    "CANDIDATE": {"PAPER", "REJECTED", "BLOCKED"},
    "PAPER": {"PROMOTED", "REJECTED", "BLOCKED"},
    "PROMOTED": set(),
    "REJECTED": set(),
    "BLOCKED": {"RESEARCH", "REJECTED"},
}

@dataclass(frozen=True)
class StrategyRecord:
    strategy_id: str
    family: str
    status: str = "IDEA"
    evidence_ids: tuple[str, ...] = ()
    inspirations: tuple[str, ...] = ()
    notes: str = ""
    paper_only: bool = True
    metadata: dict[str, str] = field(default_factory=dict)
    def __post_init__(self) -> None:
        if not self.strategy_id.strip() or not self.family.strip():
            raise LifecycleError("strategy_id and family must not be empty.")
        if self.status not in STATUSES:
            raise LifecycleError(f"Unknown status: {self.status}.")
        if not self.paper_only:
            raise LifecycleError("Strategy registry is paper-only.")

class StrategyRegistry:
    """In-memory registry; rejected/blocked records remain queryable."""
    def __init__(self, records: Iterable[StrategyRecord] = ()) -> None:
        self._records: dict[str, StrategyRecord] = {}
        for record in records:
            self.register(record)
    def register(self, record: StrategyRecord) -> None:
        if record.strategy_id in self._records:
            raise LifecycleError(f"Duplicate strategy_id: {record.strategy_id}.")
        self._records[record.strategy_id] = record
    def get(self, strategy_id: str) -> StrategyRecord:
        try:
            return self._records[strategy_id]
        except KeyError as exc:
            raise LifecycleError(f"Unknown strategy_id: {strategy_id}.") from exc
    def transition(self, strategy_id: str, new_status: str, *, note: str = "") -> StrategyRecord:
        current = self.get(strategy_id)
        if new_status not in STATUSES or (
            new_status != current.status and new_status not in _TRANSITIONS[current.status]
        ):
            raise LifecycleError(f"Invalid lifecycle transition {current.status} -> {new_status}.")
        if new_status == current.status:
            return current
        updated = StrategyRecord(
            current.strategy_id, current.family, new_status,
            current.evidence_ids, current.inspirations,
            note or current.notes, True, dict(current.metadata)
        )
        self._records[strategy_id] = updated
        return updated
    def all(self) -> tuple[StrategyRecord, ...]:
        return tuple(self._records.values())
    def graveyard(self) -> tuple[StrategyRecord, ...]:
        return tuple(r for r in self._records.values() if r.status in {"REJECTED", "BLOCKED"})
