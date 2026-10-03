from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_h06_r1_authorization_is_explicit_dispatch_only():
    text=(ROOT/".github/workflows/h06-p2-r1-performance-authorization-once.yml").read_text(encoding="utf-8")
    assert "  workflow_dispatch:" in text
    assert "  push:" not in text.split("permissions:",1)[0]
    assert "github.event_name == 'push'" not in text

def test_post_pass_replication_trigger_excludes_design_registry_changes():
    text=(ROOT/".github/workflows/post-pass-independent-replication.yml").read_text(encoding="utf-8")
    assert 'research/evidence/*performance_result.json' in text
    assert 'research/authorizations/**' in text
    assert 'research/governance/active_research_registry.json' not in text.split("workflow_dispatch:",1)[0]
    assert 'research/preregistrations/**' not in text.split("workflow_dispatch:",1)[0]
    assert "authorization_presence" in text

def test_post_pass_noop_when_no_authorized_entry():
    text=(ROOT/".github/workflows/post-pass-independent-replication.yml").read_text(encoding="utf-8")
    assert "No authorized performance entry; post-pass replication dispatch is a no-op." in text
    assert "steps.authorization_presence.outputs.count != '0'" in text
    
def test_h06_p2_historical_workflow_does_not_trigger_on_registry_changes():
    text = (ROOT / ".github/workflows/h06-p2-performance-authorization-once.yml").read_text(encoding="utf-8")
    trigger_section = text.split("workflow_dispatch:", 1)[0]
    assert "research/run_requests/h06_p2_authorize_and_execute_once.trigger" in trigger_section
    assert "research/governance/active_research_registry.json" not in trigger_section
