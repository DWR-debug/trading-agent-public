from automation.information_alpha_mechanism_discrimination_replication import (
    DEFAULT_END,
    DEFAULT_START,
    REFERENCE_END,
    REFERENCE_START,
    TASK_ID,
    _assert_temporal_disjointness,
)


def test_q016_window_is_exactly_one_year_and_precedes_q015():
    assert (DEFAULT_END - DEFAULT_START).days == 364
    assert (REFERENCE_END - REFERENCE_START).days == 364
    assert DEFAULT_END < REFERENCE_START
    assert TASK_ID == "Q-016-INFORMATION-ALPHA-MECHANISM-DISCRIMINATION-REPLICATION"


def test_q016_temporal_disjointness_guard():
    _assert_temporal_disjointness()


def test_q016_contract_constants():
    assert DEFAULT_START.isoformat() == "2024-09-25"
    assert DEFAULT_END.isoformat() == "2025-09-24"
    assert REFERENCE_START.isoformat() == "2025-09-25"
    assert REFERENCE_END.isoformat() == "2026-09-24"


def test_missing_gdelt_export_forces_data_insufficient(tmp_path):
    import json

    from automation.information_alpha_mechanism_discrimination_replication import analyze_q016

    payload = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "source_q015_workflow_run": 36161950582,
        "source_q015_artifact_id": 10875399037,
        "source_q015_result_fingerprint": "f7be165efe86a223f1e15dc0cfb206e992a95fecc596197a562c6eb65386e2da",
        "source_q015_input_fingerprint": "5475911e19dfae4aabbce1c66775962dacd7815b86f7dc4e63fe3ecb4fab4836",
        "window": {
            "start": DEFAULT_START.isoformat(),
            "end": DEFAULT_END.isoformat(),
            "calendar_days": 365,
            "strictly_temporally_disjoint_from_q015": True,
        },
        "assets": ["SPY", "TLT", "GLD"],
        "fixed_features": [
            "event_count",
            "attention_score",
            "source_breadth",
            "article_count",
            "negative_goldstein",
            "mean_tone",
        ],
        "mechanism_groups": {
            "intensity_breadth": ["event_count", "attention_score", "source_breadth", "article_count"],
            "severity": ["negative_goldstein"],
            "tone": ["mean_tone"],
        },
        "data_quality": {
            "event_rows_seen": 1,
            "event_rows_skipped": 0,
            "historical_data_complete": False,
            "missing_daily_exports": ["2025-06-14"],
        },
        "observations": [],
    }
    payload["fingerprint"] = "test-frozen-input-fingerprint"
    path = tmp_path / "q016.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = analyze_q016(path, output_dir=tmp_path / "out")
    assert result["status"] == "DATA_INSUFFICIENT"
    assert result["scientific_outcome"] == "NO_SCIENTIFIC_OUTCOME"
    assert result["missing_daily_exports"] == ["2025-06-14"]
    assert result["performance_trial_authorized"] is False
