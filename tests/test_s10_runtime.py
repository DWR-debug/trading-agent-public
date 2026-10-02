from pathlib import Path

from automation.s10_runtime import load_descriptor


def test_s10_descriptor_is_fail_closed_and_loopback_only(tmp_path: Path):
    path = tmp_path / "s10_interface.json"
    path.write_text(
        '{"schema_version":1,"enabled":true,"mode":"systemone_http","base_url":"http://127.0.0.1:8765","model":"s10-local"}',
        encoding="utf-8",
    )
    result = load_descriptor(path)
    assert result["available"] is True
    assert result["protocol_path"] == "/v1/systemone"


def test_s10_descriptor_rejects_remote_or_secret_bearing_config(tmp_path: Path):
    remote = tmp_path / "remote.json"
    remote.write_text(
        '{"schema_version":1,"enabled":true,"mode":"systemone_http","base_url":"https://example.com","model":"x"}',
        encoding="utf-8",
    )
    assert load_descriptor(remote)["status"] == "S10_DESCRIPTOR_INVALID"

    secret = tmp_path / "secret.json"
    secret.write_text(
        '{"schema_version":1,"enabled":true,"mode":"systemone_http","base_url":"http://127.0.0.1:8765","model":"x","api_key":"dont-store"}',
        encoding="utf-8",
    )
    assert load_descriptor(secret)["status"] == "S10_DESCRIPTOR_INVALID"


def test_s10_descriptor_is_bom_tolerant_and_disableable(tmp_path: Path):
    path = tmp_path / "s10_interface.json"
    path.write_text(
        '\ufeff{"schema_version":1,"enabled":false,"mode":"systemone_http","base_url":"http://127.0.0.1:8765","model":"x"}',
        encoding="utf-8",
    )
    assert load_descriptor(path)["status"] == "S10_DISABLED"


def test_s10_descriptor_accepts_custom_local_protocol_path(tmp_path: Path):
    path = tmp_path / "s10_interface.json"
    path.write_text(
        '{"schema_version":1,"enabled":true,"mode":"systemone_http","base_url":"http://localhost:8765","model":"s10-local","protocol_path":"/api/systemone"}',
        encoding="utf-8",
    )
    result = load_descriptor(path)
    assert result["available"] is True
    assert result["protocol_path"] == "/api/systemone"
