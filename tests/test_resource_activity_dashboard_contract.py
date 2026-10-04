from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_resource_dashboard_workflow_is_read_only_and_hosted():
    text = (ROOT / '.github/workflows/resource-activity-dashboard.yml').read_text(encoding='utf-8')
    assert 'runs-on: ubuntu-24.04' in text
    assert 'actions: read' in text
    assert 'contents: read' in text
    assert '/actions/runners' in text
    assert '/actions/runs?status=queued' in text
    assert '/actions/runs?status=in_progress' in text
    assert 'GITHUB_STEP_SUMMARY' in text
    assert 'resource_dashboard.json' in text


def test_resource_dashboard_contains_safety_invariants():
    text = (ROOT / '.github/workflows/resource-activity-dashboard.yml').read_text(encoding='utf-8')
    for marker in ('PAPER_ONLY', 'LIVE_TRADING_ENABLED', 'ORDERS_ENABLED', 'AUTOMATIC_PROMOTION'):
        assert marker in text