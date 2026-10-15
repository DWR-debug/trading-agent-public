import json
from pathlib import Path

from automation.sync_current_operational_status import q221_fpds_identity_bridge_sentence

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "current-status-sync.yml"


def test_current_status_sync_uses_rest_api_and_real_shell_expansion():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'gh api "/repos/${GITHUB_REPOSITORY}/pulls?state=open&per_page=100"' in text
    assert 'gh api "/repos/${GITHUB_REPOSITORY}/issues?state=open&labels=agent-cli-ready&per_page=100"' in text
    assert '--source-master-sha "${source_master_sha}"' in text
    assert '--workflow-run-id "${GITHUB_RUN_ID}"' in text
    assert '--github-state "${RUNNER_TEMP}/status/github_state.json"' in text
    assert "gh pr list" not in text
    assert "gh issue list" not in text
    assert "gh api --silent" not in text
    assert "\\${GITHUB_SHA}" not in text
    assert "\\${RUNNER_TEMP}" not in text

def test_status_sync_uses_checked_out_master_sha_not_push_event_sha():
    text = Path(".github/workflows/current-status-sync.yml").read_text(encoding="utf-8")
    assert "git rev-parse HEAD" in text
    assert 'echo "STATUS_SOURCE_SHA=${checked_out_master_sha}" >> "${GITHUB_ENV}"' in text
    assert '--source-master-sha "${source_master_sha}"' in text
    assert 'assert d["source_master_sha"] == os.environ["STATUS_SOURCE_SHA"]' in text
    assert 'if [ "$remote_master_sha" != "$STATUS_SOURCE_SHA" ]; then' in text
    assert "STATUS_SYNC_MASTER_MOVED_BEFORE_GENERATION" in text


def test_generated_status_matches_current_hosted_qa_architecture():
    generator = Path("automation/sync_current_operational_status.py").read_text(encoding="utf-8")
    assert '"continuous_qa": {' in generator
    assert '"cadence": "15 */6 * * *"' in generator
    assert '"runner": "GitHub-hosted windows-latest"' in generator
    assert '"self_hosted_slots_consumed": 0' in generator
    assert '"research_continuity": {' in generator
    assert "Continuous QA is scheduled every 6 hours on GitHub-hosted Windows" in generator


def test_status_generator_exposes_q179_q184_receipts():
    text = Path("automation/sync_current_operational_status.py").read_text(encoding="utf-8")
    assert "q179_q184_source_feasibility_latest.json" in text
    assert "q179_q184_pit_readiness_r1_latest.json" in text
    assert '"q179_q184_source_feasibility": q179_q184_source_receipt' in text
    assert '"q179_q184_pit_readiness_r1": q179_q184_pit_receipt' in text
    assert "Q179–Q184 Orthogonal Source/PIT Frontier" in text

def test_status_generator_surfaces_q186_pit_r2_boundary():
    source = Path("automation/sync_current_operational_status.py").read_text(encoding="utf-8")
    assert "q186_pit_r2_receipt" in source
    assert "Q186_PIT_R2_CLOCK_ARCHIVE_COMPLETED_NO_PERFORMANCE" in source


def test_status_generator_surfaces_q220_http_representation_probe_result():
    source = Path("automation/sync_current_operational_status.py").read_text(encoding="utf-8")
    assert "38590133217" in source
    assert "HTTP_REPRESENTATION_INVARIANT_AT_PROBE_TIME" in source
    assert "870aa4fdae7eda932bb8f50ebb9eab1a7781ee503fb5120dea5b0f099e4fd65c" in source
    assert "Do not repeat this probe or fetch further primary documents." in source


def test_status_generator_surfaces_only_the_pinned_q221_fpds_redirect_stop():
    sentence = q221_fpds_identity_bridge_sentence()
    assert "run #38712516839" in sentence
    assert "all four returned HTTP 302" in sentence
    assert "response bytes were 0" in sentence
    assert "0 exact record/UEI/name matches" in sentence
    assert "network requests" in sentence or "offline validation" in sentence
    assert "all 348 transaction public-clock rows remain unproven" in sentence
    assert "all 247 recipient-to-issuer mappings remain unfrozen" in sentence
    assert "Do not repeat this route or follow its redirects" in sentence


def test_status_generator_fails_closed_if_q221_fpds_receipt_changes():
    path = Path("research/evidence/q221_fpds_public_atom_identity_bridge_latest.json")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    baseline = q221_fpds_identity_bridge_sentence(receipt)
    assert "all four returned HTTP 302" in baseline

    altered = dict(receipt)
    altered["observations"] = [dict(row) for row in receipt["observations"]]
    altered["observations"][0]["http_status"] = 200

    blocked = q221_fpds_identity_bridge_sentence(altered)
    assert "fails its pinned validation" in blocked
    assert "all four returned HTTP 302" not in blocked
