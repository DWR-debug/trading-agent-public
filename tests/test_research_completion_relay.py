from pathlib import Path
ROOT = Path(__file__).parents[1]

def test_research_completion_relay_contract():
    text = (ROOT / ".github/workflows/research-completion-relay.yml").read_text(encoding="utf-8")
    assert "workflow_call:" in text
    assert "workflow_dispatch: {}" in text
    assert "gh workflow run planned-capacity-fast-dispatch.yml" in text
    assert "actions: write" in text

def test_core_capacity_workflows_have_completion_relay():
    expected = {
        ".github/workflows/top4-candidate-slot-research.yml": "needs: [windows, ubuntu_x64, ubuntu_arm64]",
        ".github/workflows/ai-worker-fabric.yml": "needs: [plan_openrouter, worker, gemini_worker, mistral_worker]",
        ".github/workflows/q104-i19-13f-historical-identity-census.yml": "needs: [merge]",
    }
    for path, marker in expected.items():
        text = (ROOT / path).read_text(encoding="utf-8")
        assert text.count("completion_relay:") == 1
        assert "uses: ./.github/workflows/research-completion-relay.yml" in text
        assert marker in text


def test_research_completion_relay_wakes_capacity_dispatch_and_dashboard_refresh():
    text = (ROOT / ".github/workflows/research-completion-relay.yml").read_text(encoding="utf-8")
    assert "gh workflow run planned-capacity-fast-dispatch.yml" in text
    assert "gh workflow run resource-dashboard-update.yml" in text
    assert "DASHBOARD_REFRESH_RELAY=SUCCESS" in text
