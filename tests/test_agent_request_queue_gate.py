from pathlib import Path


def test_agent_queue_gate_does_not_run_unrelated_self_hosted_regressions():
    text = Path(".github/workflows/agent-request-queue.yml").read_text(encoding="utf-8")
    assert "python -m pytest -q tests/test_agent_dispatch.py" in text
    assert "tests/test_agent_dispatch.py tests/test_self_hosted_research_worker.py" not in text
