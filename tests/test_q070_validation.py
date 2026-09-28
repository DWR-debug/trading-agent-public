from ast import parse
from pathlib import Path

def test_q070_performance_module_parses():
    parse(Path("automation/q070_performance.py").read_text(encoding="utf-8"))

def test_q070_current_workflows_are_self_hosted_and_git_free():
    for path in (
        ".github/workflows/q070-coverage-pit.yml",
        ".github/workflows/q070-evidence-reconcile.yml",
    ):
        text = Path(path).read_text(encoding="utf-8")
        assert "runs-on: [self-hosted, trading-agent-research]" in text
        assert "git add " not in text
        assert "git push " not in text
        assert "github_contents_publish.py" in text
    assert not Path(".github/workflows/q070-autonomous-advance.yml").exists()
    assert not Path(".github/workflows/q070-fixed-candidate-performance.yml").exists()

def test_q070_design_has_no_performance_selection():
    p=Path("research/preregistrations/q070_fixed_candidate_validation_2026_09_28.json").read_text(encoding="utf-8")
    assert '"status": "PREREGISTERED_DESIGN_ONLY"' in p
    assert '"performance_evaluation": false' in p
    assert '"selection_used": false' in p
    assert '"holdout_used_for_selection": false' in p
    assert '"automatic_promotion": false' in p


def test_q070_current_workflows_are_explicitly_dispatchable():
    for path in (
        ".github/workflows/q070-coverage-pit.yml",
        ".github/workflows/q070-evidence-reconcile.yml",
    ):
        text = Path(path).read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text


def test_q070_coverage_snapshot_identity_helper_is_available():
    from automation.q070_fresh_coverage import _coverage_snapshot_spec
    import json
    prereg=json.loads(Path("research/preregistrations/q070_performance_2026_09_28.json").read_text())
    scoped=_coverage_snapshot_spec(prereg)
    assert prereg["trial_id"]=="T-2026-09-28-070-PERFORMANCE"
    assert scoped["trial_id"]=="T-2026-09-28-070-COVERAGE"
    assert scoped["interval"]=="1d"
    assert scoped["raw_fetch_candles"]==5000
    assert scoped["target_common_count"]==3500


def test_q070_performance_uses_frozen_coverage_fingerprint_not_missing_result_fingerprint():
    text=Path("automation/q070_performance.py").read_text(encoding="utf-8")
    assert '"coverage_fingerprint":_fp(freeze)' in text
    assert 'coverage["result_fingerprint"]' not in text
    reconcile=Path("automation/q070_reconcile.py").read_text(encoding="utf-8")
    assert 'coverage_fingerprint' in reconcile

def test_q070_hosted_fallback_is_retired():
    assert not Path(".github/workflows/q070-hosted-fallback.yml").exists()
    auth = json.loads(
        Path("research/authorizations/q070_performance_2026_09_28.json").read_text(encoding="utf-8")
    )
    assert auth["authorized"] is False
    assert auth["execution_scope"] == "NONE" or auth.get("revoked") is True
