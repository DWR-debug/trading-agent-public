import json
from pathlib import Path

import pytest

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


def test_action_date_partitions_archive_fiscal_year_only():
    targets, errors = probe._parse_manifest(_manifest(
        _key("2019-09-30"), _key("2019-10-01", "FA000020C0002")
    ))

    assert errors == []
    assert sorted(targets) == [2019, 2020]
    assert targets[2019] == {_key("2019-09-30")}
    assert targets[2020] == {_key("2019-10-01", "FA000020C0002")}

    # The archive partition is based on action date only; the manifest parser
    # does not derive or assert a public-observation timestamp.
    assert probe.API_URL.endswith("/api/v2/bulk_download/list_monthly_files/")


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
        _archive("FY2022_All_Contracts_Full_20220701.zip", "2022-07-01"),
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


def test_untrusted_archive_host_invalidates_inventory(tmp_path, monkeypatch):
    source = tmp_path / "input.json"
    output = tmp_path / "out.json"
    source.write_text(json.dumps(_manifest(_key("2020-02-11"))), encoding="utf-8")
    rows = [
        _archive("FY2020_All_Contracts_Full_20210101.zip", "2021-01-01"),
        {
            **_archive("FY2020_All_Contracts_Full_20210601.zip", "2021-06-01"),
            "url": "https://example.invalid/archive.zip",
        },
    ]
    monkeypatch.setattr(
        probe, "request_inventory",
        lambda _fy: (200, "application/json", json.dumps({"monthly_files": rows}).encode(),
                     {"monthly_files": rows}),
    )

    receipt = probe.run(source, output)

    assert receipt["status"] == "ARCHIVE_LISTING_INCOMPLETE"
    assert receipt["fiscal_year_results"][0]["invalid_item_count"] == 1
    assert receipt["historical_first_public_observation_proven"] is False
    assert receipt["performance_authorization"] is False


