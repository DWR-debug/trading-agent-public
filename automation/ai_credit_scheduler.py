"""Deterministic AI credit/availability scheduler.

This module never calls an AI provider. It combines provider policy, observed
worker/quota events, and task cost/value metadata to compute when a free route
is safely admissible. Exact reset times are emitted only when the policy or a
provider response proves them; otherwise the result is explicitly estimated
or unknown.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "research/governance/ai_provider_credit_policies_2026_10_04.json"
DEFAULT_STATE_GLOB = "ops/ai_worker_state/*.json"


@dataclass(frozen=True)
class Availability:
    provider: str
    eligible: bool
    next_available_at: str | None
    next_reset_at: str | None
    confidence: str
    reason: str
    reserve_status: str


def parse_dt(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.astimezone(timezone.utc)


def next_calendar_boundary(now: datetime, *, tz_name: str, rule: str) -> datetime:
    zone = ZoneInfo(tz_name)
    local = now.astimezone(zone)
    if rule == "day":
        next_local = (local + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif rule == "month":
        year = local.year + (1 if local.month == 12 else 0)
        month = 1 if local.month == 12 else local.month + 1
        next_local = local.replace(
            year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0
        )
    else:
        raise ValueError(f"Unsupported calendar boundary: {rule}")
    return next_local.astimezone(timezone.utc)


def load_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def load_observations(root: Path = ROOT) -> dict[str, list[dict[str, Any]]]:
    observations: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(root.glob(DEFAULT_STATE_GLOB)):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        provider = data.get("provider")
        if isinstance(provider, str) and provider:
            observations.setdefault(provider, []).append(data)
    return observations


def _latest_block(observations: list[dict[str, Any]]) -> datetime | None:
    candidates: list[datetime] = []
    for item in observations:
        block = item.get("quota_block")
        if isinstance(block, dict):
            dt = parse_dt(block.get("blocked_until_utc"))
            if dt:
                candidates.append(dt)
        preflight = item.get("preflight")
        if isinstance(preflight, dict):
            block2 = preflight.get("quota_block")
            if isinstance(block2, dict):
                dt = parse_dt(block2.get("blocked_until_utc"))
                if dt:
                    candidates.append(dt)
    return max(candidates) if candidates else None


def load_copilot_state(root: Path = ROOT) -> dict[str, Any]:
    path = root / "ops/copilot_free_budget_state.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _recent_429(observations: list[dict[str, Any]], now: datetime) -> bool:
    for item in observations:
        status = item.get("status")
        if status == "RATE_LIMITED" or item.get("returncode") == 429:
            updated = parse_dt(item.get("updated_at_utc") or item.get("finished_at_utc") or item.get("created_at_utc"))
            if updated is None or now - updated <= timedelta(hours=24):
                return True
    return False


def availability_for_provider(
    provider: str,
    *,
    now: datetime,
    policy: dict[str, Any],
    observations: dict[str, list[dict[str, Any]]],
) -> Availability:
    spec = policy["providers"][provider]
    obs = observations.get(provider, [])

    if provider == "copilot_free":
        state = load_copilot_state()
        reserved = int(state.get("reserved_sessions", 0) or 0)
        max_reserved = int(state.get("max_reserved_sessions", 4) or 4)
        if reserved >= max_reserved:
            reset = next_calendar_boundary(now, tz_name="UTC", rule="month")
            return Availability(
                provider,
                False,
                reset.isoformat().replace("+00:00", "Z"),
                reset.isoformat().replace("+00:00", "Z"),
                "exact_policy",
                "protected project Copilot reservation is exhausted",
                "reservation_exhausted",
            )

    explicit = _latest_block(obs)
    if explicit and explicit > now:
        return Availability(
            provider,
            False,
            explicit.isoformat().replace("+00:00", "Z"),
            explicit.isoformat().replace("+00:00", "Z"),
            "exact_observed",
            "provider-specific quota block is active until an observed reset",
            "blocked",
        )

    if provider == "gemini_api":
        reset = next_calendar_boundary(now, tz_name="America/Los_Angeles", rule="day")
        return Availability(
            provider,
            True,
            None,
            reset.isoformat().replace("+00:00", "Z"),
            "exact_policy",
            "Gemini daily quota reset boundary is documented at midnight Pacific Time; remaining balance is not available in repository telemetry",
            "balance_unknown",
        )

    if provider == "copilot_free":
        reset = next_calendar_boundary(now, tz_name="UTC", rule="month")
        return Availability(
            provider,
            True,
            None,
            reset.isoformat().replace("+00:00", "Z"),
            "exact_policy",
            "protected Copilot reservation budget has capacity",
            "reservation_available",
        )

    if provider == "openrouter_free":
        if _recent_429(obs, now):
            latest_candidates = [
                parse_dt(x.get("updated_at_utc") or x.get("finished_at_utc") or x.get("created_at_utc"))
                for x in obs
            ]
            latest = max((x for x in latest_candidates if x is not None), default=now)
            reset = latest + timedelta(days=1)
            return Availability(
                provider,
                False,
                reset.isoformat().replace("+00:00", "Z"),
                None,
                "conservative_estimate",
                "recent 429 observed; OpenRouter publishes the daily cap but does not document the exact daily wall-clock reset",
                "cooldown",
            )
        return Availability(
            provider,
            True,
            None,
            None,
            "unknown",
            "OpenRouter free route is policy-allowed, but remaining daily requests are not exposed in repository telemetry; live preflight is the final gate",
            "balance_unknown",
        )

    if provider == "mistral_api":
        if _recent_429(obs, now):
            latest_candidates = [
                parse_dt(x.get("updated_at_utc") or x.get("finished_at_utc") or x.get("created_at_utc"))
                for x in obs
            ]
            latest = max((x for x in latest_candidates if x is not None), default=now)
            reset = latest + timedelta(minutes=5)
            return Availability(
                provider,
                False,
                reset.isoformat().replace("+00:00", "Z"),
                None,
                "conservative_estimate",
                "recent 429 observed; Mistral exposes rate-limit dimensions but account-specific free monthly reset is not available in repository telemetry",
                "cooldown",
            )
        return Availability(
            provider,
            True,
            None,
            None,
            "unknown",
            "Mistral free monthly usage exists but account-specific remaining balance/reset boundary is not exposed in repository telemetry",
            "balance_unknown",
        )

    if provider == "gemini_cli":
        return Availability(
            provider,
            True,
            None,
            None,
            "explicit_error_only",
            "local Gemini account quota is admitted only when explicit free-only preflight passes; reset time comes from provider error/observation",
            "preflight_required",
        )

    raise KeyError(provider)

def task_cost(task: dict[str, Any]) -> float:
    value = task.get("estimated_cost_units", 1.0)
    return float(value) if isinstance(value, (int, float)) and value > 0 else 1.0


def task_priority(task: dict[str, Any]) -> float:
    benefit = task.get("information_value", 1.0)
    cost = task_cost(task)
    risk = task.get("duplication_penalty", 0.0)
    return (float(benefit) - float(risk)) / cost


def schedule_tasks(
    *,
    tasks: list[dict[str, Any]],
    now: datetime,
    provider_order: list[str] | None = None,
    policy: dict[str, Any] | None = None,
    observations: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    policy = policy or load_policy()
    observations = observations or load_observations()
    providers = provider_order or list(policy["providers"])
    avail = {
        provider: availability_for_provider(
            provider, now=now, policy=policy, observations=observations
        )
        for provider in providers
    }

    ranked_tasks = sorted(tasks, key=lambda x: (-task_priority(x), str(x.get("task_id", ""))))
    assignments: list[dict[str, Any]] = []
    for task in ranked_tasks:
        compatible = [p for p in providers if p in task.get("providers", []) and avail[p].eligible]
        if not compatible:
            assignments.append(
                {
                    "task_id": task.get("task_id"),
                    "status": "DEFERRED_NO_FREE_PROVIDER",
                    "next_check_at": min(
                        (
                            parse_dt(avail[p].next_available_at)
                            for p in providers
                            if avail[p].next_available_at
                        ),
                        default=None,
                    ).isoformat().replace("+00:00", "Z")
                    if any(avail[p].next_available_at for p in providers)
                    else None,
                }
            )
            continue
        chosen = sorted(
            compatible,
            key=lambda p: (
                parse_dt(avail[p].next_available_at) or datetime.min.replace(tzinfo=timezone.utc),
                p,
            ),
        )[0]
        assignments.append(
            {
                "task_id": task.get("task_id"),
                "status": "ADMITTED",
                "provider": chosen,
                "provider_confidence": avail[chosen].confidence,
                "reason": avail[chosen].reason,
            }
        )

    return {
        "schema_version": 1,
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "provider_availability": {
            k: {
                "eligible": v.eligible,
                "next_available_at": v.next_available_at,
                "next_reset_at": v.next_reset_at,
                "confidence": v.confidence,
                "reason": v.reason,
                "reserve_status": v.reserve_status,
            }
            for k, v in avail.items()
        },
        "task_assignments": assignments,
        "policy_is_non_authorizing": True,
        "paid_usage_allowed": False,
        "scientific_evidence_created": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
    if not isinstance(tasks, list):
        raise SystemExit("--tasks must be a JSON list")
    result = schedule_tasks(tasks=tasks, now=datetime.now(timezone.utc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
