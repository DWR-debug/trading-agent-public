import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_q171_issuer_url_map_is_frozen_and_q107_bound():
    data = json.loads(
        (ROOT / "research/governance/q171_issuer_web_url_map_2026_10_03.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["universe_source"] == "research/evidence/q107_coverage_result.json"
    assert data["universe_fingerprint"] == (
        "18571a7871f72b8018905c10c289724bb5cf976ab7fa4f9f424599ddc727fbd2"
    )
    assert [x["symbol"] for x in data["symbols"]] == [
        "SPGI",
        "NDAQ",
        "AMP",
        "RJF",
        "WMB",
        "VLO",
        "DVN",
        "EMN",
    ]
    assert len({x["canonical_public_url"] for x in data["symbols"]}) == 8


def test_q171_webstate_coverage_is_discovery_only():
    text = (ROOT / "automation/q171_webstate_coverage.py").read_text(encoding="utf-8")
    assert "CAPTURE_FOUND" in text
    assert '"performance": False' in text
    assert '"selection": False' in text
    assert '"ranking": False' in text
    assert '"live_execution": False' in text
    assert "CC-MAIN-2025-43" in text
