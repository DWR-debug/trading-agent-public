from pathlib import Path
import json

from automation.top_candidate_source_preflight import TARGETS, run


def test_top_candidate_source_preflight_is_non_authorizing(tmp_path):
    output = tmp_path / "preflight.json"
    result = run(output)
    assert output.is_file()
    assert result["candidates"] == ["Q218", "Q219", "Q220", "Q221"]
    assert result["scientific_evidence"] is False
    assert result["performance_authorization"] is False
    assert result["holdout_selection"] is False
    assert result["ranking"] is False
    assert result["tuning"] is False
    assert result["promotion"] is False
    assert result["live_execution"] is False
    assert set(TARGETS) == {
        "Q218_sec_submissions",
        "Q218_sec_edgar_entity",
        "Q220_fsn_dataset_landing",
        "Q220_fsn_smallest_archive",
        "Q221_usaspending_home",
        "Q221_usaspending_award_example",
    }


def test_top_candidate_source_preflight_json_roundtrip(tmp_path):
    output = tmp_path / "preflight.json"
    run(output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["bundle_fingerprint"]
    assert all("name" in item and "url" in item for item in payload["checks"])
