from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_top_three_dashboard_surfaces_gate_status_blocker_and_next_action():
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")

    assert 'var FOCUS=["Q104:I19","Q220","Q221"];' in js
    assert "Gate-Status" in js
    assert "Gate-Befund / Blocker" in js
    assert "Nächste sinnvolle Aktion" in js
    assert "x.current_milestone_status" in js
    assert "x.next_milestone_progress_basis" in js
    assert "x.next_gate" in js
    assert 'badge active-badge">Q104:I19' in html
    assert 'badge active-badge">Q220' in html
    assert 'badge active-badge">Q221' in html
    assert 'badge active-badge">Q218' not in html
    assert "Referenzansicht des Prospect-Portfolios." in html
    assert "Q221" in html


def test_dashboard_candidate_work_matching_ignores_identifier_punctuation():
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    assert 'replace(/[^A-Z0-9]/g,"")' in js
    assert 'var key=FOCUS[i].toUpperCase().replace(/[^A-Z0-9]/g,"")' in js


def test_top_three_queue_layout_has_responsive_breakpoints():
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    css = (ROOT / "docs/dashboard/research-control-board.css").read_text(encoding="utf-8")
    assert 'href="research-control-board.css"' in html
    assert ".queue-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}" in css
    assert ".queue-grid{grid-template-columns:repeat(2,minmax(0,1fr))}" in css
    assert ".queue-grid{grid-template-columns:1fr}" in css



def test_resource_dashboard_redeploys_when_q220_population_receipt_changes():
    workflow = (ROOT / ".github/workflows/resource-dashboard-update.yml").read_text(encoding="utf-8")
    push_block = workflow.split("  push:", 1)[1].split("  workflow_dispatch:", 1)[0]
    assert '"research/evidence/q220_as_filed_xbrl_population_latest.json"' in push_block



