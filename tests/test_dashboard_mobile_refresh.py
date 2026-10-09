from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_has_pixel_sized_responsive_layout_and_touch_targets():
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    assert 'name="viewport" content="width=device-width, initial-scale=1"' in html
    assert "min-height:44px" in html
    assert "@media(max-width:700px)" in html
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in html
    assert "overflow-x:auto" in html
    assert 'id="refreshStatus"' in html
    assert "Snapshot-Workflow öffnen" in html


def test_dashboard_polls_the_latest_published_snapshot_every_three_minutes():
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/resource-dashboard-update.yml").read_text(encoding="utf-8")
    assert "setInterval(function(){load(false);},180000)" in js
    assert 'cache:"no-store"' in js
    assert 'url.searchParams.set("ts",String(Date.now()))' in js
    assert "Browser-Abruf alle 3 Minuten" in js
    assert "planmäßig alle 5 Minuten" in js
    assert 'cron: "*/5 * * * *"' in workflow
    assert 'document.visibilityState==="visible"' in js


def test_refresh_button_does_not_claim_to_start_a_workflow():
    js = (ROOT / "docs/dashboard/dashboard.js").read_text(encoding="utf-8")
    html = (ROOT / "docs/dashboard/index.html").read_text(encoding="utf-8")
    assert "startet aber keinen neuen GitHub-Workflow" in js
    assert 'id="refresh" type="button"' in html

def test_dashboard_deploys_after_focus_gate_completion_and_state_receipts_change():
    workflow = (ROOT / ".github/workflows/resource-dashboard-update.yml").read_text(encoding="utf-8")
    assert "workflow_run:" in workflow
    assert '"Q104 I19 Historical 13F Identity Census"' in workflow
    assert '"Q104 I19 Historical PIT Compilation"' in workflow
    assert '"Q104 I19 Independent PIT Reproduction"' in workflow
    assert '"Top-4 Candidate Slot Research"' in workflow
    assert '"Q218 Independent Architecture PIT Reproduction"' in workflow
    assert '"research/evidence/current_operational_state.json"' in workflow
    assert '"docs/CURRENT_STATUS.md"' in workflow
    assert "github.event.workflow_run.head_branch == 'master'" in workflow
    assert "github.event.workflow_run.display_title" in workflow
