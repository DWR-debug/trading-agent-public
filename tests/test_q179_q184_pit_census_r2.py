from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_q179_q184_r2_contains_all_candidates_and_is_non_authorizing() -> None:
    text = (ROOT / "automation/q179_q184_pit_census_r2.py").read_text(encoding="utf-8")
    for candidate in ("Q179", "Q180", "Q181", "Q182", "Q183", "Q184"):
        assert f'"{candidate}"' in text
    for marker in (
        "PIT_HISTORICAL_CENSUS_COMPLETED_NO_PERFORMANCE",
        "holdout_used",
        "candidate_ranked_by_returns",
        "parameter_search",
        "promotion",
        "live_execution",
    ):
        assert marker in text


def test_q179_q184_r2_requires_conservative_archive_and_clock_semantics() -> None:
    text = (ROOT / "automation/q179_q184_pit_census_r2.py").read_text(encoding="utf-8")
    assert "public-availability boundary" in text
    assert "revision lineage" in text
    assert "intraday/public-boundary" in text
    assert "historical daily transaction sample" in text
    assert "fixed operator/issuer mapping" in text


def test_q179_q184_r2_workflow_is_hosted_and_paper_only() -> None:
    text = (ROOT / ".github/workflows/q179-q184-pit-census-r2.yml").read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04" in text
    assert "PIT_HISTORICAL_CENSUS_COMPLETED_NO_PERFORMANCE" in text
    assert "LIVE_TRADING_ENABLED" in text


def test_q184_uses_pdf_text_extraction_for_clock_notice() -> None:
    text = (ROOT / "automation/q179_q184_pit_census_r2.py").read_text(encoding="utf-8")
    assert "PdfReader" in text
    assert "pdf_text_probe" in text
    assert "5:00 am eastern time" in text
    assert "previous day" in text


def test_q184_pdf_probe_normalizes_extracted_whitespace() -> None:
    text = (ROOT / "automation/q179_q184_pit_census_r2.py").read_text(encoding="utf-8")
    assert 're.sub(r"\\s+", " ", text)' in text
    assert '"normalized_text_length"' in text
