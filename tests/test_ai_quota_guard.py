from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from automation.ai_quota_guard import load_block, parse_reset_seconds, quota_error, record_block


def test_parse_reset_interval() -> None:
    assert parse_reset_seconds("Individual quota reached. Resets in 147h46m42s.") == 147 * 3600 + 46 * 60 + 42
    assert parse_reset_seconds("Resets in 12m05s") == 725
    assert parse_reset_seconds("no reset information") is None


def test_quota_error_detection() -> None:
    assert quota_error(3, "", "RESOURCE_EXHAUSTED")
    assert quota_error(429, "", "")
    assert quota_error(1, "", "HTTP 429")
    assert not quota_error(1, "", "ordinary provider failure")


def test_quota_block_round_trip_and_expiry(tmp_path) -> None:
    env = {"TRADING_AGENT_AI_QUOTA_CACHE": str(tmp_path / "quota.json")}
    block = record_block("gemini_cli", 3600, raw_error="RESOURCE_EXHAUSTED", env=env)
    loaded = load_block("gemini_cli", env)
    assert loaded is not None
    assert loaded["provider"] == "gemini_cli"
    assert loaded["reset_seconds"] == 3600

    expired = dict(block)
    expired["blocked_until_utc"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    (tmp_path / "quota.json").write_text(json.dumps(expired), encoding="utf-8")
    assert load_block("gemini_cli", env) is None
