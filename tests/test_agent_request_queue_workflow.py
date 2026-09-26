from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_agent_queue_pauses_cleanly_without_copilot_token():
    workflow = (ROOT / ".github" / "workflows" / "agent-request-queue.yml").read_text(encoding="utf-8")
    assert "id: copilot_token" in workflow
    assert 'echo "configured=false" >> "$GITHUB_OUTPUT"' in workflow
    assert "exit 0" in workflow
    assert "No Copilot session or paid usage is claimed" in workflow


def test_agent_queue_runs_copilot_only_after_token_gate():
    workflow = (ROOT / ".github" / "workflows" / "agent-request-queue.yml").read_text(encoding="utf-8")
    for step in (
        "Run bounded Copilot CLI",
        "Enforce task-scoped file scope",
        "Final bounded regression gate",
        "Commit and publish",
    ):
        start = workflow.index("      - name: " + step)
        next_marker = workflow.find("\n      - name:", start + 1)
        section = workflow[start:] if next_marker < 0 else workflow[start:next_marker]
        assert "steps.copilot_token.outputs.configured == 'true'" in section
