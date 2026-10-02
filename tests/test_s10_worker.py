from pathlib import Path

from automation import s10_worker


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b'{"answers":{"verdict":{"choice":"SUPPORTED","probabilities":{"SUPPORTED":1.0,"REFUTED":0.0,"INSUFFICIENT":0.0}}}}'


def test_s10_endpoint_smoke_validates_typed_decision(monkeypatch):
    monkeypatch.setattr(s10_worker.urllib.request, "urlopen", lambda request, timeout: _Response())
    result = s10_worker._endpoint_smoke(
        {
            "base_url": "http://127.0.0.1:8765",
            "protocol_path": "/v1/systemone",
        }
    )
    assert result["status"] == "PASS"
    assert result["probabilities_contract_valid"] is True


def test_s10_endpoint_smoke_fails_closed_on_transport_error(monkeypatch):
    def fail(request, timeout):
        raise TimeoutError("smoke timeout")

    monkeypatch.setattr(s10_worker.urllib.request, "urlopen", fail)
    result = s10_worker._endpoint_smoke(
        {
            "base_url": "http://127.0.0.1:8765",
            "protocol_path": "/v1/systemone",
        }
    )
    assert result["status"] == "FAIL_ENDPOINT_UNAVAILABLE"


def test_s10_worker_source_contains_bounded_preflight():
    text = Path("automation/s10_worker.py").read_text(encoding="utf-8")
    assert "_endpoint_smoke" in text
    assert isinstance(s10_worker.SMOKE_TIMEOUT_SECONDS, int)
    assert 0 < s10_worker.SMOKE_TIMEOUT_SECONDS <= 60
    assert "worker_output_is_scientific_evidence" in text
