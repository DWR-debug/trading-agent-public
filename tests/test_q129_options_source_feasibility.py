from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_q129_contract_is_pinned_and_conservative():
    data = json.loads(
        (
            ROOT
            / "research/governance/q129_options_source_contract_2026_10_03.json"
        ).read_text(encoding="utf-8")
    )
    assert data["candidate_id"] == "Q129"
    assert data["status"] == "SOURCE_FEASIBILITY_COMPLETED_INDEPENDENT_PIT_REPRODUCED"
    assert data["independent_pit_receipt"]["workflow_run_id"] == 37123847841
    assert len(data["canonical_release"]["assets"]) == 6
    assert data["information_boundary"]["same_day_use_allowed"] is False
    assert data["scientific_boundary"]["performance"] is False
    assert data["safety"]["PAPER_ONLY"] is True


def test_q129_workflow_is_hosted_and_fail_closed():
    text = (
        ROOT / ".github/workflows/q129-options-source-feasibility.yml"
    ).read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04" in text
    assert "Q129_SOURCE_ASSETS_VERIFIED" in text
    assert "same_day_decision_use_allowed" in text
    assert "automatic_promotion" in text


def test_q129_verifier_has_exact_release_hashes():
    text = (
        ROOT / "automation/q129_options_source_feasibility.py"
    ).read_text(encoding="utf-8")
    assert "SPY_options.parquet" in text
    assert "QQQ_options.parquet" in text
    assert "IWM_options.parquet" in text
    assert (
        "a7152991b45b81f090f970e945bf88def8093b8ecb9b250e9891cb6d88041f0a"
        in text
    )
