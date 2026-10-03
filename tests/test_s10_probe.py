from pathlib import Path

def test_s10_probe_is_fail_closed_and_local_only():
    text = Path("automation/s10_probe.py").read_text(encoding="utf-8")
    assert "formal_evidence_allowed" in text
    assert '"secrets_collected":False' in text
    assert "LOCAL" in text
    assert "S10_LIVE_READY" in text
    assert "TOKEN|KEY|SECRET|PASSWORD" in text

def test_self_hosted_frontier_lane_does_not_duplicate_s10_route():
    text = Path("automation/self_hosted_research_worker.py").read_text(encoding="utf-8")
    assert "automation.s10_probe" not in text
    assert "automation.s10_worker" not in text


def test_s10_phone_workflow_owns_phone_side_execution():
    text = Path(".github/workflows/s10-phone-worker.yml").read_text(encoding="utf-8")
    assert "runs-on: [self-hosted, s10-phone, linux, ARM64]" in text
    assert "automation/s10_worker.py" in text
    assert "automation/s10_runtime.py" in text
