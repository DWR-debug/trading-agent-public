from __future__ import annotations

from pathlib import Path

import pytest

from automation import q221_current_parent_identity_map_probe as probe


def test_all_247_frozen_recipient_candidates_are_queried_once():
    assert probe.FROZEN_REQUEST_VALUES["RECIPIENT_COUNT"] == "247"
    assert probe.FROZEN_REQUEST_VALUES["QUERY_COUNT"] == "247"
    assert probe.MAX_RESPONSE_BYTES == 100_000
    assert probe.MAX_TOTAL_BYTES == 25_000_000
    assert probe.FROZEN_REQUEST_VALUES["HISTORICAL_IDENTITY_CLAIM"] == "false"
    assert probe.FROZEN_REQUEST_VALUES["RECIPIENT_TO_ISSUER_MAPPING"] == "false"


def test_current_parent_classification_never_promotes_an_issuer():
    assert probe.classify_parent("UEI1", "UEI1", "parent-id") == "CURRENT_PROFILE_SELF_OR_NO_SEPARATE_PARENT"
    assert probe.classify_parent("UEI1", None, "parent-id") == "PARENT_UEI_MISSING"
    assert probe.classify_parent("UEI1", "UEI2", "parent-id") == "CURRENT_PARENT_ENTITY_LEAD"
    assert probe.classify_parent("UEI1", "UEI2", None) == "PARENT_UEI_DIFFERS_PARENT_ID_MISSING"


def test_request_rejects_any_historical_mapping_or_performance_authority(tmp_path):
    values = dict(probe.FROZEN_REQUEST_VALUES)
    values["REQUEST_SEQUENCE"] = "2026-10-12T20:25:00Z"
    path = tmp_path / "request.trigger"
    path.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    assert probe.read_request(path)["QUERY_COUNT"] == "247"
    values["HISTORICAL_IDENTITY_CLAIM"] = "true"
    path.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    with pytest.raises(probe.ProbeError, match="VALUE_MISMATCH:HISTORICAL_IDENTITY_CLAIM"):
        probe.read_request(path)


def test_profile_map_is_current_state_only_and_has_no_issuer_mapping_fields():
    assert "issuer_symbol" not in probe.FROZEN_REQUEST_VALUES
    assert probe.FEASIBILITY_RUN_ID == "38303469112"
    assert probe.FEASIBILITY_RECEIPT_FINGERPRINT == "d4f5819f51849d7ba037ec0fa610f5e6e47b74b9353a0c534b6e2e666842509e"


def test_frozen_source_receipt_really_has_247_unmapped_candidates():
    root = Path(__file__).parents[1]
    source, candidates = probe.validate_source(root / "research" / "evidence" / "q221_historical_public_boundary_latest.json")
    assert len(candidates) == 247
    assert all(x["mapping_status"] == "UNMAPPED" and x["issuer_symbol"] is None for x in candidates)
