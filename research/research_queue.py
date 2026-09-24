"""Deterministic research queue for autonomous, gated experimentation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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
    """Load the durable machine-readable queue used by autonomous orchestration."""
    path = Path(__file__).with_name("research_queue.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks = tuple(
        ResearchTask(
            task_id=item["task_id"],
            research_family=item["research_family"],
            hypothesis=item["hypothesis"],
            status=item.get("status", "PENDING"),
        )
        for item in payload["tasks"]
    )
    return ResearchQueue(tasks)
