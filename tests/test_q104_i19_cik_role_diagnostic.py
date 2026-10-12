from __future__ import annotations

import io
import json
import zipfile

import pytest

from automation import q104_i19_cik_role_diagnostic as diagnostic
from automation.q104_i19_13f_historical_identity_census_merge import canonical_fingerprint


def test_read_exact_submission_row_keeps_source_cik_separate_from_accession_prefix():
    raw = io.BytesIO()
    submission = (
        "ACCESSION_NUMBER\tFILING_DATE\tPERIODOFREPORT\tCIK\tSUBMISSIONTYPE\n"
        "0001493152-24-018939\t13-MAY-2024\t31-MAR-2024\t1960050\t13F-HR\n"
    )
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("SUBMISSION.tsv", submission)
    row = diagnostic.read_exact_submission_row(raw.getvalue())
    assert row["source_cik_raw"] == "1960050"
    assert row["source_cik_normalized"] == "0001960050"
    assert row["filing_date_iso"] == "2024-05-13"
    assert row["source_cik_normalized"] != diagnostic.ACCESSION.split("-", 1)[0]


def test_read_exact_submission_row_fails_closed_on_duplicate_accession():
    raw = io.BytesIO()
    submission = (
        "ACCESSION_NUMBER\tFILING_DATE\tPERIODOFREPORT\tCIK\tSUBMISSIONTYPE\n"
        "0001493152-24-018939\t13-MAY-2024\t31-MAR-2024\t1960050\t13F-HR\n"
        "0001493152-24-018939\t13-MAY-2024\t31-MAR-2024\t2094379\t13F-HR\n"
    )
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("SUBMISSION.tsv", submission)
    with pytest.raises(diagnostic.DiagnosticError, match="SOURCE_ROW_COUNT_INVALID:2"):
        diagnostic.read_exact_submission_row(raw.getvalue())


def test_build_cik_candidates_preserves_sources_and_deduplicates_values():
    candidates = diagnostic.build_cik_candidates("0001493152")
    assert candidates[0] == {
        "cik": "0001493152",
        "observed_sources": ["submission_tsv_cik", "accession_prefix_cik"],
    }
    assert len({item["cik"] for item in candidates}) == len(candidates)
    assert any(item["cik"] == "0002094379" for item in candidates)
    assert any(item["cik"] == "0001960050" for item in candidates)


def test_validate_frozen_shard_receipt_requires_exact_archive_pin(tmp_path, monkeypatch):
    archive_item = {
        "archive": {"url": diagnostic.ARCHIVE_URL, "period_start": "2024-03-01"},
        "archive_sha256": diagnostic.ARCHIVE_SHA256,
        "archive_bytes": diagnostic.ARCHIVE_BYTES,
        "acceptance_failures": {diagnostic.ACCESSION: diagnostic.EXPECTED_FAILURE},
    }
    unsigned = {
        "task_id": "Q-2026-10-06-104-I19-13F-HISTORICAL-ID-CENSUS-2024-2025-09",
        "shard": diagnostic.SOURCE_SHARD,
        "source_page_sha256": diagnostic.SOURCE_PAGE_SHA256,
        "archives": [archive_item],
    }
    fingerprint = canonical_fingerprint(unsigned)
    receipt = {**unsigned, "receipt_fingerprint": fingerprint}
    monkeypatch.setattr(diagnostic, "SOURCE_SHARD_RECEIPT_FINGERPRINT", fingerprint)
    path = tmp_path / "shard_receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    _, found = diagnostic.validate_frozen_shard_receipt(path)
    assert found["archive_sha256"] == diagnostic.ARCHIVE_SHA256

    found_bad = dict(archive_item)
    found_bad["archive_sha256"] = "0" * 64
    bad_unsigned = {**unsigned, "archives": [found_bad]}
    bad_fp = canonical_fingerprint(bad_unsigned)
    path.write_text(json.dumps({**bad_unsigned, "receipt_fingerprint": bad_fp}), encoding="utf-8")
    monkeypatch.setattr(diagnostic, "SOURCE_SHARD_RECEIPT_FINGERPRINT", bad_fp)
    with pytest.raises(diagnostic.DiagnosticError, match="PINNED_ARCHIVE_RECEIPT_FIELDS_MISMATCH"):
        diagnostic.validate_frozen_shard_receipt(path)


