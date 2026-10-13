import io
import json
import urllib.error

import pytest

from automation.wayback_cdx_metadata import MetadataProbeError, build_cdx_url, fetch_bounded, parse_cdx_rows


def test_build_cdx_url_pins_exact_original_and_caps():
    url = build_cdx_url("https://example.org/data.txt", from_year=2020, to_year=2026, limit=10)
    assert url.startswith("https://web.archive.org/cdx/search/cdx?")
    assert "matchType=exact" in url and "limit=10" in url


def test_parse_empty_cdx_is_valid_negative():
    assert parse_cdx_rows(b"[]") == []


def test_parse_cdx_validates_timestamp_status_and_exact_url():
    body = json.dumps([["timestamp","original","statuscode","digest","length"],["20240722180837","https://example.org/data.txt","200","ABC","12"]]).encode()
    assert parse_cdx_rows(body, expected_original="https://example.org/data.txt")[0]["digest"] == "ABC"
    with pytest.raises(MetadataProbeError, match="CDX_CAPTURE_URL_MISMATCH"):
        parse_cdx_rows(body, expected_original="https://example.org/other.txt")


def test_parse_cdx_rejects_malformed_metadata():
    body = json.dumps([["timestamp","original","statuscode","digest","length"],["bad","https://example.org/data.txt","200","ABC","12"]]).encode()
    with pytest.raises(MetadataProbeError, match="CDX_TIMESTAMP_INVALID"):
        parse_cdx_rows(body)


class Response:
    status=200
    headers={"Content-Type":"application/json"}
    def __init__(self, body): self.stream=io.BytesIO(body)
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n=-1): return self.stream.read(n)


def test_fetch_enforces_request_and_byte_caps_without_retry():
    state={"request_count":0,"metadata_download_bytes":0}
    def opener(*args,**kwargs): return Response(b"[]")
    status,body,_=fetch_bounded("https://web.archive.org/cdx/search/cdx?x=1",max_requests=1,max_response_bytes=10,max_total_bytes=10,state=state,opener=opener)
    assert (status,body)==(200,b"[]")
    with pytest.raises(MetadataProbeError,match="REQUEST_COUNT_CAP_EXCEEDED"):
        fetch_bounded("https://web.archive.org/cdx/search/cdx?x=2",max_requests=1,max_response_bytes=10,max_total_bytes=10,state=state,opener=opener)


def test_non_wayback_payload_urls_are_forbidden():
    with pytest.raises(MetadataProbeError,match="NON_ARCHIVE_URL_FORBIDDEN"):
        fetch_bounded("https://cdn.finra.org/file.txt",max_requests=1,max_response_bytes=10,max_total_bytes=10,state={})
