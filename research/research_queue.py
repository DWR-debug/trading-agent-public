"""Deterministic research queue for autonomous, gated experimentation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class ResearchQueueError(ValueError):
    """Raised when the research queue contract is violated."""


STATUSES = ("PENDING", "RUNNING", "COMPLETED", "REJECTED", "BLOCKED")


@dataclass(frozen=True)
class ResearchTask:
    task_id: str
    research_family: str
    hypothesis: str
    status: str = "PENDING"

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.research_family.strip():
            raise ResearchQueueError("task_id and research_family are required.")
        if self.status not in STATUSES:
            raise ResearchQueueError(f"Unknown queue status: {self.status}.")


class ResearchQueue:
    """Small fail-closed queue with deterministic ordering and no execution rights."""

    def __init__(self, tasks: Iterable[ResearchTask]) -> None:
        self._tasks = list(tasks)
        ids = [task.task_id for task in self._tasks]
        if len(ids) != len(set(ids)):
            raise ResearchQueueError("task_id values must be unique.")

    def pending(self) -> tuple[ResearchTask, ...]:
        return tuple(task for task in self._tasks if task.status == "PENDING")

    def next_task(self) -> ResearchTask | None:
        return next(iter(self.pending()), None)

    def set_status(self, task_id: str, status: str) -> ResearchTask:
        if status not in STATUSES:
            raise ResearchQueueError(f"Unknown queue status: {status}.")
        for index, task in enumerate(self._tasks):
            if task.task_id == task_id:
                current = task
                if status == current.status:
                    return current
                allowed = {
                    "PENDING": {"RUNNING", "REJECTED", "BLOCKED"},
                    "RUNNING": {"COMPLETED", "REJECTED", "BLOCKED"},
                    "COMPLETED": set(),
                    "REJECTED": set(),
                    "BLOCKED": {"PENDING", "REJECTED"},
                }
                if status not in allowed[current.status]:
                    raise ResearchQueueError(
                        f"Invalid transition {current.status} -> {status}."
                    )
                updated = ResearchTask(
                    current.task_id,
                    current.research_family,
                    current.hypothesis,
                    status,
                )
                self._tasks[index] = updated
                return updated
        raise ResearchQueueError(f"Unknown task_id: {task_id}.")

    def all(self) -> tuple[ResearchTask, ...]:
        return tuple(self._tasks)


def default_research_queue() -> ResearchQueue:
    return ResearchQueue(
        (
            ResearchTask(
                "Q-001-TRIAL-017",
                "event_intelligence",
                "Political/geopolitical event flow can improve point-in-time market-impact classification.",
            ),
            ResearchTask(
                "Q-002-ADVERSARIAL",
                "research_governance",
                "Fragile apparent alpha should degrade under latency, cost and perturbation stress.",
            ),
            ResearchTask(
                "Q-003-PORTFOLIO-RISK",
                "portfolio_risk",
                "Cross-strategy correlation, concentration and joint losses can improve exposure controls.",
            ),
            ResearchTask(
                "Q-004-CHAMPION-CHALLENGER",
                "research_governance",
                "A frozen evidence contract can prevent promotion based only on peak backtest results.",
            ),
            ResearchTask(
                "Q-005-VOLATILITY",
                "volatility",
                "Volatility-regime information may provide an orthogonal, cost-aware signal or risk overlay.",
            ),
            ResearchTask(
                "Q-006-RELATIVE-VALUE",
                "relative_value",
                "Stable cross-asset relationships may add diversification without relying on trend persistence.",
            ),
        )
    )
