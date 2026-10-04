from pathlib import Path

def test_q182_probe_is_non_authorizing():
    text = Path("automation/q182_ferc_self_hosted_access_probe.py").read_text(encoding="utf-8")
    assert "Q182_ACCESS_PROBE_COMPLETED_NO_SCIENTIFIC_EVIDENCE" in text
    assert "RUNNER_ACCESS_BLOCKED" in text
    assert "AUTOMATIC_PROMOTION" in text
    assert "live_execution" in text

def test_q182_workflow_uses_both_verified_windows_lanes():
    text = Path(".github/workflows/q182-ferc-self-hosted-access-probe.yml").read_text(encoding="utf-8")
    assert "lane: [local_reproduction, data_qa]" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "Q182_ACCESS_PROBE_COMPLETED_NO_SCIENTIFIC_EVIDENCE" in text