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
