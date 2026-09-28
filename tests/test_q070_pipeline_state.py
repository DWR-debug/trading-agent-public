from pathlib import Path
import json

from automation.q070_pipeline_state import summarize

def test_q070_starts_design_frozen_without_materialized_performance_prereg(tmp_path):
    root = tmp_path
    (root/"research/preregistrations").mkdir(parents=True)
    (root/"research/evidence").mkdir(parents=True)
    (root/"research/preregistrations/q070_fixed_candidate_validation_2026_09_28.json").write_text(
        json.dumps({
            "status":"PREREGISTERED_DESIGN_ONLY",
            "source_candidate_bank":{"definitions_locked":True},
        }),
        encoding="utf-8",
    )
    (root/"research/evidence/trial_ledger.json").write_text('{"trials":[]}',encoding="utf-8")
    out=summarize(root)
    assert out["family"]=="Q070"
    assert out["state"]=="PREFLIGHT_BLOCKED"
    assert "Q070 performance preregistration not materialized by coverage" in out["blocking_reasons"]

def test_q070_status_module_is_fail_closed():
    text = Path("automation/q070_pipeline_state.py").read_text(encoding="utf-8")
    assert "and not blockers" in text
    assert "PERFORMANCE_EVIDENCE_INVALID" in text
