import json
from pathlib import Path

import io
import urllib.error

import pytest

from automation.q221_historical_award_public_boundary import (
    ENDPOINT,
    FIELDS,
    WINDOWS,
    canonical_fingerprint,
    default_post,
    query_payload,
    run_gate,
)


def _policy():
    value = {
        "candidate_id": "Q221",
        "status": "Q221_HISTORICAL_POLICY_VINTAGES_RECONSTRUCTED",
        "all_target_windows_covered": True,
        "policy_markers_consistent_across_vintages": True,
        "historical_policy_vintages_reconstructed": True,
        "lookahead_used": False,
        "receipt_fingerprint": "",
    }
    value["receipt_fingerprint"] = canonical_fingerprint(value)
    return value


def _transaction(year: int = 2021):
    return {
        "Award ID": f"FA{year}0001",
        "Mod": f"P{year % 100:02d}",
        "Recipient Name": "EXAMPLE RESEARCH LLC",
        "Recipient UEI": "ABC123UEI456",
        "recipient_id": "recipient-1",
        "Action Date": f"{year}-06-03",
        "Action Type": "AWARD",
        "Transaction Amount": "123456.00",
        "Awarding Agency": "Department of Defense",
        "Awarding Sub Agency": "Department of the Air Force",
        "Funding Agency": "Department of Defense",
        "Funding Sub Agency": "Air Force Research Laboratory",
        "NAICS": "541715",
        "PSC": "A",
        "Award Type": "PURCHASE ORDER",
        "Transaction Description": "Research prototype",
        "generated_internal_id": f"CONT_AWD_EXAMPLE_{year}",
        "internal_id": f"100{year % 10}",
        "Issued Date": f"{year}-06-02",
        "Last Modified Date": "2026-01-02",
    }


def test_q221_contract_uses_fixed_non_amount_sorted_r_and_d_windows():
    assert len(WINDOWS) == 7
    payload = query_payload("2021-01-01", "2021-12-31")
    assert payload["filters"]["award_type_codes"] == ["A", "B", "C", "D"]
    assert payload["filters"]["naics_codes"] == {"require": ["541713", "541714", "541715"]}
    assert payload["sort"] == "Action Date"
    assert payload["order"] == "asc"
    assert payload["limit"] == 50
    assert payload["sort"] != "Transaction Amount"
    # USAspending's documented TimePeriodObject accepts only start_date/end_date.
    assert payload["filters"]["time_period"] == [
        {"start_date": "2021-01-01", "end_date": "2021-12-31"}
    ]
    # Last Modified Date is not a documented selectable transaction-search field.
    assert "Last Modified Date" not in FIELDS


def test_q221_sample_is_captured_but_public_boundary_and_mapping_remain_blocked(tmp_path):
    policy = _policy()
    calls = []

    def post(url, payload):
        calls.append((url, payload))
        year = int(payload["filters"]["time_period"][0]["start_date"][:4])
        return 200, json.dumps({
            "results": [_transaction(year)],
            "page_metadata": {"page": 1, "hasNext": False, "last_record_unique_id": 1001, "last_record_sort_value": "2021-06-03"},
        }).encode()

    output = tmp_path / "receipt.json"
    receipt = run_gate(output, policy, post=post, pause_seconds=0)
    assert len(calls) == 7
    assert all(url == ENDPOINT for url, _ in calls)
    assert receipt["source_sample_complete"] is True
    assert receipt["sampled_transaction_count"] == 7
    assert receipt["historical_first_public_observation_proven"] is False
    assert receipt["exact_transaction_class_applicability_proven"] is False
    assert receipt["recipient_to_issuer_mapping_frozen"] is False
    assert receipt["gate_positive"] is False
    assert receipt["status"] == "Q221_HISTORICAL_AWARD_SAMPLE_CAPTURED_PUBLIC_BOUNDARY_UNPROVEN"
    row = receipt["transactions"][0]
    assert row["agency_exception_class"] == "DOD_90_DAY_EXCEPTION_CANDIDATE"
    assert row["historical_first_public_observation"] is None
    assert row["recipient_to_issuer_status"].startswith("UNMAPPED")
    reread = json.loads(output.read_text(encoding="utf-8"))
    assert canonical_fingerprint(reread) == reread["receipt_fingerprint"]
    assert reread["live_execution"] is False


def test_q221_incomplete_query_is_not_misreported_as_economic_falsification(tmp_path):
    def post(url, payload):
        if payload["filters"]["time_period"][0]["start_date"] == "2020-01-01":
            raise RuntimeError("simulated transport issue")
        year = int(payload["filters"]["time_period"][0]["start_date"][:4])
        return 200, json.dumps({"results": [_transaction(year)], "page_metadata": {"page": 1, "hasNext": False}}).encode()

    receipt = run_gate(tmp_path / "receipt.json", _policy(), post=post, pause_seconds=0)
    assert receipt["source_sample_complete"] is False
    assert receipt["query_failure_count"] == 1
    assert receipt["status"] == "Q221_HISTORICAL_AWARD_SOURCE_SAMPLE_BLOCKED"
    assert receipt["next_gate"].startswith("repair the fixed-window source query")
    assert receipt["scientific_evidence"] is False


def test_q221_refuses_invalid_policy_vintage_without_querying(tmp_path):
    policy = _policy()
    policy["lookahead_used"] = True
    called = False

    def post(url, payload):
        nonlocal called
        called = True
        raise AssertionError("invalid policy receipt must stop before query")

    receipt = run_gate(tmp_path / "receipt.json", policy, post=post, pause_seconds=0)
    assert called is False
    assert receipt["policy_vintage_receipt_verified"] is False
    assert receipt["source_sample_complete"] is False
    assert receipt["historical_first_public_observation_proven"] is False


def test_q221_http_400_error_body_is_preserved_for_bounded_diagnostics(monkeypatch):
    body = b'{"detail":"unsupported field name"}'

    def fail_request(*args, **kwargs):
        raise urllib.error.HTTPError(
            ENDPOINT, 400, "Bad Request", hdrs=None, fp=io.BytesIO(body)
        )

    monkeypatch.setattr(
        "automation.q221_historical_award_public_boundary.urllib.request.urlopen",
        fail_request,
    )
    with pytest.raises(RuntimeError, match=r"USASPENDING_HTTP_400:.*unsupported field name"):
        default_post(ENDPOINT, query_payload("2021-01-01", "2021-12-31"))