def test_extract_embedded_cik_observations_reports_xml_paths_not_roles():
    body = (
        b"<DOCUMENT>\n<TYPE>13F-HR\n<FILENAME>primary_doc.xml\n<TEXT>"
        b"<edgarSubmission><formData><filingManager><cik>0001960050</cik></filingManager>"
        b"<reportingManager><cik>0002094379</cik></reportingManager></formData></edgarSubmission>"
        b"</TEXT>\n</DOCUMENT>"
    )
    values = diagnostic.extract_embedded_cik_observations(body)
    assert [x["value_normalized"] for x in values] == ["0001960050", "0002094379"]
    assert values[0]["element_path"].endswith("/filingManager/cik")
    assert values[1]["element_path"].endswith("/reportingManager/cik")
    assert all("role" not in item for item in values)


def test_diagnostic_result_never_clears_identity_gate_from_single_cik_role_trace():
    source_row = {
        "accession": diagnostic.ACCESSION,
        "source_cik_raw": "1960050",
        "source_cik_normalized": "0001960050",
        "form": "13F-HR",
        "filing_date_raw": "13-MAY-2024",
        "filing_date_iso": "2024-05-13",
        "period_of_report": "31-MAR-2024",
    }
    observed = {
        "accession": diagnostic.ACCESSION,
        "filer_cik": "0002094379",
        "form": "13F-HR",
        "filing_date": "2024-05-13",
        "acceptance_datetime": "2024-05-13T16:57:35",
    }
    probes = [
        {"status": "FETCHED", "route": "index_headers", "observed_identity": observed},
        {"status": "FETCHED", "route": "raw_sgml_header", "observed_identity": observed},
        {"status": "FETCHED_PREFIX", "route": "complete_submission_header_prefix", "observed_identity": observed},
    ]
    full = {
        "status": "FETCHED",
        "complete_submission_captured": True,
        "embedded_cik_observations": [
            {"value_normalized": "0001960050", "element_path": "/submission/filingManager/cik"},
        ],
    }
    result = diagnostic.diagnostic_result({"REQUEST_SEQUENCE": "2026-10-12T15:00:00Z"}, source_row, probes, full)
    sample = result["sample"]
    assert result["status"] == "CIK_ROLE_LINEAGE_OBSERVED_GATE_UNRESOLVED"
    assert sample["header_filer_cik_consensus"] == "0002094379"
    assert sample["source_cik_matches_header_filer_cik"] is False
    assert sample["accession_prefix_cik_matches_header_filer_cik"] is False
    assert sample["source_cik_appears_in_embedded_document"] is True
    assert result["research_boundary"]["identity_discrepancy_resolved"] is False
    assert result["research_boundary"]["candidate_identity_gate_cleared"] is False
    assert result["scientific_evidence"] is False


def test_frozen_request_requires_exact_request_pins(tmp_path):
    values = {**diagnostic.FROZEN_REQUEST_VALUES, "REQUEST_SEQUENCE": "2026-10-12T15:00:00Z"}
    path = tmp_path / "request.trigger"
    path.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n", encoding="utf-8")
    assert diagnostic.read_request(path)["ACCESSION"] == diagnostic.ACCESSION
    path.write_text(path.read_text(encoding="utf-8").replace("CENSUS_RESTART=false", "CENSUS_RESTART=true"), encoding="utf-8")
    with pytest.raises(diagnostic.DiagnosticError, match="REQUEST_VALUE_MISMATCH:CENSUS_RESTART"):
        diagnostic.read_request(path)
