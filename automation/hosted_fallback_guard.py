"""Determine whether the self-hosted research service is stale enough to trigger hosted failover."""

from __future__ import annotations

from datetime import datetime, timezone

SUCCESS_FRESH_SECONDS = 45 * 60
PENDING_MAX_SECONDS = 25 * 60


def _parse_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def decide_fallback(runs: list[dict], *, now: datetime) -> dict[str, object]:
    """Return no automatic fallback because self-hosted capacity is an orchestration assumption.

    Historical heartbeat data are retained only for diagnostics; they must not route
    work away from the two permanently available Windows slots.
    """
    now = now.astimezone(timezone.utc)
    relevant = [r for r in runs if isinstance(r, dict) and r.get("created_at")]
    relevant.sort(key=lambda r: str(r.get("created_at")), reverse=True)
    latest = relevant[0] if relevant else {}
    return {
        "run_fallback": False,
        "reason": "SELF_HOSTED_ASSUMED_ALWAYS_AVAILABLE",
        "age_seconds": None,
        "latest_status": latest.get("status"),
        "latest_conclusion": latest.get("conclusion"),
        "latest_run_id": latest.get("id"),
        "availability_policy": "ASSUMED_ALWAYS_AVAILABLE",
        "diagnostic_runs_seen": len(relevant),
    }
