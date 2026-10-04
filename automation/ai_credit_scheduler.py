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
    explicit = _latest_block(obs)
    if explicit and explicit > now:
        return Availability(
            provider,
            False,
            explicit.isoformat().replace("+00:00", "Z"),
            "exact_observed",
            "provider-specific quota block is active until an observed reset",
            "blocked",
        )

    if provider == "gemini_api":
        # Google's RPD reset is explicitly documented at midnight Pacific Time.
        reset = next_calendar_boundary(now, tz_name="America/Los_Angeles", rule="day")
        return Availability(
            provider,
            True,
            reset.isoformat().replace("+00:00", "Z"),
            "exact_policy",
            "daily quota reset boundary is documented; actual remaining quota still requires account telemetry",
            "policy_known_balance_unknown",
        )

    if provider == "copilot_free":
        reset = next_calendar_boundary(now, tz_name="UTC", rule="month")
        return Availability(
            provider,
            True,
            reset.isoformat().replace("+00:00", "Z"),
            "exact_policy",
            "included monthly AI-credit allowance resets at the start of the UTC calendar month",
            "reservation_limited",
        )

    if provider == "openrouter_free":
        if _recent_429(obs, now):
            # Provider docs publish the daily cap but not the exact wall-clock reset.
            # Conservatively wait 24h from the latest observed 429 rather than guess.
            latest = max(
                (
                    parse_dt(x.get("updated_at_utc") or x.get("finished_at_utc") or x.get("created_at_utc"))
                    for x in obs
                    if parse_dt(x.get("updated_at_utc") or x.get("finished_at_utc") or x.get("created_at_utc"))
                ),
                default=now,
            )
            reset = latest + timedelta(days=1)
            return Availability(
                provider,
                False,
                reset.isoformat().replace("+00:00", "Z"),
                "conservative_estimate",
                "daily free-model cap may be exhausted; exact daily reset wall-clock is not documented",
                "cooldown",
            )
        return Availability(
            provider,
            True,
            None,
            "unknown",
            "free route is available by policy, but current daily request balance is not observable from repository telemetry",
            "balance_unknown",
        )

    if provider == "mistral_api":
        if _recent_429(obs, now):
            latest = max(
                (
                    parse_dt(x.get("updated_at_utc") or x.get("finished_at_utc") or x.get("created_at_utc"))
                    for x in obs
                    if parse_dt(x.get("updated_at_utc") or x.get("finished_at_utc") or x.get("created_at_utc"))
                ),
                default=now,
            )
            reset = latest + timedelta(minutes=5)
            return Availability(
                provider,
                False,
                reset.isoformat().replace("+00:00", "Z"),
                "conservative_estimate",
                "recent provider rate-limit observed; exact limit dimension/reset not exposed in repository telemetry",
                "cooldown",
            )
        return Availability(
            provider,
            True,
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
            "explicit_error_only",
            "local Gemini account quota is admitted only when an explicit free-only preflight passes; reset time comes from provider error/observation",
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