def test_frozen_inventory_request_matches_exact_q221_manifest():
    root = Path(__file__).resolve().parents[1]
    request_path = root / "research/run_requests/q221_monthly_archive_inventory.trigger"
    manifest_path = root / probe.FROZEN_MANIFEST_PATH

    validated = probe.validate_request(request_path, manifest_path)

    assert validated["request_valid"] is True
    assert validated["source_manifest_git_blob_sha"] == probe.FROZEN_MANIFEST_GIT_BLOB_SHA
    assert validated["source_manifest_receipt_fingerprint"] == probe.FROZEN_MANIFEST_RECEIPT_FINGERPRINT
    assert validated["target_key_count"] == 348
    assert validated["target_fiscal_years"] == [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    assert validated["target_key_counts_by_fiscal_year"] == {
        "2019": 49, "2020": 50, "2021": 50, "2022": 50,
        "2023": 50, "2024": 49, "2025": 50,
    }


def test_frozen_inventory_request_rejects_manifest_mutation(tmp_path):
    root = Path(__file__).resolve().parents[1]
    request_path = root / "research/run_requests/q221_monthly_archive_inventory.trigger"
    source = root / probe.FROZEN_MANIFEST_PATH
    changed = tmp_path / source.name
    changed.write_bytes(source.read_bytes() + b" ")

    with pytest.raises(ValueError, match="Q221_SOURCE_MANIFEST_GIT_BLOB_SHA_MISMATCH"):
        probe.validate_request(request_path, changed)


def test_frozen_inventory_request_rejects_safety_flag_or_unknown_key(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source_request = root / "research/run_requests/q221_monthly_archive_inventory.trigger"
    source_manifest = root / probe.FROZEN_MANIFEST_PATH
    original = source_request.read_text(encoding="utf-8")
    changed = tmp_path / source_request.name
    changed.write_text(original.replace("PERFORMANCE=false", "PERFORMANCE=true"), encoding="utf-8")

    with pytest.raises(ValueError, match="Q221_REQUEST_VALUE_MISMATCH:PERFORMANCE"):
        probe.validate_request(changed, source_manifest)

    changed.write_text(original + "UNEXPECTED_KEY=false\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Q221_REQUEST_KEY_SET_MISMATCH"):
        probe.validate_request(changed, source_manifest)



def test_preregistered_negative_inventory_is_success_but_incomplete_results_fail_closed():
    assert probe.exit_code_for_status("DATED_ARCHIVE_SERIES_FOUND") == 0
    # This is the frozen H0 decision: work completed, route stops, no PIT gate opens.
    assert probe.exit_code_for_status("ARCHIVE_LISTING_OK_NO_VERSION_SERIES_FOUND") == 0
    for status in (
        "ARCHIVE_LISTING_EMPTY",
        "ARCHIVE_LISTING_INCOMPLETE",
        "REQUEST_REJECTED",
        "FIXED_TRANSACTION_MANIFEST_INVALID",
        "",
    ):
        assert probe.exit_code_for_status(status) == 2

def test_request_inventory_retries_one_transient_500_then_preserves_attempt_history(monkeypatch):
    import io
    import urllib.error

    calls = []
    sleeps = []

    def fake_request(fiscal_year):
        calls.append(fiscal_year)
        if len(calls) == 1:
            raise urllib.error.HTTPError(
                probe.API_URL, 500, "server error", {}, io.BytesIO(b"temporary failure")
            )
        body = b'{"monthly_files":[]}'
        return 200, "application/json", body, {"monthly_files": []}

    result, attempts = probe.request_inventory_with_retry(
        2019, request_fn=fake_request, sleep_fn=sleeps.append
    )

    assert calls == [2019, 2019]
    assert sleeps == [probe.REQUEST_RETRY_BACKOFF_SECONDS]
    assert result[0] == 200
    assert [item["status"] for item in attempts] == ["FAILED", "SUCCESS"]
    assert attempts[0]["http_status"] == 500
    assert attempts[0]["transient"] is True
    assert attempts[1]["http_status"] == 200


def test_request_inventory_does_not_retry_malformed_or_permanent_http_failures():
    import io
    import urllib.error

    calls = []

    def bad_request(_fiscal_year):
        calls.append(1)
        raise urllib.error.HTTPError(
            probe.API_URL, 400, "bad request", {}, io.BytesIO(b"bad request")
        )

    with pytest.raises(probe._InventoryRequestFailure) as raised:
        probe.request_inventory_with_retry(
            2019, request_fn=bad_request, sleep_fn=lambda _delay: None
        )

    assert len(calls) == 1
    assert raised.value.http_status == 400
    assert raised.value.transient is False
    assert len(raised.value.attempts) == 1


def test_run_opens_source_circuit_after_three_consecutive_transient_year_failures(
    tmp_path, monkeypatch
):
    import io
    import urllib.error

    source = tmp_path / "input.json"
    output = tmp_path / "out.json"
    keys = [
        _key(f"{year - 1}-11-01", f"FA{year:08d}C0001")
        for year in range(2019, 2026)
    ]
    source.write_text(json.dumps(_manifest(*keys)), encoding="utf-8")
    calls = []

    def always_500(fiscal_year):
        calls.append(fiscal_year)
        raise urllib.error.HTTPError(
            probe.API_URL, 500, "server error", {}, io.BytesIO(b"temporary failure")
        )

    monkeypatch.setattr(probe, "request_inventory", always_500)
    monkeypatch.setattr(probe.time, "sleep", lambda _delay: None)

    receipt = probe.run(source, output)

    assert receipt["status"] == "ARCHIVE_LISTING_INCOMPLETE"
    assert receipt["source_circuit_breaker_open"] is True
    assert receipt["api_request_count"] == 6
    assert receipt["api_requests_skipped_after_circuit_breaker"] == 4
    assert calls == [2019, 2019, 2020, 2020, 2021, 2021]
    rows = receipt["fiscal_year_results"]
    assert len(rows) == 7
    assert [row["fiscal_year"] for row in rows] == list(range(2019, 2026))
    assert all(row["status"] == "REQUEST_OR_JSON_PARSE_FAILED" for row in rows[:3])
    assert all(row["status"] == "SKIPPED_AFTER_TRANSIENT_SOURCE_ERRORS" for row in rows[3:])
    assert receipt["archive_transaction_presence_tested"] is False
    assert receipt["historical_first_public_observation_proven"] is False
    assert receipt["performance_authorization"] is False
    assert receipt["live_execution"] is False

