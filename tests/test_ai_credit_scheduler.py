from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from automation.ai_credit_scheduler import (
    availability_for_provider,
    next_calendar_boundary,
    schedule_tasks,
)

ROOT = Path(__file__).resolve().parents[1]


def test_copilot_reset_is_exact_first_of_next_month_utc() -> None:
    policy = json.loads((ROOT / "research/governance/ai_provider_credit_policies_2026_10_04.json").read_text())
    now = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)
    result = availability_for_provider("copilot_free", now=now, policy=policy, observations={})
    assert result.confidence == "exact_policy"
    assert result.next_available_at == "2026-11-01T00:00:00Z"


def test_gemini_daily_reset_is_midnight_pacific() -> None:
    policy = json.loads((ROOT / "research/governance/ai_provider_credit_policies_2026_10_04.json").read_text())
    now = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)
    result = availability_for_provider("gemini_api", now=now, policy=policy, observations={})
    assert result.confidence == "exact_policy"
    assert result.next_available_at == "2026-10-05T00:00:00Z"


def test_openrouter_is_not_claimed_exact_when_daily_balance_unknown() -> None:
    policy = json.loads((ROOT / "research/governance/ai_provider_credit_policies_2026_10_04.json").read_text())
    now = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)
    result = availability_for_provider("openrouter_free", now=now, policy=policy, observations={})
    assert result.confidence == "unknown"
    assert result.eligible is True
    assert result.next_available_at is None


def test_openrouter_recent_429_gets_conservative_cooldown() -> None:
    policy = json.loads((ROOT / "research/governance/ai_provider_credit_policies_2026_10_04.json").read_text())
    now = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)
    obs = {
        "openrouter_free": [{
            "provider": "openrouter_free",
            "status": "RATE_LIMITED",
            "returncode": 429,
            "updated_at_utc": "2026-10-04T13:30:00Z",
        }]
    }
    result = availability_for_provider("openrouter_free", now=now, policy=policy, observations=obs)
    assert result.confidence == "conservative_estimate"
    assert result.eligible is False
    assert result.next_available_at == "2026-10-05T13:30:00Z"


def test_task_scheduler_uses_available_provider_and_never_authorizes_science() -> None:
    tasks = [{
        "task_id": "T1",
        "providers": ["openrouter_free", "gemini_api"],
        "information_value": 5,
        "estimated_cost_units": 1,
    }]
    result = schedule_tasks(
        tasks=tasks,
        now=datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc),
        provider_order=["openrouter_free", "gemini_api"],
        observations={},
    )
    assert result["task_assignments"][0]["status"] == "ADMITTED"
    assert result["task_assignments"][0]["provider"] == "gemini_api" or result["task_assignments"][0]["provider"] == "openrouter_free"
    assert result["policy_is_non_authorizing"] is True
    assert result["paid_usage_allowed"] is False
    assert result["scientific_evidence_created"] is False
