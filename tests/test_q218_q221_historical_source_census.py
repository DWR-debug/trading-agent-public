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
                }
            }
        }
    ).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name in ["sub.txt", "tag.txt", "dim.txt", "num.txt", "txt.txt"]:
            archive.writestr(name, "fixture")
    zip_bytes = buffer.getvalue()

    seen_submission_urls = []

    def fake_fetch(url: str, limit=1000000):
        if "submissions/CIK" in url:
            seen_submission_urls.append(url)
            return 200, "application/json", sample_json
        if url.endswith("-index-headers.html"):
            return 200, "text/html", b"<ACCEPTANCE-DATETIME>20250215123000 EXHIBIT 99.1 EARNINGS RELEASE"
        if url.endswith(".zip"):
            return 200, "application/zip", zip_bytes
        return 200, "text/html", b"RESEARCH DEVELOPMENT TEST AND EVALUATION COMPETITION TRANSACTION"

    monkeypatch.setattr(census, "fetch", fake_fetch)
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
    assert result["q221_usa_rdtne_census"]["rdtne_marker_found"] is True
    assert Path(tmp_path / "census.json").is_file()
