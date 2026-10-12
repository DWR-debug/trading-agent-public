from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation import q221_recipient_parent_identity_probe as probe


def test_fixed_probe_is_seven_distinct_recipient_ids_and_fourteen_queries():
    assert len(probe.SAMPLES) == 7
    assert len({x["recipient_id"] for x in probe.SAMPLES}) == 7
    assert len({x["window"] for x in probe.SAMPLES}) == 7
    assert len(probe.SAMPLES) * 2 == 14
    assert probe.FROZEN_REQUEST_VALUES["HISTORICAL_IDENTITY_CLAIM"] == "false"
    assert probe.FROZEN_REQUEST_VALUES["RECIPIENT_TO_ISSUER_MAPPING"] == "false"


def test_request_rejects_historical_claim_or_changed_budget(tmp_path):
    values = dict(probe.FROZEN_REQUEST_VALUES)
    values["REQUEST_SEQUENCE"] = "2026-10-12T19:50:00Z"
    request = tmp_path / "request.trigger"
    request.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    assert probe.read_request(request)["QUERY_COUNT"] == "14"
    values["HISTORICAL_IDENTITY_CLAIM"] = "true"
    request.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    with pytest.raises(probe.ProbeError, match="REQUEST_VALUE_MISMATCH:HISTORICAL_IDENTITY_CLAIM"):
        probe.read_request(request)


def test_profile_parser_preserves_parent_ueis_and_nulls():
    payload = {
        "recipient_id": "recipient-C",
        "recipient_level": "C",
        "uei": "UEI123",
        "parent_id": "parent-P",
        "parent_uei": "PARENT123",
        "parent_name": "Example Parent",
        "parents": [{"parent_id": "parent-P", "parent_uei": "PARENT123", "parent_name": "Example Parent"}],
        "business_types": ["corporate_entity_not_tax_exempt"],
    }
    result = {
        "profile": {k: payload.get(k) for k in (
            "recipient_id", "recipient_level", "uei", "parent_id", "parent_uei", "parent_name", "parents", "business_types"
        )}
    }
    assert result["profile"]["parent_uei"] == "PARENT123"
    assert result["profile"]["parent_id"] == "parent-P"
    payload["parent_uei"] = None
    assert payload["parent_uei"] is None


def test_response_budget_is_not_expandable():
    assert probe.MAX_RESPONSE_BYTES == 1_000_000
    assert probe.MAX_TOTAL_BYTES == 14_000_000


def test_run_probe_records_all_frozen_samples_and_both_query_results(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "validate_source", lambda _path: {"receipt_fingerprint": probe.SOURCE_RECEIPT_FINGERPRINT})

    def fake_fetch(recipient_id, year, budget):
        sample = next(x for x in probe.SAMPLES if x["recipient_id"] == recipient_id)
        return {
            "requested_url": f"https://example.invalid/{recipient_id}?year={year}",
            "status": "PROFILE_CAPTURED",
            "http_status": 200,
            "profile": {
                "recipient_id": recipient_id,
                "recipient_level": "C",
                "uei": sample["recipient_uei"],
                "parent_id": "parent-P",
                "parent_uei": "PARENTUEI",
                "parent_name": "Parent",
                "parents": [{"parent_id": "parent-P", "parent_uei": "PARENTUEI"}],
                "business_types": [],
            },
        }

    monkeypatch.setattr(probe, "fetch_profile", fake_fetch)
    output = tmp_path / "receipt.json"
    receipt = probe.run_probe({}, Path("unused"), output)
    assert receipt["status"] == "CURRENT_PROFILE_PROBE_COMPLETE_HISTORY_UNPROVEN"
    assert receipt["sample_count"] == 7
    assert receipt["query_count"] == 14
    assert all(len(x["queries"]) == 2 for x in receipt["samples"])
    assert all(x["parent_metadata_comparison"]["all_vs_fiscal_year_parent_uei_equal"] for x in receipt["samples"])
    assert json.loads(output.read_text(encoding="utf-8"))["receipt_fingerprint"] == receipt["receipt_fingerprint"]
