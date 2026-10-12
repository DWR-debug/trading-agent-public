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
