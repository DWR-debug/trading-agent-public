from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_CACHE = Path.home() / ".trading-agent" / "ai_quota_block.json"
_RESET_RE = re.compile(
    r"resets\s+in\s+(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?(?:(?P<s>\d+)s)?",
    re.IGNORECASE,
)


def cache_path(env: dict[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    return Path(env.get("TRADING_AGENT_AI_QUOTA_CACHE", str(DEFAULT_CACHE))).expanduser()


def parse_reset_seconds(text: str) -> int | None:
    match = _RESET_RE.search(text or "")
    if not match:
        return None
    h = int(match.group("h") or 0)
    m = int(match.group("m") or 0)
    s = int(match.group("s") or 0)
    total = h * 3600 + m * 60 + s
    return total if total > 0 else None


def quota_error(returncode: int | None, stdout: str = "", stderr: str = "") -> bool:
    joined = f"{stdout}\n{stderr}".lower()
    return (
        returncode in {429, 3}
        or "resource_exhausted" in joined
        or "individual quota reached" in joined
        or "http 429" in joined
        or "code 429" in joined
    )


def load_block(provider: str, env: dict[str, str] | None = None) -> dict[str, Any] | None:
    path = cache_path(env)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if data.get("provider") != provider:
        return None
    blocked_until = data.get("blocked_until_utc")
    if not isinstance(blocked_until, str):
        return None
    try:
        expiry = datetime.fromisoformat(blocked_until.replace("Z", "+00:00"))
    except ValueError:
        return None
    now = datetime.now(timezone.utc)
    if expiry <= now:
        try:
            path.unlink()
        except OSError:
            pass
        return None
    return {**data, "remaining_seconds": int((expiry - now).total_seconds())}


def record_block(
    provider: str,
    reset_seconds: int,
    *,
    raw_error: str = "",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    if reset_seconds <= 0:
        reset_seconds = 3600
    now = datetime.now(timezone.utc)
    blocked_until = now + timedelta(seconds=reset_seconds)
    path = cache_path(env)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "provider": provider,
        "blocked_at_utc": now.isoformat().replace("+00:00", "Z"),
        "blocked_until_utc": blocked_until.isoformat().replace("+00:00", "Z"),
        "reset_seconds": int(reset_seconds),
        "reason": "RESOURCE_EXHAUSTED",
        "raw_error": raw_error[-4000:],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data
