from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation import q104_i19_filing_date_change_header_probe as probe


def test_header_parser_captures_date_of_filing_date_change_without_inference():
    raw = (
        b"<SEC-HEADER>\n"
        b"<ACCESSION-NUMBER>0000950123-17-002537\n"
        b"<CIK>0001276144\n"
        b"<CONFORMED-SUBMISSION-TYPE>13F-HR\n"
        b"<FILING-DATE>20170214\n"
        b"<DATE-OF-FILING-DATE-CHANGE>20170215\n"
        b"<ACCEPTANCE-DATETIME>20170214180040\n"
        b"</SEC-HEADER><DOCUMENT>\n"
    )
    parsed = probe.parse_header_fields(raw, "raw_sgml_header")
    assert parsed["accession"] == "0000950123-17-002537"
    assert parsed["filer_cik"] == "0001276144"
    assert parsed["form"] == "13F-HR"
    assert parsed["filing_date"] == "2017-02-14"
    assert parsed["date_of_filing_date_change"] == "2017-02-15"
    assert parsed["acceptance_datetime"] == "2017-02-14T18:00:40"


def test_header_parser_leaves_missing_date_change_unknown():
    parsed = probe.parse_header_fields(b"<FILING-DATE>20170214\n<ACCEPTANCE-DATETIME>20170214180040", "raw_sgml_header")
    assert parsed["date_of_filing_date_change"] is None
    assert parsed["filing_date"] == "2017-02-14"


def test_request_is_frozen_and_cannot_enable_field_precedence(tmp_path):
    values = dict(probe.FROZEN_REQUEST_VALUES)
    values["REQUEST_SEQUENCE"] = "2026-10-12T20:10:00Z"
    path = tmp_path / "request.trigger"
    path.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    assert probe.read_request(path)["PROBE_COUNT"] == "24"
    values["FIELD_PRECEDENCE_APPLIED"] = "true"
    path.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    with pytest.raises(probe.ProbeError, match="VALUE_MISMATCH:FIELD_PRECEDENCE_APPLIED"):
        probe.read_request(path)


def test_sample_population_and_download_budget_are_fixed():
    assert len(probe.EXPECTED) == 8
    assert len(probe.EXPECTED) * len(probe.ROUTES) == 24
    assert probe.MAX_RESPONSE_BYTES == 262_144
    assert probe.MAX_TOTAL_BYTES == 8_000_000
    assert all(x["bulk_filing_date"] for x in probe.EXPECTED.values())
