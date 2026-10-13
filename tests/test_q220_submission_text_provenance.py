from __future__ import annotations

import json
from pathlib import Path

from automation import q220_submission_text_provenance as probe
from automation import q220_primary_source_vintage_forensics as forensic

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "research/run_requests/q220_submission_text_provenance.trigger"
SOURCE = ROOT / "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json"
SUMMARY = ROOT / "research/evidence/q220_single_feed_boundary_validation_2026_10_13_summary.json"


def _submission_text() -> bytes:
    accession = "0000064040-19-000059"
    filename = "spgi-20181231x10k.htm"
    primary = (
        b"<!DOCTYPE html>\r\n<html><body>"
        b"Submission-source mock with trailing bytes preserved."
        b"</body></html>\r\n"
    )
    return (
        b"<SEC-DOCUMENT>0000064040-19-000059.txt : 20190213\n"
        b"<SEC-HEADER>\n"
        + f"<ACCESSION-NUMBER>{accession}\n".encode()
        + b"<FILER>\n<COMPANY-DATA>\n<CIK>0000064040\n</COMPANY-DATA>\n</FILER>\n"
        + b"</SEC-HEADER>\n<TYPE>10-K\n<FILING-DATE>20190213\n"
        + b"<DOCUMENT>\n<TYPE>10-K\n<SEQUENCE>1\n<FILENAME>" + filename.encode()
        + b"\n<TEXT>\r\n" + primary + b"</TEXT>\n</DOCUMENT>\n"
        + b"</SEC-DOCUMENT>\n"
    )


def _index_html() -> bytes:
    return b"""<!DOCTYPE html><html><body><table>
<tr><td>1</td><td>10-K</td><td><a href="spgi-20181231x10k.htm">spgi-20181231x10k.htm</a></td><td>10-K</td><td>4,774,347</td></tr>
<tr><td>2</td><td>Complete submission text file</td><td><a href="0000064040-19-000059.txt">0000064040-19-000059.txt</a></td><td>10-K</td><td>26,429,931</td></tr>
</table></body></html>"""


def test_registered_sources_validate_frozen_q220_inputs():
    request = probe.read_request(REQUEST)
    receipt, summary = probe.validate_sources(SOURCE, SUMMARY, request)
    assert receipt["receipt_fingerprint"] == request["SOURCE_RECEIPT_FINGERPRINT"]
    assert receipt["source_hash_failure_count"] == 55
    assert summary["upstream_receipt_fingerprint"] == request["SINGLE_SUMMARY_UPSTREAM_RECEIPT_FINGERPRINT"]
    assert request["TARGET_RECORD_KEY"] == "0000064040|0000064040-19-000059|10-K|2019-02-13"


def test_filing_index_parser_resolves_exact_unique_rows_and_sizes():
    result = probe.parse_filing_index(
        _index_html(),
        "spgi-20181231x10k.htm",
        "0000064040-19-000059.txt",
    )
    assert result["unique_target_rows"] is True
    assert result["primary"]["index_size_bytes"] == 4774347
    assert result["submission"]["index_size_bytes"] == 26429931
    assert result["primary_match_count"] == 1
    assert result["submission_match_count"] == 1


def test_filing_index_parser_fails_closed_on_duplicate_target_rows():
    html = _index_html() + _index_html()
    result = probe.parse_filing_index(
        html,
        "spgi-20181231x10k.htm",
        "0000064040-19-000059.txt",
    )
    assert result["unique_target_rows"] is False
    assert result["primary"] is None
    assert result["submission"] is None


def test_submission_text_run_is_bounded_and_keeps_every_gate_closed(tmp_path):
    text_bytes = _submission_text()
    index_bytes = _index_html()
    primary_bytes = b"<html>current-primary-mock</html>\r\n"
    calls: list[tuple[str, int]] = []

    def fetcher(url, max_bytes, budget):
        calls.append((url, max_bytes))
        if url.endswith("-index.html"):
            body = index_bytes
        elif url.endswith(".txt"):
            body = text_bytes
        else:
            body = primary_bytes
        budget.add(len(body))
        return {
            "status": "FETCHED",
            "http_status": 200,
            "body": body,
            "response_bytes": len(body),
            "response_sha256": forensic.sha256(body),
            "content_length_header": str(len(body)),
            "last_modified": "Wed, 13 Feb 2019 11:02:53 GMT",
            "requested_url": url,
            "final_url": url,
        }

    output = tmp_path / "receipt.json"
    result = probe.run(REQUEST, SOURCE, SUMMARY, output, fetcher=fetcher)
    persisted = json.loads(output.read_text(encoding="utf-8"))

    assert result["status"] == "COMPLETE_SUBMISSION_TEXT_COMPARISON_COMPLETE"
    assert persisted["receipt_fingerprint"] == result["receipt_fingerprint"]
    assert result["comparison"]["complete_submission_text"]["identity_validated"] is True
    assert result["comparison"]["filing_index"]["target_rows_unique"] is True
    assert result["comparison"]["filing_index"]["primary_pinned_size_matches"] is True
    assert result["comparison"]["filing_index"]["submission_pinned_size_matches"] is True
    assert len(calls) == 3
    assert calls[0][1] == 250000
    assert calls[1][1] == 30000000
    assert calls[2][1] == 8000000
    assert result["source_download_bytes"] <= 80000000
    assert result["comparison"]["complete_submission_text"]["frozen_expected_sha256_match_variants"] == []
    assert result["gate_positive"] is False
    assert result["scientific_evidence"] is False
    assert result["performance_authorization"] is False
    assert result["holdout_selection"] is False
    assert result["ranking"] is False
    assert result["tuning"] is False
    assert result["promotion"] is False
    assert result["live_execution"] is False
    assert "body" not in result["complete_submission_response"]


def test_changed_frozen_hash_pin_is_rejected_before_any_network_call(tmp_path):
    changed = REQUEST.read_text(encoding="utf-8").replace(
        "EXPECTED_SHA256=27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83",
        "EXPECTED_SHA256=" + "a" * 64,
    )
    altered_request = tmp_path / "request.trigger"
    altered_request.write_text(changed, encoding="utf-8")
    calls = []

    def forbidden_fetcher(*_args, **_kwargs):
        calls.append(True)
        raise AssertionError("no network call is allowed after frozen pin mismatch")

    result = probe.run(altered_request, SOURCE, SUMMARY, tmp_path / "receipt.json", fetcher=forbidden_fetcher)
    assert result["status"] == "REQUEST_REJECTED"
    assert calls == []
    assert result["gate_positive"] is False
    assert result["live_execution"] is False
