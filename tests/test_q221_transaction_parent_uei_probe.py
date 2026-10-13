from automation import q221_transaction_parent_uei_probe as probe


def test_seven_transaction_keys_are_unique_and_frozen():
    assert len(probe.SAMPLES)==7
    assert len({x[0] for x in probe.SAMPLES})==7
    assert len({x[1] for x in probe.SAMPLES})==7
    assert probe.MAX_ROWS==10000 and probe.MAX_ZIP==20_000_000
    assert probe.FROZEN["APPLY_HISTORICAL_MAPPING"]=="false"


def test_download_query_uses_exact_award_ids_and_action_dates():
    filters={"award_ids":[f'"{s[1]}"' for s in probe.SAMPLES],"time_period":[{"start_date":s[3],"end_date":s[3],"date_type":"action_date"} for s in probe.SAMPLES]}
    assert len(filters["award_ids"])==7 and len(filters["time_period"])==7
    assert all(x["start_date"]==x["end_date"] for x in filters["time_period"])

import io
import urllib.error

import pytest


class _Response:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit=-1):
        return self.body if limit < 0 else self.body[:limit]


def test_api_retries_transient_503_with_bounded_attempts(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, timeout))
        if len(calls) == 1:
            raise urllib.error.HTTPError(request.full_url, 503, "Unavailable", {}, io.BytesIO(b""))
        return _Response(b'{"calculated_count":7}')

    sleeps = []
    monkeypatch.setattr(probe.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(probe.time, "sleep", sleeps.append)

    payload, byte_count = probe.api("https://api.usaspending.gov/api/v2/download/count/", {"probe": True})

    assert payload == {"calculated_count": 7}
    assert byte_count == len(b'{"calculated_count":7}')
    assert len(calls) == 2
    assert sleeps == [1]


def test_api_does_not_retry_nontransient_http_errors(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, io.BytesIO(b"bad request"))

    monkeypatch.setattr(probe.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(probe.time, "sleep", lambda _: None)

    with pytest.raises(probe.ProbeError, match=r"API_HTTP_ERROR:400"):
        probe.api("https://api.usaspending.gov/api/v2/download/count/", {"probe": True})

    assert len(calls) == 1


def test_incomplete_receipt_is_fingerprinted_and_non_authorizing():
    request = {"REQUEST_SEQUENCE": "2026-10-13T16:23:00Z"}
    receipt = probe.incomplete_receipt(request, probe.ProbeError("API_HTTP_ERROR:503:"))

    assert receipt["status"] == "TRANSACTION_PARENT_UEI_PROBE_INCOMPLETE"
    assert receipt["request_sequence"] == request["REQUEST_SEQUENCE"]
    assert receipt["receipt_fingerprint"] == probe.fp(receipt)
    assert receipt["gate_positive"] is False
    assert receipt["historical_parent_lineage_proven"] is False
    assert receipt["recipient_to_issuer_mapping_frozen"] is False
    assert receipt["historical_first_public_observation_proven"] is False
    assert receipt["performance_authorization"] is False
    assert receipt["live_execution"] is False
    assert receipt["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }

import sys


def test_main_writes_a_valid_incomplete_receipt_after_probe_error(monkeypatch, tmp_path):
    output = tmp_path / "receipt.json"
    monkeypatch.setattr(probe, "read_request", lambda _path: {"REQUEST_SEQUENCE": "2026-10-13T16:23:00Z"})

    def fail_probe(*_args):
        raise probe.ProbeError("API_HTTP_ERROR:503:")

    monkeypatch.setattr(probe, "main_run", fail_probe)
    monkeypatch.setattr(sys, "argv", ["q221-probe", "--request", "request.trigger", "--source", "source.json", "--profile-map", "profile.json", "--output", str(output)])

    assert probe.main() == 2
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["status"] == "TRANSACTION_PARENT_UEI_PROBE_INCOMPLETE"
    assert receipt["receipt_fingerprint"] == probe.fp(receipt)
    assert receipt["gate_positive"] is False
