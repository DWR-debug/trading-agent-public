import io
import json
import zipfile
from pathlib import Path

from automation import q218_q221_historical_source_census as census


def test_q218_q221_census_is_deterministic_and_non_authorizing(tmp_path, monkeypatch):
    sample_json = json.dumps(
        {
            "filings": {
                "recent": {
                    "form": ["10-K", "8-K"],
                    "filingDate": ["2025-02-01", "2025-02-15"],
                    "reportDate": ["2024-09-30", "2024-09-30"],
                    "accessionNumber": ["0000320193-25-000001", "0000320193-25-000002"],
                    "primaryDocument": ["a10k.htm", "a8k.htm"],
                    "items": ["", "2.02,9.01"],
                }
            }
        }
    ).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name in ["sub.tsv", "tag.tsv", "dim.tsv", "num.tsv", "txt.tsv"]:
            archive.writestr(name, "fixture")
    zip_bytes = buffer.getvalue()

    seen_submission_urls = []

    def fake_fetch(url: str, limit=1000000):
        if "submissions/CIK" in url:
            seen_submission_urls.append(url)
            return 200, "application/json", sample_json
        if url.endswith("-index-headers.html"):
            return 200, "text/html", b"<ACCEPTANCE-DATETIME>20250215123000"
        if url.endswith("a8k.htm"):
            return 200, "text/html", b"ITEM 2.02 RESULTS OF OPERATIONS AND FINANCIAL CONDITION EARNINGS RELEASE"
        if url.endswith(".zip"):
            return 200, "application/zip", zip_bytes
        if "about-the-data-download.pdf" in url:
            return 200, "application/pdf", b"USA"
        if "api.usaspending.gov/docs/endpoints" in url:
            return 200, "text/html", b"/api/v2/transactions/"
        return 200, "text/html", b"fixture"

    monkeypatch.setattr(census, "fetch", fake_fetch)
    monkeypatch.setattr(
        census,
        "_extract_pdf_text",
        lambda body: "Frequency of Updates to Prime Award Data for Contracts "
        "within five days published to USAspending.gov following morning",
    )
    result = census.run(tmp_path / "census.json")
    assert result["candidate_ids"] == ["Q218", "Q219", "Q220", "Q221"]
    assert result["scientific_evidence"] is False
    assert result["performance_authorization"] is False
    assert result["holdout_selection"] is False
    assert result["ranking"] is False
    assert result["tuning"] is False
    assert result["promotion"] is False
    assert result["live_execution"] is False
    assert result["q218_sec_pair_census"]["pairable_issuer_count"] == 8
    assert len(seen_submission_urls) == 8
    assert all("/submissions/CIK" in url and len(url.rsplit("CIK", 1)[1].split(".json", 1)[0]) == 10 for url in seen_submission_urls)
    assert any(url.endswith("CIK0000320193.json") for url in seen_submission_urls)
    assert all(item["pairability_observed"] for item in result["q218_sec_pair_census"]["issuer_results"].values())
    assert result["q220_sec_notes_census"]["zip_parse_ok"] is True
    assert result["q221_usa_rdtne_census"]["public_clock_section_found"] is True
    assert result["q221_usa_rdtne_census"]["contract_modification_within_five_days_found"] is True
    assert result["q221_usa_rdtne_census"]["publication_sequence_found"] is True
    assert result["q221_usa_rdtne_census"]["transactions_endpoint_documented"] is True
    assert Path(tmp_path / "census.json").is_file()

def test_q218_sec_submission_census_excludes_8k_amendments_from_event_pairing(monkeypatch):
    sample_json = json.dumps(
        {
            "filings": {
                "recent": {
                    "form": ["10-K", "8-K", "8-K/A"],
                    "filingDate": ["2025-02-01", "2025-02-15", "2025-02-16"],
                    "reportDate": ["2024-09-30", "2024-09-30", "2024-09-30"],
                    "accessionNumber": [
                        "0000320193-25-000001",
                        "0000320193-25-000002",
                        "0000320193-25-000003",
                    ],
                    "primaryDocument": ["a10k.htm", "a8k.htm", "a8ka.htm"],
                    "items": ["", "2.02,9.01", "2.02,9.01"],
                }
            }
        }
    ).encode()

    def fake_fetch(url: str, limit=1000000):
        if "submissions/CIK" in url:
            return 200, "application/json", sample_json
        if url.endswith("-index-headers.html"):
            if "000003" in url:
                stamp = "20250201140000"
            elif "000002" in url:
                stamp = "20250201130000"
            else:
                stamp = "20250201120000"
            return 200, "text/html", f"<ACCEPTANCE-DATETIME>{stamp}".encode()
        if url.endswith("a8k.htm"):
            return 200, "text/html", b"EARNINGS RELEASE RESULTS"
        if url.endswith("a8ka.htm"):
            return 200, "text/html", b"EARNINGS RELEASE AMENDMENT"
        raise AssertionError(f"unexpected SEC URL: {url}")

    monkeypatch.setattr(census, "fetch", fake_fetch)

    result = census.sec_submission_census()
    issuer = result["issuer_results"]["AAPL"]

    assert issuer["amendment_count"] == 1
    assert issuer["pairing_excludes_amended_8k"] is True
    assert issuer["paired_10k_count"] == 1
    event = issuer["paired_10k_events"][0]
    assert event["paired_8k_accession"] == "0000320193-25-000002"
    assert event["paired_8k_is_amendment"] is False
