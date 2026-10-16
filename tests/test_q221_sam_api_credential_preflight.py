import json

from automation.q221_sam_api_credential_preflight import build_receipt


def test_missing_secret_fails_closed_without_requests():
    receipt = build_receipt(None)

    assert receipt["status"] == "SAM_GOV_API_KEY_NOT_CONFIGURED_NO_REQUESTS"
    assert receipt["credential_configured"] is False
    assert receipt["network_requests_made"] == 0
    assert receipt["sam_api_requests_made"] == 0
    assert receipt["source_requests_made"] == 0
    assert receipt["historical_public_clock_gate_cleared"] is False
    assert receipt["performance_authorization"] is False
    assert receipt["live_execution"] is False


def test_blank_secret_is_not_treated_as_configured():
    receipt = build_receipt("   ")

    assert receipt["credential_configured"] is False
    assert receipt["status"] == "SAM_GOV_API_KEY_NOT_CONFIGURED_NO_REQUESTS"


def test_configured_secret_is_only_reported_as_boolean():
    sentinel = "NEVER_LOG_THIS_SAM_SECRET_123456789"
    receipt = build_receipt(sentinel)
    serialized = json.dumps(receipt)

    assert receipt["status"] == "SAM_GOV_API_KEY_CONFIGURED_NO_REQUESTS"
    assert receipt["credential_configured"] is True
    assert sentinel not in serialized
    assert receipt["credential_value_logged"] is False
    assert receipt["credential_value_persisted"] is False
    assert receipt["credential_value_hashed"] is False
    assert receipt["network_requests_made"] == 0
    assert receipt["sam_api_requests_made"] == 0
    assert receipt["source_requests_made"] == 0
