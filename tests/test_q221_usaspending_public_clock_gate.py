from automation import q221_usaspending_public_clock_gate as gate

def test_q221_clock_gate(tmp_path,monkeypatch):
    monkeypatch.setattr(gate, "fetch", lambda url: (200,"application/pdf",b"fixture") if url==gate.ABOUT else (200,"text/html",b"/api/v2/transactions/"))
    monkeypatch.setattr(gate, "extract", lambda body: "Frequency of Updates to Prime Award Data for Contracts within five days. Contract award or modification. three business days to FPDS. made available to USAspending.gov on the following morning. automatically published to the website the day after that. DOD and USACE data are delayed 90 days. FAR within 30 days.")
    r=gate.run(tmp_path/"r.json")
    assert r["source_clock_contract_ready"] is True
    assert r["clock_readiness_scope"] == "CURRENT_DOCUMENTATION_ONLY"
    assert r["historical_applicability_proven"] is False
    assert r["historical_boundary_verified"] is False
    assert r["transaction_class_clock_boundaries_verified"] is False
    assert r["rd_classifier_versioned"] is False
    assert r["recipient_to_issuer_mapping_verified"] is False
    assert r["far_30_day_exception_language_found"] is True
    assert r["performance_authorization"] is False