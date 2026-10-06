from automation import q218_sec_multichannel_source_gate as gate

def test_q218_source_gate_uses_item_2_02_and_is_non_authorizing(tmp_path,monkeypatch):
    import json
    payload={"filings":{"recent":{"form":["10-K","8-K"],"filingDate":["2025-01-02","2025-01-03"],"accessionNumber":["0000320193-25-000001","0000320193-25-000002"],"primaryDocument":["a.htm","b.htm"],"reportDate":["2024-09-28","2024-09-28"],"items":["","2.02,9.01"]}}}
    def fake_fetch(url):
        if "/submissions/CIK" in url:return json.dumps(payload).encode()
        return b"<ACCEPTANCE-DATETIME>20250103120000"
    monkeypatch.setattr(gate,"fetch",fake_fetch)
    r=gate.run(tmp_path/"r.json")
    assert r["issuers_with_10k"]==8
    assert r["issuers_with_item_2_02_8k"]==8
    assert r["all_required_issuer_channels_observed"] is True
    assert r["performance_authorization"] is False
    assert r["next_gate"]=="DETERMINISTIC_10K_8K_EVENT_PAIR_AND_AMENDMENT_LINEAGE"