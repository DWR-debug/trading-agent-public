from automation import q218_sec_event_pair_lineage_gate as gate

def test_q218_pairs_latest_prior_item_202_and_tracks_amendments(tmp_path, monkeypatch):
    import json

    payload = {
        "filings": {
            "recent": {
                "form": ["10-K", "8-K", "8-K", "10-K/A"],
                "filingDate": ["2025-01-02", "2025-01-01", "2025-01-03", "2025-02-01"],
                "accessionNumber": [
                    "0000320193-25-000001",
                    "0000320193-25-000000",
                    "0000320193-25-000002",
                    "0000320193-25-000003",
                ],
                "primaryDocument": ["tenk.htm", "old.htm", "earn.htm", "amend.htm"],
                "reportDate": ["2024-09-28", "2024-09-28", "2024-09-28", "2024-09-28"],
                "items": ["", "2.02,9.01", "2.02,9.01", ""],
            }
        }
    }
    acceptance_map = {
        "0000320193-25-000001": "20250102120000",
        "0000320193-25-000000": "20250101120000",
        "0000320193-25-000002": "20250103120000",
        "0000320193-25-000003": "20250201120000",
    }

    def fake_fetch(url):
        if "/submissions/CIK" in url:
            return json.dumps(payload).encode()
        accession = url.split("/")[-1].replace("-index-headers.html", "")
        return (
            f"<ACCEPTANCE-DATETIME>{acceptance_map[accession]}".encode()
        )

    monkeypatch.setattr(gate, "fetch", fake_fetch)
    result = gate.run(tmp_path / "receipt.json")

    assert result["issuer_count"] == 8
    aapl = result["issuer_results"]["AAPL"]
    assert aapl["event_pair_count"] == 1
    assert aapl["event_pairs"][0]["item_2_02_8k_accession"] == "0000320193-25-000002"
    assert aapl["event_pairs"][0]["acceptance_order_valid"] is True
    assert aapl["amendment_lineage"][0]["parent_candidate_accession"] == "0000320193-25-000001"
    assert aapl["all_pairing_valid"] is True
    assert aapl["all_lineage_valid"] is True
    assert result["all_pairing_valid"] is True
    assert result["next_gate"] == "INDEPENDENT_ARCHITECTURE_PIT_REPRODUCTION"
    assert result["performance_authorization"] is False
    assert result["live_execution"] is False


def test_q218_rejects_future_8k_pair(tmp_path, monkeypatch):
    import json

    payload = {
        "filings": {
            "recent": {
                "form": ["10-K", "8-K"],
                "filingDate": ["2025-01-02", "2025-01-03"],
                "accessionNumber": ["0000320193-25-000001", "0000320193-25-000002"],
                "primaryDocument": ["tenk.htm", "earn.htm"],
                "reportDate": ["2024-09-28", "2024-09-28"],
                "items": ["", "2.02,9.01"],
            }
        }
    }

    def fake_fetch(url):
        if "/submissions/CIK" in url:
            return json.dumps(payload).encode()
        return b"<ACCEPTANCE-DATETIME>20250103120000"

    monkeypatch.setattr(gate, "fetch", fake_fetch)
    result = gate.run(tmp_path / "receipt.json")
    assert result["all_pairing_valid"] is False
    assert result["next_gate"] == "REPAIR_10K_8K_EVENT_PAIR_AND_AMENDMENT_LINEAGE"
