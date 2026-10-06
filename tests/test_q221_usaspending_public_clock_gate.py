from automation import q221_usaspending_public_clock_gate as gate

def test_q221_clock_gate(tmp_path,monkeypatch):
    monkeypatch.setattr(gate, "fetch", lambda url: (200,"application/pdf",b"fixture") if url==gate.ABOUT else (200,"text/html",b"/api/v2/transactions/"))
    monkeypatch.setattr(gate, "extract", lambda body: "Frequency of Updates to Prime Award Data for Contracts within five days. Contract award or modification. three business days to FPDS. made available to USAspending.gov on the following morning. automatically published to the website the day after that. DOD and USACE data are delayed 90 days. FAR.")
    r=gate.run(tmp_path/"r.json")
    assert r["source_clock_contract_ready"] is True
    assert r["historical_applicability_proven"] is False
    assert r["performance_authorization"] is False