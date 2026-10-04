import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_q144_page_map_is_fixed_to_q107_universe():
    data=json.loads((ROOT/"research/governance/q144_q107_wikipedia_page_map_2026_10_03.json").read_text(encoding="utf-8"))
    assert data["universe_fingerprint"]=="18571a7871f72b8018905c10c289724bb5cf976ab7fa4f9f424599ddc727fbd2"
    assert [x["symbol"] for x in data["symbols"]]==["SPGI","NDAQ","AMP","RJF","WMB","VLO","DVN","EMN"]
    assert data["freeze_policy"]["page_title_is_frozen"] is True

def test_q137_q144_micro_pit_is_non_performance():
    text=(ROOT/"automation/q137_q144_micro_pit.py").read_text(encoding="utf-8")
    for marker in ('"performance":False','"holdout_selection":False','"candidate_ranking":False','"parameter_search":False','"live_execution":False'):
        assert marker in text

def test_q137_q144_micro_pit_has_no_search_or_return_metrics():
    text=(ROOT/"automation/q137_q144_micro_pit.py").read_text(encoding="utf-8").lower()
    for marker in ("sharpe","profit factor","grid search","threshold sweep","holdout ranking"):
        assert marker not in text

def test_q144_uses_fixed_wikimedia_endpoint_contract():
    text=(ROOT/"automation/q137_q144_micro_pit.py").read_text(encoding="utf-8")
    assert "all-access/all-agents" in text
    assert "2025082500/2025092500" in text

from automation.q137_q144_micro_pit import _overlapping_submission_files, _submission_rows


def test_q137_historical_submission_file_selection_is_date_bounded():
    payload = {
        "filings": {
            "files": [
                {"name": "old.json", "filingFrom": "2020-01-01", "filingTo": "2024-12-31", "filingCount": 10},
                {"name": "target.json", "filingFrom": "2025-01-01", "filingTo": "2025-12-31", "filingCount": 20},
                {"name": "future.json", "filingFrom": "2026-01-01", "filingTo": "2026-12-31", "filingCount": 30},
            ]
        }
    }
    selected = _overlapping_submission_files(payload)
    assert [x["name"] for x in selected] == ["target.json"]


def test_q137_submission_rows_support_historical_continuation_shape():
    payload = {
        "filingDate": ["2025-08-25", "2025-09-24"],
        "acceptanceDateTime": ["20250825120000", "20250924150000"],
        "accessionNumber": ["0000000001-25-000001", "0000000001-25-000002"],
        "form": ["SC 13G", "SC 13G/A"],
    }
    rows = _submission_rows(payload, "SPGI")
    assert [row["accession"] for row in rows] == [
        "0000000001-25-000001", "0000000001-25-000002"
    ]
