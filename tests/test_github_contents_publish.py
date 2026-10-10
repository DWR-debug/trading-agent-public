import urllib.error

from automation import github_contents_publish as publisher


class _Response:
    def __init__(self, body=b'{"ok":true}'):
        self.body = body
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False
    def read(self):
        return self.body


def test_api_retries_transient_http_error(monkeypatch):
    import json
    calls = []
    def fake_urlopen(req, timeout):
        calls.append((req.get_method(), timeout))
        if len(calls) == 1:
            raise urllib.error.HTTPError(req.full_url, 503, "retry", {}, None)
        return _Response(json.dumps({"sha": "abc"}).encode())
    monkeypatch.setenv("GH_TOKEN", "test-token")
    monkeypatch.setattr(publisher.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(publisher.time, "sleep", lambda *_args: None)
    result = publisher.api("POST", "https://api.github.com/repos/example/repo/git/trees", {"tree": []})
    assert result == {"sha": "abc"}
    assert len(calls) == 2
    assert calls[0][1] == 45


def test_large_blob_api_call_has_bounded_longer_timeout_and_retries_network_reset(monkeypatch):
    import json
    calls = []
    def fake_urlopen(req, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            raise OSError("connection reset by peer")
        return _Response(json.dumps({"sha": "blob-sha"}).encode())
    monkeypatch.setenv("GH_TOKEN", "test-token")
    monkeypatch.setattr(publisher.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(publisher.time, "sleep", lambda *_args: None)
    result = publisher.api("POST", "https://api.github.com/repos/example/repo/git/blobs", {"content": "x" * 100, "encoding": "utf-8"})
    assert result == {"sha": "blob-sha"}
    assert calls == [120, 120]
