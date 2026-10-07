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
    assert aapl["event_pairs"][0]["item_2_02_8k_accession"] == "0000320193-25-000000"
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
    acceptance_map = {
        "0000320193-25-000001": "20250102120000",
        "0000320193-25-000002": "20250104120000",
    }

    def fake_fetch(url):
        if "/submissions/CIK" in url:
            return json.dumps(payload).encode()
        accession = url.split("/")[-1].replace("-index-headers.html", "")
        return f"<ACCEPTANCE-DATETIME>{acceptance_map[accession]}".encode()

    monkeypatch.setattr(gate, "fetch", fake_fetch)
    result = gate.run(tmp_path / "receipt.json")
    assert result["all_pairing_valid"] is False
    assert result["next_gate"] == "REPAIR_10K_8K_EVENT_PAIR_AND_AMENDMENT_LINEAGE"


def test_q218_uses_acceptance_interval_when_report_dates_differ(tmp_path, monkeypatch):
    import json

    payload = {
        "filings": {
            "recent": {
                "form": ["10-K", "8-K"],
                "filingDate": ["2025-02-20", "2025-02-19"],
                "accessionNumber": ["0000320193-25-000010", "0000320193-25-000009"],
                "primaryDocument": ["tenk.htm", "earn.htm"],
                "reportDate": ["2025-01-31", "2025-02-19"],
                "items": ["", "2.02,9.01"],
            }
        }
    }
    acceptance_map = {
        "0000320193-25-000010": "20250220120000",
        "0000320193-25-000009": "20250219120000",
    }

    def fake_fetch(url):
        if "/submissions/CIK" in url:
            return json.dumps(payload).encode()
        accession = url.split("/")[-1].replace("-index-headers.html", "")
        return f"<ACCEPTANCE-DATETIME>{acceptance_map[accession]}".encode()

    monkeypatch.setattr(gate, "fetch", fake_fetch)
    result = gate.run(tmp_path / "receipt.json")
    aapl = result["issuer_results"]["AAPL"]

    assert aapl["event_pair_count"] == 1
    assert aapl["event_pairs"][0]["item_2_02_8k_accession"] == "0000320193-25-000009"
    assert aapl["event_pairs"][0]["pairing_method"] == "acceptance_interval"
    assert aapl["event_pairs"][0]["pairing_lower_bound_acceptance"] is None
    assert aapl["event_pairs"][0]["acceptance_order_valid"] is True
    assert aapl["all_pairing_valid"] is True


def test_q218_fetch_retries_transient_timeout_then_succeeds(monkeypatch):
    calls = []
    sleeps = []

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return b"ok"

    def fake_urlopen(req, timeout):
        calls.append(timeout)
        if len(calls) < 3:
            raise TimeoutError("temporary SEC timeout")
        return Response()

    monkeypatch.setattr(gate.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(gate.time, "sleep", sleeps.append)

    assert gate.fetch("https://example.invalid") == b"ok"
    assert calls == [30, 30, 30]
    assert sleeps == [2, 4]


def test_q218_fetch_does_not_retry_non_transient_http_error(monkeypatch):
    import pytest

    def fake_urlopen(req, timeout):
        raise gate.urllib.error.HTTPError(
            req.full_url, 404, "not found", hdrs=None, fp=None
        )

    monkeypatch.setattr(gate.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(gate.urllib.error.HTTPError) as exc:
        gate.fetch("https://example.invalid")
    assert exc.value.code == 404


def test_q218_uses_explicit_parent_filing_date_for_amendment(tmp_path, monkeypatch):
    import json

    payload = {
        "filings": {
            "recent": {
                "form": ["8-K", "10-K", "8-K/A"],
                "filingDate": ["2025-11-14", "2026-03-13", "2026-01-16"],
                "accessionNumber": [
                    "0000104169-25-000172",
                    "0000104169-26-000055",
                    "0000104169-26-000024",
                ],
                "primaryDocument": ["wmt-20251111.htm", "wmt-20260131.htm", "wmt-20251113.htm"],
                "reportDate": ["2025-11-11", "2026-01-31", "2025-11-13"],
                "items": ["5.02,9.01", "", "5.02"],
            }
        }
    }
    acceptance_map = {
        "0000104169-25-000172": "20251114080030",
        "0000104169-26-000055": "20260313160624",
        "0000104169-26-000024": "20260116090305",
    }

    def fake_fetch(url):
        if "/submissions/CIK" in url:
            return json.dumps(payload).encode()
        accession = url.split("/")[-1].replace("-index-headers.html", "")
        if accession in acceptance_map:
            return f"<ACCEPTANCE-DATETIME>{acceptance_map[accession]}".encode()
        if url.endswith("/wmt-20251111.htm"):
            return b"Initial CEO succession filing"
        if url.endswith("/wmt-20260131.htm"):
            return b"Annual report"
        if url.endswith("/wmt-20251113.htm"):
            return (
                b"As previously reported in a Current Report on Form 8-K "
                b"filed with the Securities and Exchange Commission on November 14, 2025 "
                b"(the Initial Form 8-K)."
            )
        return b""

    monkeypatch.setattr(gate, "fetch", fake_fetch)
    result = gate.run(tmp_path / "receipt.json")
    wmt = result["issuer_results"]["WMT"]
    assert wmt["all_lineage_valid"] is True
    assert wmt["amendment_lineage"][0]["parent_candidate_accession"] == "0000104169-25-000172"
