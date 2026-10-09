from pathlib import Path

WORKFLOW = Path(".github/workflows/top4-candidate-slot-research.yml").read_text(encoding="utf-8")


def _job(name: str, next_name: str) -> str:
    start = WORKFLOW.index(f"  {name}:\n")
    end = WORKFLOW.index(f"  {next_name}:\n", start)
    return WORKFLOW[start:end]


def test_focused_q218_gates_are_routable_on_both_hosted_architectures():
    for name, next_name in (("ubuntu_x64", "ubuntu_arm64"), ("ubuntu_arm64", "completion_relay")):
        block = _job(name, next_name)
        assert "automation.q218_sec_multichannel_source_gate" in block
        assert "automation.q218_sec_event_pair_lineage_gate" in block
        assert "tests/test_q218_sec_multichannel_source_gate.py" in block
        assert "tests/test_q218_sec_event_pair_lineage_gate.py" in block
        assert "Q218_COMPLETED_FOCUS_GATE_NOOP=$skip" in block
        assert "inputs.candidate == 'Q218' && inputs.focus_wave" in block


def test_focused_q218_receipt_is_published_after_the_job_artifact_exists():
    for name, next_name in (("windows", "ubuntu_x64"), ("ubuntu_x64", "ubuntu_arm64"), ("ubuntu_arm64", "completion_relay")):
        block = _job(name, next_name)
        assert "automation/q218_publish_focus_gate_receipt.py" in block
        assert block.index("actions/upload-artifact@v6") < block.index("automation/q218_publish_focus_gate_receipt.py")


def test_focused_q218_dispatch_remains_non_performance_only():
    for name, next_name in (("ubuntu_x64", "ubuntu_arm64"), ("ubuntu_arm64", "completion_relay")):
        block = _job(name, next_name)
        assert "automation.q218_independent_replication" not in block
        assert "SLOT_RESEARCH_BOUNDARY=PAPER_ONLY_NO_PERFORMANCE_NO_HOLDOUT_NO_RANKING_NO_TUNING_NO_PROMOTION_NO_LIVE_EXECUTION" in block
