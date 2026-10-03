from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_q133_q170_receipt_persist_is_material_only():
    text=(ROOT/"automation/q133_q170_pit_receipt_persist.py").read_text(encoding="utf-8")
    assert "candidate_results" in text
    assert "scientific_boundary" in text
    assert "safety" in text
    assert "source_code_sha256" in text

def test_q133_q170_receipt_persist_has_no_performance_logic():
    text=(ROOT/"automation/q133_q170_pit_receipt_persist.py").read_text(encoding="utf-8").lower()
    for marker in ("sharpe","profit factor","grid search","holdout ranking","parameter sweep"):
        assert marker not in text