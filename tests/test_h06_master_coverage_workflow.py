from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_h06_master_workflow_is_scheduled_and_coverage_only():
    text = (ROOT / ".github" / "workflows" / "h06-master-coverage-repair.yml").read_text(encoding="utf-8")
    assert 'cron: "27 */6 * * *"' in text
    assert "workflow_dispatch:" in text
    assert "runs-on: ubuntu-24.04-arm" in text
    assert "automation/wide_search_h06_sector_neutral_residual_momentum_repair_coverage.py" in text
    assert "pytest -q tests/test_wide_search_h06_sector_neutral_residual_momentum_repair_coverage.py" in text
    assert "performance_trial_authorized" not in text
    assert "automatic_promotion" not in text
    assert "holdout" not in text.lower()
