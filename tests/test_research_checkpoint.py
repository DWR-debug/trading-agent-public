from automation.checkpoint import ResearchCheckpointStore, checkpoint_key


def test_checkpoint_roundtrip(tmp_path):
    path = tmp_path / "checkpoint.json"
    store = ResearchCheckpointStore(path)

    store.save({
        "status": "RUNNING",
        "completed": ["BTCUSDT::1h"],
    })

    loaded = store.load()

    assert loaded["status"] == "RUNNING"
    assert loaded["completed"] == ["BTCUSDT::1h"]
    assert "updated_at" in loaded


def test_checkpoint_load_missing_returns_none(tmp_path):
    assert ResearchCheckpointStore(
        tmp_path / "missing.json"
    ).load() is None


def test_checkpoint_key_normalizes_symbol():
    assert checkpoint_key("btcusdt", "1h") == "BTCUSDT::1h"
