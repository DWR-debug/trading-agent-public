from automation.q122_cftc_release_date_evidence import (
    classify,
    extract_documented_backlog,
    extract_schedule_metadata,
)


def test_q122_parses_documented_report_to_new_publish_mapping():
    html = b"""
    COT Report Date | Original Publish Date | New Publish Date
    09/30/2025 | 10/03/2025 | 11/19/2025
    10/07/2025 | 10/10/2025 | 11/21/2025
    """
    rows = extract_documented_backlog(html)
    assert rows[0]["report_date"] == "2025-09-30"
    assert rows[0]["original_publish_date"] == "2025-10-03"
    assert rows[0]["documented_new_publish_date"] == "2025-11-19"
    assert rows[0]["evidence_type"] == "DOCUMENTED_SPECIAL_ANNOUNCEMENT"


def test_q122_unknown_never_becomes_inferred_release_date():
    documented = {
        "2025-09-30": {
            "report_date": "2025-09-30",
            "original_publish_date": "2025-10-03",
            "documented_new_publish_date": "2025-11-19",
            "evidence_type": "DOCUMENTED_SPECIAL_ANNOUNCEMENT",
        }
    }
    out = classify("2019-01-08", documented)
    assert out["release_date"] == ""
    assert out["release_evidence_type"] == "UNKNOWN"


def test_q122_report_date_and_release_date_remain_distinct():
    documented = {
        "2025-09-30": {
            "report_date": "2025-09-30",
            "original_publish_date": "2025-10-03",
            "documented_new_publish_date": "2025-11-19",
            "evidence_type": "DOCUMENTED_SPECIAL_ANNOUNCEMENT",
        }
    }
    out = classify("2025-09-30", documented)
    assert out["report_date"] != out["release_date"]


def test_q122_schedule_metadata_does_not_claim_historical_mapping():
    html = b"Release Schedule: The Commitments of Traders reports are released at 3:30 p.m. Eastern time. 2026 Release Schedule"
    out = extract_schedule_metadata(html)
    assert out["release_time_et_documented"] is True
    assert out["2026_schedule_documented"] is True
    assert out["schedule_only_not_historical_mapping"] is True


def test_q122_parses_live_style_html_table_with_footnote():
    html = b"""
    <table>
      <tr><th>COT Report Date</th><th>Original Publish Date</th><th>New Publish Date</th></tr>
      <tr><td>09/30/2025</td><td>10/03/2025</td><td>11/19/2025<sup>+</sup></td></tr>
      <tr><td>10/07/2025</td><td>10/10/2025</td><td>11/21/2025</td></tr>
    </table>
    """
    rows = extract_documented_backlog(html)
    assert len(rows) == 2
    assert rows[0]["report_date"] == "2025-09-30"
    assert rows[0]["documented_new_publish_date"] == "2025-11-19"


def test_q122_release_clock_coverage_is_explicit():
    from automation.q122_cftc_release_date_evidence import build

    rows = [
        {
            "report_date": "2025-09-30",
            "original_publish_date": "2025-10-03",
            "documented_new_publish_date": "2025-11-19",
            "evidence_type": "DOCUMENTED_SPECIAL_ANNOUNCEMENT",
        },
        {
            "report_date": "2025-10-07",
            "original_publish_date": "2025-10-10",
            "documented_new_publish_date": "2025-11-21",
            "evidence_type": "DOCUMENTED_SPECIAL_ANNOUNCEMENT",
        },
    ]
    out = build(rows, {}, {})
    coverage = out["release_clock_coverage"]
    assert coverage["documented_mapping_count"] == 2
    assert coverage["documented_report_date_min"] == "2025-09-30"
    assert coverage["documented_report_date_max"] == "2025-10-07"
    assert coverage["documented_release_date_min"] == "2025-11-19"
    assert coverage["documented_release_date_max"] == "2025-11-21"
    assert "Only report dates with explicit documented release evidence" in coverage["formalization_rule"]
