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
    now = now.astimezone(timezone.utc)
    relevant = [r for r in runs if isinstance(r, dict) and r.get("created_at")]
    relevant.sort(key=lambda r: str(r.get("created_at")), reverse=True)

    if not relevant:
        return {
            "run_fallback": True,
            "reason": "NO_SELF_HOSTED_HEARTBEAT",
            "age_seconds": None,
            "latest_status": None,
            "latest_conclusion": None,
        }

    latest = relevant[0]
    created = _parse_time(str(latest["created_at"]))
    age = max(0, int((now - created).total_seconds()))
    status = str(latest.get("status") or "")
    conclusion = latest.get("conclusion")

    if status in {"queued", "pending", "in_progress"}:
        run_fallback = age >= PENDING_MAX_SECONDS
        reason = "SELF_HOSTED_RUN_STALE_PENDING" if run_fallback else "SELF_HOSTED_RUN_ACTIVE"
    elif status == "completed":
        run_fallback = age > SUCCESS_FRESH_SECONDS
        reason = "SELF_HOSTED_HEARTBEAT_STALE" if run_fallback else ("SELF_HOSTED_HEARTBEAT_FRESH" if conclusion == "success" else "SELF_HOSTED_RECENT_NON_SUCCESS")
    else:
        run_fallback = age > SUCCESS_FRESH_SECONDS
        reason = "SELF_HOSTED_STATUS_STALE"

    return {
        "run_fallback": run_fallback,
        "reason": reason,
        "age_seconds": age,
        "latest_status": status,
        "latest_conclusion": conclusion,
        "latest_run_id": latest.get("id"),
    }