import base64
import json
from email.message import Message
from unittest.mock import patch

from automation import global_physical_economy_source_probe as probe


class FakeResponse:
    def __init__(self, payload, status=200, headers=None):
        self._payload = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.status = status
        self.headers = Message()
        for key, value in (headers or {"Content-Type": "application/json"}).items():
            self.headers[key] = str(value)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        return self._payload if size < 0 else self._payload[:size]


def test_bounded_fetch_preserves_exact_body_hash_and_bytes():
    body = b'{"ok":true,"n":1}'
    fake = FakeResponse(body, headers={"Content-Type": "application/json", "ETag": '"v1"'})
    with patch.object(probe.urllib.request, "urlopen", return_value=fake):
        record = probe.fetch_bounded_json("fixture", "https://example.test/sample")

    assert record["capture_state"] == "COMPLETE_JSON_HTTP_200"
    assert record["raw_body_sha256"] == probe.sha256_hex(body)
    assert base64.b64decode(record["raw_body_base64"]) == body
    assert record["parsed_json"] == {"ok": True, "n": 1}
    assert record["response_headers"]["etag"] == '"v1"'


def test_over_limit_body_is_not_misrepresented_as_complete_snapshot():
    body = b"x" * (probe.MAX_RESPONSE_BYTES + 1)
    fake = FakeResponse(body, headers={"Content-Type": "application/json"})
    with patch.object(probe.urllib.request, "urlopen", return_value=fake):
        record = probe.fetch_bounded_json("fixture", "https://example.test/large")

    assert record["capture_state"] == "RESPONSE_OVER_BYTE_LIMIT"
    assert record["raw_body_base64"] is None
    assert record["raw_body_sha256"] is None
    assert record["partial_prefix_bytes"] == probe.MAX_RESPONSE_BYTES


def test_source_probe_records_metadata_and_fixed_bounded_samples():
    layer = {
        "isDataVersioned": False,
        "objectIdField": "OBJECTID",
        "editingInfo": {"dataLastEditDate": 1785856779122},
    }
    collection = {
        "id": "sentinel-2-l2a",
        "license": "other",
        "extent": {"temporal": {"interval": [["2015-06-27T10:25:31Z", None]]}},
    }
    row_sample = {"features": [{"attributes": {"OBJECTID": 1}}]}
    item = {
        "type": "Feature",
        "id": "S2A_SAMPLE",
        "collection": "sentinel-2-l2a",
        "properties": {
            "datetime": "2025-10-10T10:00:00Z",
            "created": "2025-10-10T12:00:00Z",
            "updated": "2025-10-11T12:00:00Z",
            "platform": "sentinel-2a",
            "processing:level": "L2A",
            "product:type": "S2MSI2A",
            "eo:cloud_cover": 20,
        },
        "assets": {},
        "links": [],
    }

    def fake_urlopen(request, timeout=0):
        url = request.full_url
        assert timeout == probe.REQUEST_TIMEOUT_SECONDS
        if url == probe.PORTWATCH_LAYER_URL:
            return FakeResponse(layer)
        if url == probe.COPERNICUS_COLLECTION_URL:
            return FakeResponse(collection)
        if url.startswith(probe.PORTWATCH_QUERY_BASE + "?"):
            assert "orderByFields=OBJECTID" in url
            assert "resultRecordCount=3" in url
            return FakeResponse(row_sample)
        if url.startswith(probe.COPERNICUS_SEARCH_URL + "?"):
            assert "limit=2" in url
            assert "sentinel-2-l2a" in url
            return FakeResponse({"type": "FeatureCollection", "features": [item]})
        raise AssertionError(f"Unexpected external request: {url}")

    with patch.object(probe.urllib.request, "urlopen", side_effect=fake_urlopen):
        receipt = probe.build_receipt()

    assert receipt["status"] == "BOUNDED_SOURCES_CAPTURED_PIT_UNPROVEN"
    assert len(receipt["requests"]) == 6
    assert receipt["source_summary"]["portwatch"]["is_data_versioned"] is False
    assert receipt["source_summary"]["portwatch"]["row_query_state"].startswith("REQUESTED")
    assert len(receipt["source_summary"]["copernicus"]["items"]) == 3
    assert all(window["feature_count_returned"] == 1 for window in receipt["source_summary"]["copernicus"]["items"])
    assert receipt["historical_pit_gate"]["gate_pass"] is False
    assert receipt["historical_pit_gate"]["status"] == "NOT_PROVEN"
    assert receipt["safety"] == {
        "PAPER_ONLY": True,
        "LIVE_TRADING_ENABLED": False,
        "ORDERS_ENABLED": False,
        "AUTOMATIC_PROMOTION": False,
    }
    assert all(not request["url"].endswith(".tif") for request in receipt["requests"])


def test_missing_object_id_fails_closed_without_unordered_portwatch_query():
    layer = {"isDataVersioned": False}
    collection = {
        "id": "sentinel-2-l2a",
        "extent": {"temporal": {"interval": [["2015-06-27T10:25:31Z", None]]}},
    }

    def fake_urlopen(request, timeout=0):
        if request.full_url == probe.PORTWATCH_LAYER_URL:
            return FakeResponse(layer)
        if request.full_url == probe.COPERNICUS_COLLECTION_URL:
            return FakeResponse(collection)
        if request.full_url.startswith(probe.COPERNICUS_SEARCH_URL + "?"):
            return FakeResponse({"type": "FeatureCollection", "features": []})
        raise AssertionError("The unordered PortWatch row query must not run")

    with patch.object(probe.urllib.request, "urlopen", side_effect=fake_urlopen):
        receipt = probe.build_receipt()

    assert receipt["status"] == "SOURCE_FETCH_INCOMPLETE_OR_QUERY_BLOCKED"
    assert receipt["source_summary"]["portwatch"]["row_query_state"] == "BLOCKED_OBJECT_ID_FIELD_UNRESOLVED"
    assert receipt["source_summary"]["portwatch"]["is_data_versioned"] is False
    assert receipt["historical_pit_gate"]["gate_pass"] is False


def test_current_success_can_never_set_historical_pit_gate_to_pass():
    source = open(probe.__file__, encoding="utf-8").read().lower()
    assert 'gate_pass": false' in source
    assert '"performance": false' in source
    assert '"live_execution": false' in source
    assert "first public availability" in source
