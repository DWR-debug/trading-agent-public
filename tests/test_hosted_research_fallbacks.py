from pathlib import Path

def test_hosted_q068_fallback_is_same_concurrency_group_and_frozen_only():
    text=Path(".github/workflows/q068-hosted-fallback.yml").read_text()
    assert "trading-agent-q068-auto-advance" in text
    assert "cancel-in-progress: true" in text
    assert "Q068_FIXED_RULE_PERFORMANCE_ONLY" in text
    assert "parameter selection" in text
    assert "live execution" in text
    assert "actions: write" in text

def test_hosted_q070_fallback_is_same_concurrency_group_and_frozen_only():
    text=Path(".github/workflows/q070-hosted-fallback.yml").read_text()
    assert "trading-agent-q070-coverage-pit" in text
    assert "cancel-in-progress: true" in text
    assert "Q070_FIXED_CANDIDATE_PERFORMANCE_ONLY" in text
    assert "parameter selection" in text
    assert "live execution" in text
    assert "actions: write" in text

def test_hosted_q068_fallback_has_idempotent_authorization_guard():
    text=Path(".github/workflows/q068-hosted-fallback.yml").read_text()
    assert "authorization already exists" in text
    assert "Q068 AUTHORIZATION REUSE OK" in text
    assert "Q068-PERFORMANCE-HOSTED-FALLBACK-2026-09-28" in text


def test_hosted_q070_fallback_freezes_asset_prerequisite_before_performance():
    text=Path(".github/workflows/q070-hosted-fallback.yml").read_text()
    assert "asset_freeze_fingerprint" in text
    assert "Q070-PERFORMANCE-HOSTED-FALLBACK-2026-09-28" in text
    assert "Q070 HOSTED PERFORMANCE RESULT OK" in text
