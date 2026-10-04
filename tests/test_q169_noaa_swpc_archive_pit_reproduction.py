from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_r4_is_structurally_independent_from_r3():
    text = (ROOT / "automation/q169_noaa_swpc_archive_pit_reproduction.py").read_text(encoding="utf-8")
    assert "q169_noaa_swpc_archive_pit_probe" not in text
    assert "r3_parsing_functions_reused" in text
    assert '"independent_parser": True' in text

def test_r4_freezes_r3_hashes_and_issue_times():
    text = (ROOT / "automation/q169_noaa_swpc_archive_pit_reproduction.py").read_text(encoding="utf-8")
    assert "e73f6e9b573555ca7656ad06999820d1f1437d79ccf1b97202b5ebd5df47ed76" in text
    assert "3e79d7460ba10e11d0f4c6b16e3e464a33e64243beb9f17be5c5aaec64c4cf0c" in text
    assert "2025-10-14T03:30:00+00:00" in text
    assert "2025-10-15T03:30:00+00:00" in text

def test_r4_has_no_performance_or_search_dimension():
    text = (ROOT / "automation/q169_noaa_swpc_archive_pit_reproduction.py").read_text(encoding="utf-8").lower()
    for marker in ("sharpe", "profit factor", "grid search", "threshold sweep", "candidate ranking"):
        assert marker not in text
    assert '"performance": false' in text
    assert '"candidate_pit_validated": false' in text
