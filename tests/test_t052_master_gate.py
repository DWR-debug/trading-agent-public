from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_t052_allows_documented_s10_runtime_status_descendant():
    workflow = (ROOT / ".github/workflows/t052-exact-master-ci-gate.yml").read_text(
        encoding="utf-8"
    )
    assert "ops/s10_runtime_status.json" in workflow
    assert "MASTER_MOVED_WITH_NON_EVIDENCE_CODE_CHANGES" in workflow
