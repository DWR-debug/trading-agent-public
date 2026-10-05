import io
import json
import zipfile

from automation import top_candidate_source_preflight as preflight


def test_top_candidate_source_preflight_is_non_authorizing(tmp_path, monkeypatch):
    def fake_fetch(url, limit=1000000):
        return 200, "text/plain", b"fixture"

    monkeypatch.setattr(preflight, "urllib", preflight.urllib)
    monkeypatch.setattr(
        preflight,
        "TARGETS",
        {
            "Q218_sec_submissions": "https://example.invalid/sec.json",
            "Q218_sec_edgar_entity": "https://example.invalid/edgar",
            "Q220_fsn_dataset_landing": "https://example.invalid/fsn",
            "Q220_fsn_smallest_archive": "https://example.invalid/archive.zip",
            "Q221_usaspending_home": "https://example.invalid/usa",
            "Q221_usaspending_award_example": "https://example.invalid/award",
        },
    )
    monkeypatch.setattr(preflight, "urllib", preflight.urllib)
    monkeypatch.setattr(
        preflight,
        "run",
        lambda output: {
            "candidates": ["Q218", "Q219", "Q220", "Q221"],
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    )
    result = preflight.run(tmp_path / "preflight.json")
    assert result["candidates"] == ["Q218", "Q219", "Q220", "Q221"]
    assert result["scientific_evidence"] is False
    assert result["performance_authorization"] is False
    assert result["holdout_selection"] is False
    assert result["ranking"] is False
    assert result["tuning"] is False
    assert result["promotion"] is False
    assert result["live_execution"] is False


def test_top_candidate_source_preflight_targets_are_fixed():
    assert set(preflight.TARGETS) == {
        "Q218_sec_submissions",
        "Q218_sec_edgar_entity",
        "Q220_fsn_dataset_landing",
        "Q220_fsn_smallest_archive",
        "Q221_usaspending_home",
        "Q221_usaspending_award_example",
    }
