from automation.q104_i19_r3_date_change_header_probe import (
    EXPECTED, ROUTES, fingerprint, parse_header_fields, validate_sample_observations,
)


def test_r3_sample_allowlist_is_exact_and_frozen():
    assert set(EXPECTED) == {
        "0000950123-16-022491",
        "0000950123-16-022512",
        "0001138060-16-000026",
        "0001144204-16-134468",
        "0001144204-16-134474",
        "0001352900-16-000030",
    }
    assert len(ROUTES) == 3
    assert all(x["bulk_date"] == "2016-11-15" and x["header_date"] == "2016-11-14" for x in EXPECTED.values())


def test_parser_captures_date_change_and_acceptance_from_sgml():
    raw = b"""<SEC-HEADER>
<ACCESSION-NUMBER>0000950123-16-022491
<FILER><CIK>896159</CIK></FILER>
<CONFORMED-SUBMISSION-TYPE>13F-HR
<FILING-DATE>20161114
<DATE-OF-FILING-DATE-CHANGE>20161117
<ACCEPTANCE-DATETIME>20161114174915
</SEC-HEADER>"""
    got = parse_header_fields(raw, "raw_sgml_header")
    assert got["accession"] == "0000950123-16-022491"
    assert got["filer_cik"] == "0000896159"
    assert got["form"] == "13F-HR"
    assert got["filing_date"] == "2016-11-14"
    assert got["date_of_filing_date_change"] == "2016-11-17"
    assert got["acceptance_datetime"] == "2016-11-14T17:49:15"


def test_parser_supports_index_header_date_labels():
    raw = b"""ACCESSION NUMBER: 0000950123-16-022491
CENTRAL INDEX KEY: 0000896159
CONFORMED SUBMISSION TYPE: 13F-HR
FILED AS OF DATE: 20161114
DATE OF FILING DATE CHANGE: 20161117
<ACCEPTANCE-DATE>20161114</ACCEPTANCE-DATE>
<ACCEPTANCE-TIME>174915</ACCEPTANCE-TIME>"""
    got = parse_header_fields(raw, "index_headers")
    assert got["date_of_filing_date_change"] == "2016-11-17"
    assert got["acceptance_datetime"] == "2016-11-14T17:49:15"


def test_observation_checker_fails_closed_on_identity_or_filing_date_mismatch():
    accession = "0000950123-16-022491"
    expected = EXPECTED[accession]
    probes = []
    for route in ROUTES:
        probes.append({
            "route":route,"status":"FETCHED","http_status":200,
            "observed_fields":{
                "accession":accession,"filer_cik":expected["cik"],"form":"13F-HR",
                "filing_date":expected["header_date"],"acceptance_datetime":expected["acceptance"],
                "date_of_filing_date_change":"2016-11-17","route":route,
            },
        })
    ok, checks = validate_sample_observations(accession, probes)
    assert ok
    assert checks["date_change_route_values"] == ["2016-11-17"] * 3
    probes[1]["observed_fields"]["filer_cik"] = "0000000000"
    assert validate_sample_observations(accession, probes)[0] is False


def test_fingerprint_is_order_invariant_and_detects_mutation():
    source = {"b":2,"a":1,"receipt_fingerprint":"old"}
    expected = fingerprint(source)
    assert expected == fingerprint({"a":1,"b":2,"receipt_fingerprint":"different"})
    assert expected != fingerprint({"a":1,"b":3})
