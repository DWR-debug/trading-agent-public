import json

import automation.q124_source_feasibility as q124


def test_q124_source_feasibility_is_non_scientific(monkeypatch):
    treasury = {
        "data": [{
            "record_date": "2026-09-10",
            "auction_date": "2026-09-10",
            "security_type": "Note",
            "security_term": "10-Year",
            "bid_to_cover_ratio": "2.50",
            "high_yield": "4.0",
            "median_yield": "4.0",
            "low_yield": "4.0",
        }]
    }
    cboe = "<html>09:00 CALLS PUTS 09:30 CALLS PUTS</html>"

    def fake_fetch(url):
        if "fiscaldata.treasury.gov" in url:
            return 200, json.dumps(treasury)
        return 200, cboe

    monkeypatch.setattr(q124, "fetch", fake_fetch)
    result = q124.build()
    assert result["paper_only"] is True
    assert result["scientific_boundary"]["performance_evaluation"] is False
    assert result["scientific_boundary"]["candidate_selection"] is False
    assert result["next_gate"] == "historical_archive_and_PIT_reconstruction"
    assert result["probes"]["treasury"]["source_status"] == "PUBLIC_SOURCE_VERIFIABLE"
    assert result["probes"]["cboe"]["source_status"] == "PUBLIC_CURRENT_SOURCE_VERIFIABLE"
