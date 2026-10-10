from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_top_three_dashboard_surfaces_gate_status_blocker_and_next_action():
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")

    assert 'var FOCUS=["Q104:I19","Q220","Q218"];' in js
    assert "Gate-Status" in js
    assert "Gate-Befund / Blocker" in js
    assert "Nächste sinnvolle Aktion" in js
    assert "x.current_milestone_status" in js
    assert "x.next_milestone_progress_basis" in js
    assert "x.next_gate" in js
    assert 'id="handoffPanel"' in html
    assert '"handoff_decision_log": handoff_decision_log' in (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    assert "data.chat_handoff" in js
    assert "data.handoff_decision_log" in js
    assert "Letzte wichtige Entscheidungen und Sicherungspunkte" in js
    assert 'badge active-badge">Q104:I19' in html
    assert 'badge active-badge">Q220' in html
    assert 'badge active-badge">Q218' in html
    assert "Referenzansicht des Prospect-Portfolios." in html


def test_dashboard_candidate_work_matching_ignores_identifier_punctuation():
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    assert 'replace(/[^A-Z0-9]/g,"")' in js
    assert 'var key=FOCUS[i].toUpperCase().replace(/[^A-Z0-9]/g,"")' in js


def test_top_three_queue_layout_has_responsive_breakpoints():
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    assert ".queue-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}" in html
    assert ".queue-grid{grid-template-columns:repeat(2,minmax(0,1fr))}" in html
    assert ".queue-grid{grid-template-columns:1fr}" in html



def test_resource_dashboard_redeploys_when_q220_population_receipt_changes():
    workflow = (ROOT / ".github/workflows/resource-dashboard-update.yml").read_text(encoding="utf-8")
    push_block = workflow.split("  push:", 1)[1].split("  workflow_dispatch:", 1)[0]
    assert '"research/evidence/q220_as_filed_xbrl_population_latest.json"' in push_block
