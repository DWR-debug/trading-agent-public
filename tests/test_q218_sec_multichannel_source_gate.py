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

def test_q218_fetch_retries_transient_timeout_then_succeeds(monkeypatch):
    calls = []
    sleeps = []

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return b"ok"

    def fake_urlopen(req, timeout):
        calls.append(timeout)
        if len(calls) < 3:
            raise TimeoutError("temporary SEC timeout")
        return Response()

    monkeypatch.setattr(gate.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(gate.time, "sleep", sleeps.append)

    assert gate.fetch("https://example.invalid") == b"ok"
    assert calls == [30, 30, 30]
    assert sleeps == [2, 4]


def test_q218_fetch_exhausts_transient_timeouts(monkeypatch):
    calls = []
    sleeps = []

    def fake_urlopen(req, timeout):
        calls.append(timeout)
        raise TimeoutError("persistent SEC timeout")

    monkeypatch.setattr(gate.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(gate.time, "sleep", sleeps.append)

    import pytest
    with pytest.raises(TimeoutError, match="persistent SEC timeout"):
        gate.fetch("https://example.invalid")
    assert calls == [30, 30, 30]
    assert sleeps == [2, 4]
