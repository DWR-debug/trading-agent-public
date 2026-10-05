"""Contract tests for the third Windows capacity/independent-QA pulse."""
from pathlib import Path


def test_windows_capacity_pulse_is_bounded_and_non_formal() -> None:
    text = Path(".github/workflows/windows-independent-capacity-pulse.yml").read_text(encoding="utf-8")
    assert 'cron: "*/20 * * * *"' in text
    assert "runs-on: [self-hosted, trading-agent-long]" in text
    assert "trading-agent-windows-research-capacity-v1" in text
    assert "cancel-in-progress: true" in text
    assert "timeout-minutes: 20" in text
    assert "formal_evidence_allowed':False" in text
    assert "independent_reproduction_only':True" in text
    assert "PAPER_ONLY':True" in text
    assert "LIVE_TRADING_ENABLED':False" in text
    assert "ORDERS_ENABLED':False" in text
    assert "AUTOMATIC_PROMOTION':False" in text


def test_windows_capacity_pulse_rotates_fixed_packs() -> None:
    text = Path(".github/workflows/windows-independent-capacity-pulse.yml").read_text(encoding="utf-8")
    assert "set /a PACK=GITHUB_RUN_NUMBER %% 4" in text
    assert "tests/test_research_governance_audit.py" in text
    assert "tests/test_q187_q192_source_feasibility.py" in text
    assert "tests/test_q197_q198_source_feasibility.py" in text
    assert "tests/test_q199_q201_source_feasibility.py" in text
