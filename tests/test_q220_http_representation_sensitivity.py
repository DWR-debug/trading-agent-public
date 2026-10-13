from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation import q220_http_representation_sensitivity as probe

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "research/run_requests/q220_http_representation_sensitivity.trigger"
SOURCE = ROOT / "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json"
SUMMARY = ROOT / "research/evidence/q220_single_feed_boundary_validation_2026_10_13_summary.json"


def response(body: bytes, *, status: str = "FETCHED", http_status: int = 200) -> dict:
    return {
        "status": status,
        "http_status": http_status,
        "requested_url": probe.URL,
        "final_url": probe.URL,
        "response_bytes": len(body),
        "body": body,
        "error_code": None,
        "content_type": "text/html",
        "content_length_header": str(len(body)),
        "content_encoding": None,
        "transfer_encoding": None,
        "etag": '"mock-etag"',
        "last_modified": "Wed, 13 Feb 2019 11:02:53 GMT",
        "date": "Tue, 13 Oct 2026 18:00:00 GMT",
        "server": "mock-sec",
        "accept_ranges": "bytes",
    }


def test_registered_request_and_frozen_sources_validate_exactly():
    request = probe.read_request(REQUEST)
    source, summary = probe.validate_sources(SOURCE, SUMMARY, request)
    assert request["MAX_REQUESTS"] == "5"
    assert source["receipt_fingerprint"] == probe.SOURCE_RECEIPT_FINGERPRINT
    assert summary["upstream_receipt_fingerprint"] == probe.SINGLE_SUMMARY_UPSTREAM_RECEIPT_FINGERPRINT


def test_header_contrasts_change_one_profile_dimension_at_a_time():
    first, user_agent_only, accept_only, combined, repeat = probe.PROFILES
    h_first = probe.request_headers(first)
    h_user_agent = probe.request_headers(user_agent_only)
    h_accept = probe.request_headers(accept_only)
    h_combined = probe.request_headers(combined)
    h_repeat = probe.request_headers(repeat)

    assert h_first["Accept"] == h_user_agent["Accept"] == probe.ACCEPT_POPULATION
    assert h_first["User-Agent"] == h_accept["User-Agent"] == h_repeat["User-Agent"] == probe.UA_POPULATION
    assert h_first["User-Agent"] != h_user_agent["User-Agent"]
    assert h_first["Accept"] != h_accept["Accept"]
    assert h_combined["User-Agent"] == probe.UA_FORENSIC
    assert h_combined["Accept"] == probe.ACCEPT_FORENSIC
    assert all(row["Accept-Encoding"] == "identity" for row in (h_first, h_user_agent, h_accept, h_combined, h_repeat))


def test_profile_variation_is_detected_but_never_opens_q220_gate(tmp_path):
    calls: list[tuple[str, dict[str, str]]] = []

    def fetcher(url, headers, max_bytes, timeout_seconds):
        calls.append((url, dict(headers)))
        body = b"stable-body"
        if headers["User-Agent"] == probe.UA_PIT:
            body = b"stable-body-pit-ua"
        elif headers["Accept"] == probe.ACCEPT_PIT:
            body = b"stable-body-pit-accept"
        elif headers["User-Agent"] == probe.UA_FORENSIC:
            body = b"stable-body-forensic"
        return response(body)

    output = tmp_path / "receipt.json"
    result = probe.run(REQUEST, SOURCE, SUMMARY, output, fetcher=fetcher, sleep_fn=lambda _seconds: None)
    persisted = json.loads(output.read_text(encoding="utf-8"))

    assert len(calls) == probe.MAX_REQUESTS
    assert all(url == probe.URL for url, _headers in calls)
    assert result["status"] == "HTTP_REPRESENTATION_VARIATION_OBSERVED"
    assert result["completed_request_count"] == 5
    assert result["comparison"]["user_agent_only_body_differs"] is True
    assert result["comparison"]["accept_only_body_differs"] is True
    assert result["comparison"]["forensic_combined_body_differs"] is True
    assert result["comparison"]["baseline_repeat_stable"] is True
    assert result["gate_positive"] is False
    assert result["performance_authorization"] is False
    assert result["live_execution"] is False
    serialized = json.dumps(persisted)
    assert "stable-body-pit-ua" not in serialized
    assert "stable-body-forensic" not in serialized
    assert '"body":' not in serialized
    assert persisted["receipt_fingerprint"] == probe.canonical_fingerprint(persisted)


def test_identical_profiles_are_reported_as_probe_time_invariant_not_as_pit_pass(tmp_path):
    calls = 0

    def fetcher(url, headers, max_bytes, timeout_seconds):
        nonlocal calls
        calls += 1
        return response(b"same-response-for-every-profile")

    result = probe.run(REQUEST, SOURCE, SUMMARY, tmp_path / "receipt.json", fetcher=fetcher, sleep_fn=lambda _seconds: None)
    assert calls == 5
    assert result["status"] == "HTTP_REPRESENTATION_INVARIANT_AT_PROBE_TIME"
    assert result["comparison"]["baseline_repeat_stable"] is True
    assert result["comparison"]["profile_body_differences_observed"] == 0
    assert result["gate_positive"] is False
    assert result["scientific_evidence"] is False


def test_baseline_repeat_difference_is_detected_independently_of_profile_effects(tmp_path):
    calls = 0

    def fetcher(url, headers, max_bytes, timeout_seconds):
        nonlocal calls
        calls += 1
        return response(b"baseline-A" if calls < 5 else b"baseline-B")

    result = probe.run(REQUEST, SOURCE, SUMMARY, tmp_path / "receipt.json", fetcher=fetcher, sleep_fn=lambda _seconds: None)
    assert result["status"] == "HTTP_REPRESENTATION_VARIATION_OBSERVED"
    assert result["comparison"]["baseline_repeat_stable"] is False
    assert result["comparison"]["baseline_repeat_body_differs"] is True
    assert result["gate_positive"] is False


def test_incomplete_http_response_fails_closed_after_bounded_requests(tmp_path):
    calls = 0

    def fetcher(url, headers, max_bytes, timeout_seconds):
        nonlocal calls
        calls += 1
        if calls == 3:
            return response(b"", status="HTTP_ERROR", http_status=503)
        return response(b"small")

    result = probe.run(REQUEST, SOURCE, SUMMARY, tmp_path / "receipt.json", fetcher=fetcher, sleep_fn=lambda _seconds: None)
    assert calls == 5
    assert result["status"] == "HTTP_REPRESENTATION_PROBE_INCOMPLETE"
    assert result["comparison"]["all_responses_complete_http_200"] is False
    assert result["gate_positive"] is False


def test_mismatched_request_fails_before_any_http_call(tmp_path):
    original = REQUEST.read_text(encoding="utf-8")
    bad_request = tmp_path / "bad.trigger"
    bad_request.write_text(original.replace("LIVE_EXECUTION=false", "LIVE_EXECUTION=true"), encoding="utf-8")
    calls = []

    def fetcher(*_args):
        calls.append(True)
        return response(b"never-called")

    result = probe.run(bad_request, SOURCE, SUMMARY, tmp_path / "receipt.json", fetcher=fetcher, sleep_fn=lambda _seconds: None)
    assert result["status"] == "SOURCE_VALIDATION_REJECTED"
    assert result["request_validation_passed"] is False
    assert calls == []
