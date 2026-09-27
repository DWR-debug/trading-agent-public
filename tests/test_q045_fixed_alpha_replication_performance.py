from automation.q045_fixed_alpha_replication_performance import SYMBOLS,_a1_signal,_summary

def test_q045_universe_is_fixed():
    assert SYMBOLS == ("AON","CVS","ADSK","BA","T","F","LUV","NFLX")

def test_q045_summary_split_is_fixed():
    s=_summary([0.001]*3498)
    assert s["research"]["day_count"]==2798
    assert s["holdout"]["day_count"]==700

def test_q045_performance_contract_is_top_level():
    import json
    from pathlib import Path
    p=json.loads(Path("research/preregistrations/q045_fixed_alpha_replication_performance_2026_09_27.json").read_text())
    assert p["performance_evaluation"] is True
    assert p["oos_evaluation"] is True
    assert p["holdout_evaluation"] is True
    assert p["coverage_source"]["workflow_run_id"] == 36347316117
    assert p["coverage_source"]["artifact_id"] == 10940494021
    assert p["coverage_source"]["reuse_policy"] == "immutable_reuse; no reacquisition or symbol re-selection"

def test_q045_manifest_localization_preserves_content_and_maps_dataset_paths(tmp_path):
    import json
    from automation.q045_fixed_alpha_replication_performance import _localize_manifest

    coverage_root = tmp_path / "coverage"
    dataset = coverage_root / "T-2026-09-27-063" / "datasets" / "AON"
    dataset.mkdir(parents=True)
    csv_path = dataset / "1d.csv"
    csv_path.write_text("timestamp,open,high,low,close,volume\n", encoding="utf-8")

    source = tmp_path / "source_manifest.json"
    source_payload = {
        "status": "coverage_passed",
        "data_snapshot": {
            "datasets": [
                {
                    "path": "research/runs/q043_coverage/T-2026-09-27-063/datasets/AON/1d.csv",
                    "candle_count": 0,
                    "fingerprint": "fixed",
                }
            ]
        },
    }
    source.write_text(json.dumps(source_payload), encoding="utf-8")

    localized = _localize_manifest(source, coverage_root)
    data = json.loads(localized.read_text(encoding="utf-8"))
    assert source_payload["data_snapshot"]["datasets"][0]["path"].startswith(
        "research/runs/q043_coverage/"
    )
    assert data["data_snapshot"]["datasets"][0]["path"] == str(csv_path)
    assert data["data_snapshot"]["datasets"][0]["fingerprint"] == "fixed"
