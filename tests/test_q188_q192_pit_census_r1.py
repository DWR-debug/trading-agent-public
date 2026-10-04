from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_q188_q192_pit_census_has_five_candidates():
    text = (ROOT / "automation/q188_q192_pit_census_r1.py").read_text(encoding="utf-8")
    for candidate in ("Q188", "Q189", "Q190", "Q191", "Q192"):
        assert f'"{candidate}"' in text
    assert "PIT_HISTORICAL_CENSUS_COMPLETED_NO_PERFORMANCE" in text


def test_q188_q192_pit_census_preserves_pit_prohibitions():
    text = (ROOT / "automation/q188_q192_pit_census_r1.py").read_text(encoding="utf-8")
    for marker in (
        "first-public-observation",
        "revision",
        "issuer",
        "holdout_selection_allowed",
        "performance_authorized",
        "live_execution",
    ):
        assert marker in text


def test_q188_q192_uses_machine_readable_source_surfaces():
    text = (ROOT / "automation/q188_q192_pit_census_r1.py").read_text(encoding="utf-8")
    assert "saferproducts.gov/RestWebServices/Recall" in text
    assert "api.fda.gov/drug/shortages.json" in text
    assert "api.crossref.org/works" in text
    assert "echo.epa.gov/tools/data-downloads" in text


def test_q189_accepts_cpsc_json_array_shape() -> None:
    text = (ROOT / "automation/q188_q192_pit_census_r1.py").read_text(encoding="utf-8")
    assert "if isinstance(payload, list)" in text
    assert "elif isinstance(payload, dict)" in text
