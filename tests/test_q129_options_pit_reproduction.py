from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_q129_independent_reproduction_is_fail_closed():
    text = (ROOT / "automation/q129_options_pit_reproduction.py").read_text(encoding="utf-8")
    assert "duckdb" in text
    assert "exchange_calendars" in text
    assert "logic_is_distinct_from_source_feasibility_verifier" in text
    assert "same_day_decision_use_allowed" in text
    assert "live_execution" in text


def test_q129_independent_workflow_is_hosted_and_boundary_safe():
    text = (ROOT / ".github/workflows/q129-independent-pit-reproduction.yml").read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04" in text
    assert "Q129_INDEPENDENT_PIT_REPRODUCED" in text
    assert "performance: false" in text
    assert "automatic_promotion" in text
