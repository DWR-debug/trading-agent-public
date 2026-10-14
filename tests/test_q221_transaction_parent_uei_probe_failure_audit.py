from automation.q221_transaction_parent_uei_probe_failure_audit import build_audit, AuditError, EXPECTED_SEQUENCE


def baseline_receipt():
    return {
        "record_type":"q221_transaction_parent_uei_feasibility_probe",
        "status":"TRANSACTION_PARENT_UEI_PROBE_INCOMPLETE",
        "receipt_fingerprint":"", "request_sequence":EXPECTED_SEQUENCE,
        "source_receipt_fingerprint":"9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4",
        "source_receipt_git_blob_sha":"b78cf6f7b48af3f914ee7c6d06a38f6485b0438f",
        "profile_map_run_id":"38305074104",
        "profile_map_artifact":"q221-current-parent-identity-map-38305074104-1",
        "profile_map_receipt_fingerprint":"ae3a3263d5e7d2545dbdaed7ba7ff1cfe3d4cd00e0403352096dcce4d4797602",
        "error_type":"ProbeError","error":"API_HTTP_ERROR:503:","preflight_count":None,
        "download_rows_matched":0,"matches":[],
        "historical_parent_lineage_proven":False,
        "recipient_to_issuer_mapping_frozen":False,
        "historical_first_public_observation_proven":False,
    }


def test_audit_classifies_frozen_503_as_preflight_not_data_download():
    from automation.q221_transaction_parent_uei_probe_failure_audit import fingerprint, BOUNDARY_FP, BOUNDARY_BLOB, PROFILE_RUN_ID, PROFILE_ARTIFACT_NAME, PROFILE_FP
    receipt=baseline_receipt()
    receipt["receipt_fingerprint"]=fingerprint(receipt)
    request={
        "REQUEST_SEQUENCE":EXPECTED_SEQUENCE,
    }
    # Use module's request contract keys as a tiny fixture-independent shape.
    out=build_audit(receipt,request,expected_receipt_fp=fingerprint(receipt))
    assert out["failure_stage"]=="DOCUMENTED_DOWNLOAD_COUNT_PREFLIGHT"
    assert out["transaction_download_attempted"] is False
    assert out["same_route_retry_allowed"] is False
    assert out["interpretation_scope"]["gate_positive"] is False
    assert out["safety"]["live_trading_enabled"] is False


def test_audit_rejects_mismatched_or_non_503_receipt():
    from automation.q221_transaction_parent_uei_probe_failure_audit import fingerprint
    receipt=baseline_receipt()
    receipt["error"]="API_HTTP_ERROR:429:rate limited"
    receipt["receipt_fingerprint"]=fingerprint(receipt)
    try:
        build_audit(receipt,{"REQUEST_SEQUENCE":EXPECTED_SEQUENCE},expected_receipt_fp=fingerprint(receipt))
    except AuditError as exc:
        assert "FROZEN_HTTP_503" in str(exc)
    else:
        raise AssertionError("different failure must not be attributed to the frozen source event")
