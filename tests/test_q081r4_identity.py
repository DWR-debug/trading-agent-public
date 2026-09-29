from __future__ import annotations

import ast
import json
from pathlib import Path

from automation import q081r4_ast_literal_audit_performance as runner

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research" / "preregistrations" / "q081r4_ast_literal_audit_2026_09_30.json"
SOURCE = ROOT / "automation" / "q081r4_ast_literal_audit_performance.py"


def test_q081r4_runner_identity_matches_preregistration() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert prereg["trial_id"] == "T-2026-09-30-081R4-PERFORMANCE"
    assert runner.TRIAL_ID == prereg["trial_id"]
    assert prereg["governance"]["performance_trial_authorized"] is False
    correction = prereg["correction"]
    assert correction["new_parameters"] is False
    assert correction["new_thresholds"] is False
    assert correction["asset_selection"] is False
    assert correction["direction_reversal"] is False
    assert correction["changed_data"] is False
    assert correction["changed_pit"] is False
    assert correction["changed_horizon"] is False
    assert correction["changed_variants"] is False
    assert correction["changed_costs"] is False
    assert correction["changed_execution_rules"] is False
    assert correction["predecessor_implementation_incident"] == "T-2026-09-30-081R3-PERFORMANCE"
    assert correction["predecessor_execution_run_id"] == "36640012014"


def test_q081r4_executable_ast_contains_no_json_style_literals() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    bad = sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id in {"true", "false", "null"}})
    assert bad == []


def test_q081r4_source_contract_is_dedicated() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    source_contract = prereg["source_contract"]
    assert "automation/q081r4_ast_literal_audit_performance.py" in source_contract
    assert "automation/q081r3_python_literal_fix_performance.py" not in source_contract
