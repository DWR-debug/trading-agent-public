from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import automation.q228_sec_correspondence_source_gate as gate


def _run_gate(
    monkeypatch,
    tmp_path: Path,
    responses: dict[str, tuple[int, dict, bytes, str] | Exception],
):
    calls: list[str] = []

    def fake_fetch(url: str):
        calls.append(url)
        response = responses[url]
        if isinstance(response, Exception):
            raise response
        return response

    output = tmp_path / "q228_receipt.json"
    monkeypatch.setattr(gate, "fetch", fake_fetch)
    monkeypatch.setattr(sys, "argv", ["q228_sec_correspondence_source_gate", "--output", str(output)])
    gate.main()
    return json.loads(output.read_text(encoding="utf-8")), calls


def _complete_responses():
    return {
        gate.ROOT: (
            200,
            {"Content-Type": "text/html; charset=utf-8"},
            b"<html><head><title>SEC Correspondence Guidance</title></head><body><h1>SEC correspondence</h1>SEC publicly releases correspondence after 20 business days; UPLOAD and CORRESP are distinct.</body></html>",
            gate.ROOT,
        ),
        gate.SEARCH: (
            200,
            {"Content-Type": "text/html; charset=utf-8"},
            b"<html><head><title>EDGAR Search</title></head><body><h1>EDGAR search</h1>Filing review correspondence. Last 10 years of filings.</body></html>",
            gate.SEARCH,
        ),
    }


def test_module_imports():
    assert callable(gate.main)


def test_positive_page_structure_does_not_authorize_pit_or_performance(monkeypatch, tmp_path):
    receipt, calls = _run_gate(monkeypatch, tmp_path, _complete_responses())

    assert receipt["status"] == "SOURCE_STRUCTURE_READY_NO_PERFORMANCE"
    assert set(calls) == {gate.ROOT, gate.SEARCH}
    assert len(receipt["results"]) == 2
    assert all(row["reachable"] is True for row in receipt["results"])
    assert all(row["missing_markers"] == [] for row in receipt["results"])
    assert all(len(row["sha256"]) == 64 for row in receipt["results"])
    assert all(row["content_type"].startswith("text/html") for row in receipt["results"])
    assert all(row["final_url"] == row["url"] for row in receipt["results"])
    assert receipt["results"][0]["title"] == "SEC Correspondence Guidance"
    assert receipt["results"][0]["h1"] == "SEC correspondence"
    search = next(row for row in receipt["results"] if row["name"] == "SEC_EDGAR_SEARCH")
    marker = next(item for item in search["marker_diagnostics"] if item["marker"] == "Filing review correspondence")
    assert marker["found"] is True
    assert "Filing review correspondence" in marker["context"]

    # The gate only establishes current-page structure. Historical identity,
    # public-clock reconstruction and performance remain explicitly closed.
    assert receipt["pit_contract"]["public_observation_clock_proven"] is False
    assert receipt["pit_contract"]["latent_review_start_tradable"] is False
    assert receipt["pit_contract"]["same_day_use_allowed"] is False
    assert receipt["pit_contract"]["review_cycle_filing_join_completed"] is False
    assert receipt["pit_contract"]["future_correspondence_mutation_allowed"] is False
    assert all(value is False for value in receipt["scientific_boundary"].values())

    fingerprint = receipt.pop("receipt_fingerprint")
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert hashlib.sha256(canonical.encode()).hexdigest() == fingerprint


def test_missing_marker_fails_closed_and_records_bounded_diagnostics(monkeypatch, tmp_path):
    responses = _complete_responses()
    responses[gate.SEARCH] = (
        200,
        {"Content-Type": "text/html; charset=utf-8"},
        b"<html><head><title>EDGAR Search</title></head><body><h1>EDGAR search</h1>Filing results only; category marker is absent.</body></html>",
        "https://www.sec.gov/edgar/search/",
    )

    receipt, _ = _run_gate(monkeypatch, tmp_path, responses)

    assert receipt["status"] == "SOURCE_STRUCTURE_INCOMPLETE"
    search = next(row for row in receipt["results"] if row["name"] == "SEC_EDGAR_SEARCH")
    assert search["reachable"] is True
    assert search["title"] == "EDGAR Search"
    assert search["content_type"].startswith("text/html")
    assert "Filing review correspondence" in search["missing_markers"]
    marker = next(item for item in search["marker_diagnostics"] if item["marker"] == "Filing review correspondence")
    assert marker == {"marker": "Filing review correspondence", "found": False, "context": None}
    assert receipt["pit_contract"]["public_observation_clock_proven"] is False
    assert all(value is False for value in receipt["scientific_boundary"].values())


def test_fetch_exception_is_recorded_and_fails_closed(monkeypatch, tmp_path):
    responses = _complete_responses()
    responses[gate.ROOT] = OSError("controlled test failure")

    receipt, _ = _run_gate(monkeypatch, tmp_path, responses)

    assert receipt["status"] == "SOURCE_STRUCTURE_INCOMPLETE"
    guidance = next(row for row in receipt["results"] if row["name"] == "SEC_CORRESPONDENCE_GUIDANCE")
    assert guidance["reachable"] is False
    assert guidance["error"] == "OSError:controlled test failure"
    assert guidance["sha256"] is None
    assert guidance["content_type"] is None
    assert guidance["final_url"] is None
    assert guidance["marker_diagnostics"] == []
    assert all(value is False for value in receipt["scientific_boundary"].values())
