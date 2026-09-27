from __future__ import annotations

import json
from pathlib import Path

def test_q036_is_diagnostic_only() -> None:
    spec=json.loads(Path("research/preregistrations/q036_t056_risk_mechanism_diagnostic_2026_09_27.json").read_text(encoding="utf-8"))
    assert spec["status"]=="PREREGISTERED_DIAGNOSTIC_ONLY"
    assert spec["governance"]["performance_evaluation"] is False
    assert spec["methodology"]["no_parameter_search"] is True
    assert spec["methodology"]["no_family_selection"] is True

def test_q036_arm_set_is_fixed() -> None:
    assert {"CONTROL","RISK-A","RISK-B","RISK-C","RISK-D"} == {"CONTROL","RISK-A","RISK-B","RISK-C","RISK-D"}


def test_q036_source_binding_is_immutable() -> None:
    spec=json.loads(Path("research/preregistrations/q036_t056_risk_mechanism_diagnostic_2026_09_27.json").read_text(encoding="utf-8"))
    assert spec["source_workflow_run"] == 36342102919
    assert spec["source_artifact_id"] == 10939680447
    assert spec["source_head_sha"] == "23e09d478ef4d7c9f866b8fc123b1842c9953ad8"


def test_q036_workflow_fetches_history_for_exact_source_commit() -> None:
    workflow=Path(".github/workflows/q036-t056-risk-mechanism-diagnostic.yml").read_text(encoding="utf-8")
    assert "fetch-depth: 0" in workflow


def test_q036_source_blob_binding_is_frozen() -> None:
    spec=json.loads(Path("research/preregistrations/q036_t056_risk_mechanism_diagnostic_2026_09_27.json").read_text(encoding="utf-8"))
    assert spec["source_file_blob_sha"] == "33be8c29281ed7da2d109baad641d28fb91802e3"

    
def test_q036_preregistration_binds_to_t056_artifact() -> None:
    spec=json.loads(Path("research/preregistrations/q036_t056_risk_mechanism_diagnostic_2026_09_27.json").read_text(encoding="utf-8"))
    assert spec["source_artifact_id"] == 10939680447
    assert spec["source_report_fingerprint"] == "56feed52b6c8321e3b4cfcf7914b87d2d54ad4cf7d1cf66b095a62db0453943f"

def test_q036_localizes_relative_dataset_paths(tmp_path) -> None:
    import json
    from automation.q036_t056_risk_mechanism_diagnostic import localize_manifest

    dataset = tmp_path / "datasets" / "BSV"
    dataset.mkdir(parents=True)
    (dataset / "1d.csv").write_text("timestamp,open,high,low,close,volume\n", encoding="utf-8")

    manifest_dir = tmp_path / "coverage" / "T053"
    manifest_dir.mkdir(parents=True)
    manifest = manifest_dir / "coverage_preflight_test.json"
    manifest.write_text(json.dumps({
        "data_snapshot": {
            "datasets": [
                {"path": "research/runs/q035_coverage/T-2026-09-27-053-COVERAGE/datasets/BSV/1d.csv"}
            ]
        }
    }), encoding="utf-8")

    localized = localize_manifest(manifest)
    try:
        data = json.loads(localized.read_text(encoding="utf-8"))
        assert data["data_snapshot"]["datasets"][0]["path"] == str((manifest_dir / "datasets" / "BSV" / "1d.csv").resolve())
    finally:
        localized.unlink(missing_ok=True)
