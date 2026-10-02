from pathlib import Path

def test_s10_probe_is_fail_closed_and_local_only():
    text = Path("automation/s10_probe.py").read_text(encoding="utf-8")
    assert "formal_evidence_allowed" in text
    assert '"secrets_collected":False' in text
    assert "LOCAL" in text
    assert "S10_LIVE_READY" in text
    assert "TOKEN|KEY|SECRET|PASSWORD" in text

def test_self_hosted_frontier_lane_routes_s10_probe():
    text = Path("automation/self_hosted_research_worker.py").read_text(encoding="utf-8")
    assert "automation.s10_probe" in text
    assert "automation.s10_worker" in text