def test_dashboard_exposes_copyable_current_chat_handoff():
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    generator = (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")

    assert 'id="chatHandoffText"' in html
    assert 'id="copyHandoff"' in html
    assert 'id="copyHandoffStatus"' in html
    assert "data.chat_handoff" in js
    assert "next_research_focus" in js
    assert "navigator.clipboard.writeText(payload)" in js
    assert "field.select()" in js
    assert '"chat_handoff": chat_handoff_snapshot(evidence, os_state)' in generator
    assert "Active execution focus: " in js
    assert "PAPER_ONLY=" in js


def test_dashboard_uses_prioritized_research_control_board_layout():
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    css = (ROOT / "docs/dashboard/research-control-board.css").read_text(encoding="utf-8")
    assert 'href="research-control-board.css"' in html
    assert 'grid-template-areas:' in css
    assert '"focus focus focus focus focus focus focus focus focus focus focus focus"' in css
    assert css.index('"queue queue queue queue queue queue work work work work work work"') < css.index('"portfolio portfolio portfolio portfolio portfolio portfolio portfolio portfolio portfolio portfolio portfolio portfolio"')
    assert 'LIVE TRADING AUS' in html
    assert 'PAPER ONLY' in html
    assert 'grid-template-areas:"focus" "queue" "work" "capacity" "evidence" "milestones" "portfolio" "support" "handoff"' in css


def test_dashboard_top_three_remain_in_the_existing_candidate_focus_order():
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    assert 'var FOCUS=["Q104:I19","Q220","Q221"];' in js
    assert 'Q104:I19 · Q220 · Q221' in js


def test_active_top_three_decision_board_is_receipt_first():
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")

    assert 'var FOCUS=["Q104:I19","Q220","Q221"]' in js
    assert 'id="candidateDecisionRules"' in html
    assert html.index('id="candidateFocus"') < html.index('id="candidateDecisionRules"')
    assert html.index('id="candidateDecisionRules"') < html.index('class="progress-overview"')
    assert "function renderCandidateDecisionRules(pipeline)" in js
    for code in ("Q104:I19", "Q220", "Q221"):
        assert 'code:"' + code + '"' in js
    assert "DoD/USACE-90-Tage- und FAR-Ausnahmen" in js
    assert "Q218 ist aus aktivem Fokus und automatischem Dispatch entfernt" in js
    assert "Q219 bleibt pausiert" in js

def test_dashboard_uses_one_external_stylesheet_and_preserves_layout_rules():
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    css = (ROOT / "docs/dashboard/research-control-board.css").read_text(encoding="utf-8")

    assert "<style>" not in html
    assert 'href="research-control-board.css"' in html
    assert ".clock-grid" in css
    assert ".candidate-focus" in css
    assert "@media(max-width:700px)" in css
    assert "#focusSummary" not in css or ".focus-summary" in css
    assert css.index("/* Existing board-specific theme and component overrides. */") < css.index("/* Base layout rules moved from index.html; kept after the existing board stylesheet to preserve the original CSS cascade. */")
    assert css.index("/* Base layout rules moved from index.html; kept after the existing board stylesheet to preserve the original CSS cascade. */") < css.index(".refresh-status{")


def test_dashboard_refresh_does_not_reset_to_embedded_snapshot_or_overlap_requests():
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")

    assert "var refreshInFlight=false" in js
    assert "var hasRenderedSnapshot=false" in js
    assert "function snapshotKey(data)" in js
    assert "if(!hasRenderedSnapshot)hasRenderedSnapshot=renderEmbedded();" in js
    assert "if(!hasRenderedSnapshot||snapshotKey(data)!==lastRenderedSnapshotKey)render(data);" in js
    assert "var rendered=renderEmbedded();" not in js
    assert "setInterval(function(){load(false);},refreshIntervalMs)" in js
    assert 'document.visibilityState==="visible"' in js
    assert 'id="refreshStatus"' in (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    assert "startet keinen Workflow" in js


def test_dashboard_publishes_after_active_q104_q220_q221_gate_workflows():
    workflow = (ROOT / ".github/workflows/resource-dashboard-update.yml").read_text(encoding="utf-8")
    push_block = workflow.split("  push:", 1)[1].split("  workflow_dispatch:", 1)[0]

    assert "workflow_run:" in workflow
    assert 'branches: [master]' in workflow
    for name in (
        "Q104 I19 Historical 13F Identity Census",
        "Q104 I19 Historical PIT Compilation",
        "Q104 I19 Independent PIT Reproduction",
        "Q220 As-Filed SEC-XBRL Population Repair",
        "Q220 Historical Representation PIT Compiler",
        "Q220 Independent Historical PIT Reproduction",
        "Q220 TextBlock Differential Diagnostic",
        "Q221 Monthly Archive Inventory Probe",
        "Q221 Historical Award Public Boundary Falsification",
    ):
        assert f'"{name}"' in workflow
    assert "github.event.workflow_run.head_branch == 'master'" in workflow
    assert '"research/evidence/current_operational_state.json"' in push_block
    assert '"docs/CURRENT_STATUS.md"' in push_block
    assert '"research/evidence/trading_agent_chat_handoff.json"' in push_block


def test_dashboard_hides_queued_q104_census_retry_when_census_is_running(monkeypatch):
    from automation import generate_resource_dashboard as generator

    monkeypatch.setattr(generator, "jobs_for_run", lambda _run_id: [])
    monkeypatch.setattr(generator, "infer_lane", lambda *args: "FORMAL READINESS")
    monkeypatch.setattr(generator, "infer_resource", lambda *args: "Windows self-hosted A")

    name = "Q104 I19 Historical 13F Identity Census"
    rows = generator.current_work_from_runs([
        {"id": 100, "name": name, "status": "in_progress", "created_at": "2026-10-11T19:00:00Z", "event": "workflow_dispatch"},
        {"id": 101, "name": name, "status": "queued", "created_at": "2026-10-11T19:05:00Z", "event": "push"},
    ])

    assert {row["run_id"] for row in rows} == {100}


def test_dashboard_pending_run_without_job_records_has_no_unbound_job_reference(monkeypatch):
    from automation import generate_resource_dashboard as generator

    monkeypatch.setattr(generator, "jobs_for_run", lambda _run_id: [])
    monkeypatch.setattr(generator, "infer_lane", lambda *args: "FORMAL READINESS")
    monkeypatch.setattr(generator, "infer_resource", lambda *args: "GitHub-hosted Ubuntu x64")

    rows = generator.current_work_from_runs([
        {
            "id": 200,
            "name": "Q104 I19 Historical 13F Identity Census",
            "status": "queued",
            "created_at": "2026-10-11T20:00:00Z",
            "event": "workflow_dispatch",
        }
    ])

    assert len(rows) == 1
    assert rows[0]["run_id"] == 200
    assert rows[0]["job_status"] == "queued"
    assert rows[0]["job_started_at"] is None
    assert rows[0]["job_completed_at"] is None




def test_dashboard_decision_log_is_visible_current_and_non_authorizing():
    import json

    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    generator = (ROOT / "automation/generate_resource_dashboard.py").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/resource-dashboard-update.yml").read_text(encoding="utf-8")
    status_sync = (ROOT / "automation/sync_current_operational_status.py").read_text(encoding="utf-8")
    log_path = ROOT / "research/evidence/trading_agent_chat_decision_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8"))

    assert 'id="handoffPanel"' in html
    assert "data.handoff_decision_log" in js
    assert "safeHttpsUrl" in js
    assert '"handoff_decision_log": handoff_decision_log' in generator
    assert '"research/evidence/trading_agent_chat_decision_log.json"' in workflow
    assert log["record_type"] == "trading_agent_chat_decision_log"
    assert log["safety"] == {
        "PAPER_ONLY": True,
        "LIVE_TRADING_ENABLED": False,
        "ORDERS_ENABLED": False,
        "AUTOMATIC_PROMOTION": False,
        "paid_usage_usd": 0,
    }
    assert all(entry["scientific_evidence"] is False for entry in log["entries"])
    focus = next(entry for entry in log["entries"] if entry["candidate"] == "PORTFOLIO")
    assert all(code in focus["decision"] for code in ("Q104:I19", "Q220", "Q221"))
    assert "Q218" in focus["decision"] and "excluded" in focus["decision"].lower()

    # Dashboard continuity work must preserve the existing single-flight and receipt-driven guards.
    assert "status_priority" in generator
    assert "wait behind the active run" in generator
    assert "q220_population_focus_sentence" in status_sync
