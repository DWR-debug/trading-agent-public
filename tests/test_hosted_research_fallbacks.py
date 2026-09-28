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

def test_hosted_q068_fallback_orders_authorization_before_performance():
    text=Path(".github/workflows/q068-hosted-fallback.yml").read_text()
    positions=[
        text.index("Build and publish one-shot authorization when missing"),
        text.index("Run exact frozen Q068 performance locally"),
        text.index("Validate exact Q068 performance result"),
        text.index("Publish Q068 performance evidence"),
        text.index("Reconcile Q068 ledger locally"),
        text.index("Publish Q068 ledger reconciliation"),
    ]
    assert positions == sorted(positions)

def test_hosted_q068_fallback_avoids_nested_heredoc():
    text=Path(".github/workflows/q068-hosted-fallback.yml").read_text()
    assert "if [ -f research/authorizations/q068_performance_2026_09_28.json ]; then" not in text
    assert "Prepare one-shot Q068 authorization" in text
    assert "Publish Q068 authorization when needed" in text

def test_hosted_q068_fallback_persists_frozen_snapshot():
    text=Path(".github/workflows/q068-hosted-fallback.yml").read_text()
    assert "Q068 FROZEN SNAPSHOT RECONSTRUCTED EXACTLY" in text
    assert "EVIDENCE: persist exact Q068 frozen snapshot" in text
    assert "datasets/ETR/1d.csv" in text
    assert "datasets/O/1d.csv" in text
