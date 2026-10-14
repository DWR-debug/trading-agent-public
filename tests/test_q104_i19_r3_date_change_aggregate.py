from automation.q104_i19_r3_date_change_aggregate import build_aggregate, route_summary, AggregateError


def probe(route, accession, cik, date="2016-11-14", acceptance="2016-11-14T17:49:15", change="2016-11-17"):
    return {"route":route,"http_status":200,"status":"FETCHED",
            "observed_fields":{"route":route,"accession":accession,"filer_cik":cik,"form":"13F-HR",
                               "filing_date":date,"acceptance_datetime":acceptance,
                               "date_of_filing_date_change":change}}


def test_route_summary_preserves_missing_date_change_without_imputation():
    accession="0000950123-16-022491"
    row={"accession":accession,"form":"13F-HR","bulk_filing_date":"2016-11-15",
         "probes":[probe("index_headers",accession,"0000896159"),
                   probe("raw_sgml_header",accession,"0000896159",change=None),
                   probe("complete_submission_header_prefix",accession,"0000896159",change=None)]}
    out=route_summary(row,"fixture")
    assert out["bulk_date_differs_from_header"] is True
    assert out["date_change_observed"] is True
    assert out["date_change_values"] == ["2016-11-17"]
    assert out["date_change_route_count"] == 1


def test_route_summary_marks_disagreement_without_picking_a_winner():
    accession="0000950123-16-022491"
    row={"accession":accession,"form":"13F-HR","bulk_filing_date":"2016-11-15",
         "probes":[probe("index_headers",accession,"0000896159",change="2016-11-16"),
                   probe("raw_sgml_header",accession,"0000896159",change="2016-11-17"),
                   probe("complete_submission_header_prefix",accession,"0000896159",change=None)]}
    out=route_summary(row,"fixture")
    assert out["date_change_routes_agree_where_observed"] is False
    assert out["date_change_equals_header_filing_date"] is None


def test_aggregate_requires_exact_upstream_fingerprints_and_fourteen_disjoint_rows():
    prior={"record_type":"q104_i19_filing_date_change_header_probe","status":"not complete"}
    try:
        build_aggregate(prior,{})
    except AggregateError as e:
        assert "PRIOR_FIELD_PROBE_NOT_COMPLETE" in str(e)
    else:
        raise AssertionError("incomplete upstream evidence must fail closed")
