from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def test_source_feasibility_script_is_discovery_only():
    text = (ROOT / "automation/q133_q145_source_feasibility.py").read_text(encoding="utf-8")
    assert "performance" in text
    assert "return evaluation" in text
    assert "holdout" in text
    assert "parameter_search" in text


def test_source_feasibility_workflow_is_hosted_and_safety_bound():
    text = (ROOT / ".github/workflows/deep-frontier-source-feasibility.yml").read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04" in text
    assert 'cron: "17 */12 * * *"' in text
    assert "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED" in text
    assert "automatic_promotion" in text


def test_q133_q145_candidate_count_is_stable():
    data = json.loads((ROOT / "research/frontier/q133_q145_candidate_wave_2026_10_03.json").read_text(encoding="utf-8"))
    assert len(data["candidates"]) == 13
    assert data["policy"]["performance_authorized"] is False
