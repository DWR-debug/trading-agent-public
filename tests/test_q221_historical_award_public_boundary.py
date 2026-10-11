import json
from pathlib import Path

from automation.q221_historical_award_public_boundary import (
    ENDPOINT,
    WINDOWS,
    canonical_fingerprint,
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


def _transaction():
    return {
        "Award ID": "FA000001",
        "Mod": "P00001",
        "Recipient Name": "EXAMPLE RESEARCH LLC",
        "Recipient UEI": "ABC123UEI456",
        "recipient_id": "recipient-1",
        "Action Date": "2021-06-03",
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
        "generated_internal_id": "CONT_AWD_EXAMPLE_1",
        "internal_id": "1001",
        "Issued Date": "2021-06-02",
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


def test_q221_sample_is_captured_but_public_boundary_and_mapping_remain_blocked(tmp_path):
    policy = _policy()
    calls = []

    def post(url, payload):
        calls.append((url, payload))
        return 200, json.dumps({
            "results": [_transaction()],
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
        return 200, json.dumps({"results": [_transaction()], "page_metadata": {"page": 1, "hasNext": False}}).encode()

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
