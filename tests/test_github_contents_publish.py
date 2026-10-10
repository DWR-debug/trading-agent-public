from __future__ import annotations

import importlib
from pathlib import Path


def test_publish_retries_concurrent_fast_forward(monkeypatch, tmp_path) -> None:
    module = importlib.import_module("automation.github_contents_publish")
    payload = tmp_path / "evidence.json"
    payload.write_text('{"status":"ok"}\n', encoding="utf-8")

    base1 = "1" * 40
    base2 = "2" * 40
    commit1 = "c" * 40
    commit2 = "d" * 40
    tree1 = "e" * 40
    tree2 = "f" * 40
    blob1 = "a" * 40
    blob2 = "b" * 40

    patch_attempts = {"count": 0}
    ref_reads = {"count": 0}

    def fake_api(method, url, request=None):
        if method == "GET" and url.endswith("/git/ref/heads/master"):
            ref_reads["count"] += 1
            return {"object": {"sha": base1 if ref_reads["count"] == 1 else base2}}
        if method == "GET" and f"/git/commits/{base1}" in url:
            return {"tree": {"sha": tree1}}
        if method == "GET" and f"/git/commits/{base2}" in url:
            return {"tree": {"sha": tree2}}
        if method == "POST" and url.endswith("/git/blobs"):
            return {"sha": blob1 if patch_attempts["count"] == 0 else blob2}
        if method == "POST" and url.endswith("/git/trees"):
            return {"sha": tree1 if patch_attempts["count"] == 0 else tree2}
        if method == "POST" and url.endswith("/git/commits"):
            return {"sha": commit1 if patch_attempts["count"] == 0 else commit2}
        if method == "PATCH" and url.endswith("/git/refs/heads/master"):
            patch_attempts["count"] += 1
            if patch_attempts["count"] == 1:
                raise RuntimeError("GitHub API PATCH failed: 422: Update is not a fast forward")
            return {"ok": True}
        raise AssertionError(f"Unexpected API call: {method} {url}")

    monkeypatch.setattr(module, "api", fake_api)

    result = module.publish(
        "DWR-debug/trading-agent-public",
        "master",
        base1,
        [("research/evidence/test.json", str(payload))],
    )

    assert result == commit2
    assert patch_attempts["count"] == 2
    assert ref_reads["count"] == 2



def test_api_retries_transient_502(monkeypatch):
    module = importlib.import_module("automation.github_contents_publish")
    calls = {"count": 0}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(req, timeout=30):
        calls["count"] += 1
        if calls["count"] < 3:
            raise __import__("urllib.error").error.HTTPError(
                req.full_url, 502, "Bad Gateway", {}, None
            )
        return FakeResponse()

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    monkeypatch.setenv("GH_TOKEN", "test-token")
    assert module.api("GET", "https://api.github.com/test") == {"ok": True}
    assert calls["count"] == 3

def test_publish_resolves_latest_branch_head_without_external_cli(monkeypatch, tmp_path) -> None:
    module = importlib.import_module("automation.github_contents_publish")
    payload = tmp_path / "evidence.json"
    payload.write_text('{"status":"ok"}\\n', encoding="utf-8")

    base = "1" * 40
    tree = "2" * 40
    blob = "3" * 40
    commit = "4" * 40
    calls = []

    def fake_api(method, url, request=None):
        calls.append((method, url))
        if method == "GET" and url.endswith("/git/ref/heads/master"):
            return {"object": {"sha": base}}
        if method == "GET" and url.endswith(f"/git/commits/{base}"):
            return {"tree": {"sha": tree}}
        if method == "POST" and url.endswith("/git/blobs"):
            return {"sha": blob}
        if method == "POST" and url.endswith("/git/trees"):
            return {"sha": "5" * 40}
        if method == "POST" and url.endswith("/git/commits"):
            return {"sha": commit}
        if method == "PATCH" and url.endswith("/git/refs/heads/master"):
            return {"ok": True}
        raise AssertionError(f"Unexpected API call: {method} {url}")

    monkeypatch.setattr(module, "api", fake_api)
    result = module.publish(
        "DWR-debug/trading-agent-public",
        "master",
        "latest",
        [("research/evidence/test.json", str(payload))],
    )

    assert result == commit
    assert calls[0] == (
        "GET",
        "https://api.github.com/repos/DWR-debug/trading-agent-public/git/ref/heads/master",
    )
    assert calls[-1][0] == "PATCH"

