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
    assert "0001020066-11-000014-index.html" in HISTORICAL_EDGAR_ANCHORS["13D_G"]["url"]
    assert "0001921094-23-000806-index.htm" in HISTORICAL_EDGAR_ANCHORS["FORM144"]["url"]
    assert HISTORICAL_EDGAR_ANCHORS["13D_G"]["accession"] == "0001020066-11-000014"
    assert HISTORICAL_EDGAR_ANCHORS["FORM144"]["accession"] == "0001921094-23-000806"


def test_q098_anchor_can_satisfy_historical_depth_without_false_archive_pass(
    monkeypatch,
) -> None:
    import automation.q098_historical_archive_depth as q098

    current = {
        "filings": {
            "recent": {
                "form": ["SC 13G"],
                "filingDate": ["2026-08-01"],
                "accessionNumber": ["0001020066-26-000001"],
                "acceptanceDateTime": ["20260801160000"],
                "primaryDocument": ["x.htm"],
            },
            "files": [
                {
                    "name": "CIK0001020066-submissions-001.json",
                    "filingFrom": "2010-04-28",
                    "filingTo": "2015-05-10",
                    "filingCount": 10,
                }
            ],
        }
    }
    oldest = {
        "form": ["10-K"],
        "filingDate": ["2010-05-01"],
        "accessionNumber": ["0001020066-10-000001"],
    }

    def fake_get(url: str):
        if url.endswith("CIK0001020066.json"):
            import json
            return 200, json.dumps(current).encode(), "application/json"
        import json
        return 200, json.dumps(oldest).encode(), "application/json"

    monkeypatch.setattr(q098, "get", fake_get)
    row = q098.submission_archive_probe(
        "13D_G",
        "0001020066",
        {"SC 13G", "SC 13G/A"},
    )
    assert row["status"] == "VERIFIABLE"
    assert (
        row["coverage_completeness"]
        == "HISTORICAL_ANCHOR_VERIFIED_COMPLETE_ARCHIVE_NOT_PROVEN"
    )
    assert row["checks"]["oldest_extension_contains_target_form"] is False


def test_q098_historical_anchor_acceptance_time_contract(monkeypatch) -> None:
    import automation.q098_historical_archive_depth as q098

    html = (
        "<html><body>Form SC 13G "
        "SEC Accession No. 0001020066-11-000014 "
        "Filing Date 2011-06-09 "
        "Accepted 2011-06-09 16:13:07</body></html>"
    )

    monkeypatch.setattr(
        q098,
        "get",
        lambda url: (200, html.encode("utf-8"), "text/html; charset=UTF-8"),
    )
    row = q098.historical_edgar_anchor_probe(
        "13D_G",
        q098.HISTORICAL_EDGAR_ANCHORS["13D_G"],
    )
    assert row["status"] == "VERIFIABLE"
    assert row["checks"]["accepted_timestamp_present"] is True
    assert row["checks"]["accession_identity_present"] is True


def test_q098_archive_depth_never_authorizes_performance() -> None:
    import automation.q098_historical_archive_depth as q098
    import inspect

    source = inspect.getsource(q098.main)
    assert '"performance_authorized": False' in source
    assert '"performance_evaluation": False' in source
    assert '"candidate_selection": False' in source
    assert '"candidate_ranking": False' in source
