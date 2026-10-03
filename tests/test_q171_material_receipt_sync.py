from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_q171_material_sync_is_separate_from_scientific_workflow():
    sync=(ROOT/".github/workflows/q171-material-receipt-sync.yml").read_text(encoding="utf-8")
    deep=(ROOT/".github/workflows/deep-frontier-source-feasibility.yml").read_text(encoding="utf-8")
    assert "workflow_run:" in sync
    assert "actions: read" in sync
    assert "contents: write" in sync
    assert "github.event.workflow_run.head_branch == 'master'" in sync
    assert "automation/github_contents_publish.py" in sync
    assert "contents: read" in deep
    assert "contents: write" not in deep.split("concurrency:",1)[0]
    assert "Persist material Q171 WARC receipt" not in deep

def test_q171_material_sync_reacts_to_completion_not_scientific_outcome():
    text=(ROOT/".github/workflows/q171-material-receipt-sync.yml").read_text(encoding="utf-8")
    assert "types: [completed]" in text
    assert "conclusion != 'cancelled'" in text
    assert "conclusion != 'skipped'" in text