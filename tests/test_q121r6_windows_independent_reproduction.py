"""Contract tests for the Permanent-PC Q121-R6 independent reproduction workflow."""
from pathlib import Path


def test_q121r6_windows_independent_reproduction_contract() -> None:
    text = Path(".github/workflows/q121r6-windows-independent-reproduction.yml").read_text(encoding="utf-8")
    assert "workflow_run:" in text
    assert "Q121-R6 SEC Acceptance-Time Compilation" in text
    assert "self-hosted" in text
    assert "max-parallel: 2" in text
    assert "--shard-count 2" in text
    assert "--workers 8" in text
    assert "--request-gap-seconds 0.25" in text
    assert "timeout-minutes: 240" in text
    assert "independent_reproduction_only':True" in text
    assert "formal_evidence_allowed':False" in text
    assert "trading-agent-windows-research-capacity-v1" in text
    assert "cancel-in-progress: true" in text
