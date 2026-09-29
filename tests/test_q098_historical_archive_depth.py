from __future__ import annotations

from automation.q098_historical_archive_depth import (
    HISTORICAL_EDGAR_ANCHORS,
    submission_rows,
)


def test_q098_accepts_nested_and_flat_sec_submission_shapes() -> None:
    nested = {
        "filings": {
            "recent": {
                "form": ["13F-HR"],
                "filingDate": ["2024-02-14"],
                "accessionNumber": ["0001067983-24-000001"],
                "acceptanceDateTime": ["20240214160000"],
                "primaryDocument": ["x.txt"],
            }
        }
    }
    flat = {
        "form": ["144"],
        "filingDate": ["2024-03-01"],
        "accessionNumber": ["0001326801-24-000001"],
        "acceptanceDateTime": ["20240301160000"],
        "primaryDocument": ["y.txt"],
    }
    assert submission_rows(nested)[0]["form"] == "13F-HR"
    assert submission_rows(flat)[0]["form"] == "144"


def test_q098_is_non_evaluative() -> None:
    from pathlib import Path
    source = Path("automation/q098_historical_archive_depth.py").read_text(encoding="utf-8")
    assert '"performance_evaluation": False' in source
    assert '"holdout_evaluation": False' in source
    assert '"candidate_ranking": False' in source
    assert '"candidate_selection": False' in source
    assert '"parameter_search": False' in source
    assert '"performance_authorized": False' in source


def test_q098_historical_edgar_anchors_are_frozen_to_study_appropriate_dates() -> None:
    assert HISTORICAL_EDGAR_ANCHORS["13D_G"]["study_date"] == "2011-06-09"
    assert HISTORICAL_EDGAR_ANCHORS["FORM144"]["study_date"] == "2023-11-06"
    assert "index-headers.html" in HISTORICAL_EDGAR_ANCHORS["13D_G"]["url"]
    assert "index-headers.html" in HISTORICAL_EDGAR_ANCHORS["FORM144"]["url"]
    assert HISTORICAL_EDGAR_ANCHORS["13D_G"]["accession"] == "0001020066-11-000014"
    assert HISTORICAL_EDGAR_ANCHORS["FORM144"]["accession"] == "0001921094-23-000806"
