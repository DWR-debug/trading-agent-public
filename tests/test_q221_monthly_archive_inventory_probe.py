import hashlib
import json
from datetime import date
from pathlib import Path

from automation import q221_monthly_archive_inventory_probe as probe


def _key(action_date: str, award: str = "FA000019C0001") -> str:
    return f"{award}|P00001|{action_date}|transaction-id|RECIPIENT01"


def _manifest(*keys: str) -> dict:
    return {"queries": [{"selected_transaction_keys": list(keys)}]}


def _archive(name: str, updated: str) -> dict:
    return {
        "file_name": name,
        "updated_date": updated,
        "url": f"https://files.usaspending.gov/archive/{name}",
        "type": "contracts",
    }


def test_action_date_partitions_archive_fiscal_year_only(tmp_path, monkeypatch):
    targets, errors = probe._parse_manifest(_manifest(
        _key("2019-09-30"), _key("2019-10-01", "FA000020C0002")
    ))

    assert errors == []
    assert sorted(targets) == [2019, 2020]
    assert targets[2019] == {_key("2019-09-30")}
    assert targets[2020] == {_key("2019-10-01", "FA000020C0002")}

    # The probe never promotes action date into a public-observation clock.
    receipt = probe.run_pathless_manifest_for_test if hasattr(probe, "run_pathless_manifest_for_test") else None
    assert probe.API_URL.endswith("/api/v2/bulk_download/list_monthly_files/")
    assert receipt is None


def test_dated_archive_series_is_only_a_candidate_not_a_public_clock(tmp_path, monkeypatch):
    source = tmp_path / "input.json"
    output = tmp_path / "out.json"
    source.write_text(json.dumps(_manifest(_key("2019-01-03"))), encoding="utf-8")
    rows = [
        _archive("FY2019_All_Contracts_Full_20200101.zip", "2020-01-01"),
        _archive("FY2019_All_Contracts_Full_20200601.zip", "2020-06-01"),
        _archive("FY(All)_All_Contracts_Delta_20200601.zip", "2020-06-01"),
        _archive("FY(All)_All_Contracts_Delta_20200701.zip", "2020-07-01"),
    ]

    def fake_request(fiscal_year):
        assert fiscal_year == 2019
        body = json.dumps({"monthly_files": rows}).encode()
        return 200, "application/json", body, {"monthly_files": rows}

    monkeypatch.setattr(probe, "request_inventory", fake_request)
    receipt = probe.run(source, output)

    assert receipt["status"] == "DATED_ARCHIVE_SERIES_FOUND"
    assert receipt["dated_archive_series_found"] is True
    assert receipt["full_archive_count"] == 2
    assert receipt["delta_archive_count"] == 2
    assert receipt["archive_transaction_presence_tested"] is False
    assert receipt["archive_transaction_absence_tested"] is False
    assert receipt["historical_first_public_observation_proven"] is False
    assert receipt["event_level_public_boundary_proven"] is False
    assert receipt["scientific_evidence"] is False
    assert receipt["performance_authorization"] is False
    assert receipt["live_execution"] is False
    assert len(receipt["receipt_fingerprint"]) == 64
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["receipt_fingerprint"] == receipt["receipt_fingerprint"]


def test_empty_inventory_is_blocked_and_never_sets_pit_gate(tmp_path, monkeypatch):
    source = tmp_path / "input.json"
    output = tmp_path / "out.json"
    source.write_text(json.dumps(_manifest(_key("2021-02-11"))), encoding="utf-8")
    monkeypatch.setattr(
        probe, "request_inventory",
        lambda _fy: (200, "application/json", b'{"monthly_files":[]}', {"monthly_files": []}),
    )

    receipt = probe.run(source, output)

    assert receipt["status"] == "ARCHIVE_LISTING_EMPTY"
    assert receipt["dated_archive_series_found"] is False
    assert receipt["historical_first_public_observation_proven"] is False
    assert receipt["performance_authorization"] is False


def test_bad_filename_or_date_mismatch_invalidates_inventory(tmp_path, monkeypatch):
    source = tmp_path / "input.json"
    output = tmp_path / "out.json"
    source.write_text(json.dumps(_manifest(_key("2022-03-02"))), encoding="utf-8")
    rows = [
        _archive("FY2022_All_Contracts_Full_20220101.zip", "2022-01-02"),
        _archive("FY2022_All_Contracts_Full_20220601.zip", "2022-06-01"),
    ]
    monkeypatch.setattr(
        probe, "request_inventory",
        lambda _fy: (200, "application/json", json.dumps({"monthly_files": rows}).encode(),
                     {"monthly_files": rows}),
    )

    receipt = probe.run(source, output)

    assert receipt["status"] == "ARCHIVE_LISTING_INCOMPLETE"
    assert receipt["fiscal_year_results"][0]["invalid_item_count"] == 1
    assert receipt["dated_archive_series_found"] is True
    assert receipt["historical_first_public_observation_proven"] is False


def test_invalid_fixed_manifest_fails_closed_without_network(tmp_path, monkeypatch):
    source = tmp_path / "input.json"
    output = tmp_path / "out.json"
    source.write_text(json.dumps({"queries": [{"selected_transaction_keys": ["award|0|not-a-date"]}]}),
                      encoding="utf-8")

    def must_not_call(_fy):
        raise AssertionError("invalid manifest must stop before the API call")

    monkeypatch.setattr(probe, "request_inventory", must_not_call)
    receipt = probe.run(source, output)

    assert receipt["status"] == "FIXED_TRANSACTION_MANIFEST_INVALID"
    assert receipt["fiscal_year_results"] == []
    assert receipt["historical_first_public_observation_proven"] is False
    assert receipt["performance_authorization"] is False


def test_request_inventory_has_strict_timeout_and_response_limit(monkeypatch):
    class Response:
        status = 200
        headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self, size):
            assert size == probe.MAX_RESPONSE_BYTES + 1
            return b'{"monthly_files":[]}'

    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(probe.urllib.request, "urlopen", fake_urlopen)
    status, content_type, body, decoded = probe.request_inventory(2019)

    assert status == 200
    assert content_type == "application/json"
    assert decoded == {"monthly_files": []}
    assert captured["timeout"] == probe.REQUEST_TIMEOUT_SECONDS
    assert captured["request"].get_method() == "POST"
    assert captured["request"].get_header("Content-type") == "application/json"
    assert json.loads(captured["request"].data.decode()) == {
        "agency": "all", "fiscal_year": 2019, "type": "contracts"
    }
