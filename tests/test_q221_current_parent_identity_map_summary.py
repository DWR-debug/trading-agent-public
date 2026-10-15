import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "research/evidence/q221_current_parent_identity_map_summary_2026_10_12.json"


def test_q221_parent_map_summary_pins_completed_artifact_and_complete_247_profile_coverage():
    row = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert row["record_type"] == "q221_current_parent_identity_lead_map_summary"
    assert row["status"] == "CURRENT_PARENT_MAP_COMPLETE_HISTORY_UNPROVEN"
    assert row["immutable_run"]["workflow_run_id"] == 38305074104
    assert row["immutable_run"]["artifact_id"] == 11772786096
    assert row["immutable_run"]["artifact_expires"] is False
    assert row["receipt_fingerprint"] == "ae3a3263d5e7d2545dbdaed7ba7ff1cfe3d4cd00e0403352096dcce4d4797602"
    assert row["upstream"]["source_receipt_fingerprint"] == "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
    assert row["coverage"]["expected_recipients"] == row["coverage"]["captured_recipients"] == 247
    assert row["coverage"]["expected_queries"] == row["coverage"]["captured_queries"] == 247
    assert row["coverage"]["verified_profiles"] == 247
    assert row["current_parent_classification_counts"] == {
        "CURRENT_PARENT_ENTITY_LEAD": 71,
        "CURRENT_PROFILE_SELF_OR_NO_SEPARATE_PARENT": 176,
    }


def test_q221_current_parent_lead_map_does_not_claim_historical_or_issuer_mapping():
    row = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert row["interpretation"]["current_parent_identity_leads_only"] is True
    assert row["interpretation"]["historical_parent_lineage_proven"] is False
    assert row["interpretation"]["historical_first_public_observation_proven"] is False
    assert row["interpretation"]["recipient_to_issuer_mapping_frozen"] is False
    assert row["interpretation"]["scientific_evidence"] is False
    assert row["interpretation"]["performance_authorization"] is False
    assert row["interpretation"]["promotion"] is False
    assert row["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
