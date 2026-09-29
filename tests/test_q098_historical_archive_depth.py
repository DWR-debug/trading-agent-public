from __future__ import annotations

from automation.q098_historical_archive_depth import submission_rows


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
