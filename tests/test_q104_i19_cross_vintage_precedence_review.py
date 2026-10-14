from copy import deepcopy
import pytest

from automation import q104_i19_cross_vintage_precedence_review as review


def aggregate_fixture():
    rows = []
    for i in range(14):
        changed_equals = i < 2
        rows.append({
            "source_label": "R1_R2_2015_2017_2020_2025" if i < 8 else "R3_2016Q4",
            "accession": f"0000000000-16-{i + 1:06d}",
            "filer_cik": f"{1000000000 + i}",
            "form": "13F-HR",
            "bulk_filing_date": "2016-11-15",
            "edgar_header_filing_dates": ["2016-11-14"],
            "edgar_header_filing_date_route_count": 3,
            "acceptance_datetimes": ["2016-11-14T17:49:15"],
            "acceptance_route_count": 3,
            "date_change_values": ["2016-11-14" if changed_equals else "2016-11-15"],
            "date_change_route_count": 3,
            "date_change_observed": True,
            "date_change_equals_header_filing_date": changed_equals,
            "date_change_routes_agree_where_observed": True,
            "bulk_date_differs_from_header": True,
            "identity_fields_consistent": True,
            "header_filing_date_routes_agree": True,
            "acceptance_routes_agree": True,
        })
    return {
        "schema_version": 1,
        "record_type": "q104_i19_cross_vintage_date_change_aggregate",
        "status": "FIELD_PRECEDENCE_EXTENDED_DIAGNOSTIC_ONLY_NOT_APPLIED",
        "generated_at_utc": "2026-10-14T11:39:00+00:00",
        "analysis_fingerprint": "a" * 64,
        "source_prior_run_id": "38304249742",
        "source_prior_receipt_fingerprint": review.PRIOR_FP,
        "source_r1_receipt_fingerprint": review.R1_FP,
        "source_r2_receipt_fingerprint": review.R2_FP,
        "source_r3_lineage_receipt_fingerprint": review.R3_FP,
        "counts": {
            "sample_count": 14,
            "bulk_date_differs_from_header": 14,
            "header_filing_date_routes_agree": 14,
            "acceptance_routes_agree": 14,
            "date_change_observed": 14,
            "date_change_routes_agree_where_observed": 14,
            "date_change_equals_header_filing_date": 2,
            "date_change_differs_from_header_filing_date": 12,
        },
        "samples": rows,
        "interpretation_scope": {
            "field_precedence_applied": False,
            "source_receipts_modified": False,
            "acceptance_time_gate_cleared": False,
            "historical_archive_gate_cleared": False,
            "production_join_changed": False,
            "census_restarted": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }


def pin_receipt(monkeypatch, payload, expected_name):
    payload = deepcopy(payload)
    payload["receipt_fingerprint"] = review.fingerprint(payload)
    monkeypatch.setattr(review, expected_name, payload["receipt_fingerprint"])
    return payload


def test_review_expands_proposal_to_14_rows_without_applying_precedence(monkeypatch):
    monkeypatch.setattr(review, "ANALYSIS_FP", "a" * 64)
    x64 = pin_receipt(monkeypatch, aggregate_fixture(), "X64_FP")
    arm = aggregate_fixture()
    arm["generated_at_utc"] = "2026-10-14T11:39:26+00:00"
    arm = pin_receipt(monkeypatch, arm, "ARM64_FP")

    result = review.build_review(x64, arm)

    assert result["status"] == "FIELD_PRECEDENCE_REVIEW_PROPOSAL_READY_NOT_APPLIED"
    assert result["independent_analysis_fingerprint_match"] is True
    assert result["counts"]["sample_count"] == 14
    assert result["counts"]["bulk_date_differs_from_header"] == 14
    assert result["counts"]["date_change_differs_from_header_filing_date"] == 12
    assert result["counts"]["date_change_equals_header_filing_date"] == 2
    assert result["archive_vintage_count"] == 5
    assert result["interpretation_scope"]["source_precedence_applied"] is False
    assert result["interpretation_scope"]["production_join_changed"] is False
    assert result["safety"]["live_trading_enabled"] is False


def test_review_rejects_any_upstream_scope_violation(monkeypatch):
    monkeypatch.setattr(review, "ANALYSIS_FP", "a" * 64)
    payload = aggregate_fixture()
    payload["interpretation_scope"]["field_precedence_applied"] = True
    x64 = pin_receipt(monkeypatch, payload, "X64_FP")
    arm = pin_receipt(monkeypatch, aggregate_fixture(), "ARM64_FP")

    with pytest.raises(review.ReviewError, match="AGGREGATE_SCOPE_VIOLATION:field_precedence_applied"):
        review.build_review(x64, arm)


def test_request_cannot_enable_precedence_or_change_frozen_pins(tmp_path):
    values = dict(review.FROZEN)
    values["REQUEST_SEQUENCE"] = "2026-10-14T11:42:00Z"
    request = tmp_path / "request.trigger"
    request.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    assert review.read_request(request)["SAMPLE_COUNT"] == "14"

    values["APPLY_FIELD_PRECEDENCE"] = "true"
    request.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    with pytest.raises(review.ReviewError, match="REQUEST_VALUE_MISMATCH:APPLY_FIELD_PRECEDENCE"):
        review.read_request(request)
