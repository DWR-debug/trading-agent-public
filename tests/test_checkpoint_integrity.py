import json

import pytest

from automation.checkpoint import ResearchCheckpointStore, checkpoint_fingerprint


def test_checkpoint_fingerprint_is_deterministic():
    state = {"run_fingerprint": "abc", "results": [{"value": 1}]}
    assert checkpoint_fingerprint(state) == checkpoint_fingerprint(dict(state))


def test_checkpoint_store_adds_and_verifies_fingerprint(tmp_path):
    path = tmp_path / "checkpoint.json"
    store = ResearchCheckpointStore(path)
    store.save({"run_fingerprint": "abc", "status": "RUNNING"})
    loaded = store.load()
    assert loaded["checkpoint_fingerprint"] == checkpoint_fingerprint(loaded)


def test_checkpoint_store_rejects_tampering(tmp_path):
    path = tmp_path / "checkpoint.json"
    store = ResearchCheckpointStore(path)
    store.save({"run_fingerprint": "abc", "status": "RUNNING"})
    data = json.loads(path.read_text(encoding="utf-8"))
    data["status"] = "COMPLETED"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="gültigen Fingerprint"):
        store.load()
