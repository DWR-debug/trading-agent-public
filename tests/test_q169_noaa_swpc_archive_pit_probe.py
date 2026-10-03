from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_q169_probe_uses_fixed_official_archive_and_semantics_sources():
    text = (ROOT / "automation/q169_noaa_swpc_archive_pit_probe.py").read_text(encoding="utf-8")
    assert "daily_reports/geoalerts/2025/10/" in text
    assert "products/notifications-timeline" in text
    assert 'SAMPLE_DATES = tuple(SAMPLE_FILES)' in text


def test_q169_probe_is_boundary_only():
    text = (ROOT / "automation/q169_noaa_swpc_archive_pit_probe.py").read_text(encoding="utf-8").lower()
    for marker in ("sharpe", "profit factor", "threshold sweep", "grid search", "candidate ranking"):
        assert marker not in text
    assert '"performance": false' in text
    assert '"candidate_pit_validated": false' in text


def test_q169_probe_requires_candidate_specific_join_before_pit_validated():
    text = (ROOT / "automation/q169_noaa_swpc_archive_pit_probe.py").read_text(encoding="utf-8")
    assert '"candidate_specific_exposure_map_frozen": False' in text
    assert '"candidate_specific_revision_lineage_reconstructed": False' in text
    assert '"candidate_pit_validated": False' in text


def test_q169_probe_freezes_exact_noaa_daily_filenames():
    text = (ROOT / "automation/q169_noaa_swpc_archive_pit_probe.py").read_text(encoding="utf-8")
    assert '"2025-10-14": "1014GEOA.txt"' in text
    assert '"2025-10-15": "1015GEOA.txt"' in text
