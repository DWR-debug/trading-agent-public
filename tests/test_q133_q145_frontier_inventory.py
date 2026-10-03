from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def test_q133_q145_inventory_is_discovery_only():
    p = ROOT / "research/frontier/q133_q145_candidate_wave_2026_10_03.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["status"] == "DESIGN_INVENTORY_ONLY"
    assert len(data["candidates"]) == 13
    assert data["policy"]["performance_authorized"] is False
    assert data["policy"]["holdout_selection_allowed"] is False
    assert data["policy"]["parameter_search_allowed"] is False
    assert data["safety"]["paper_only"] is True
    assert data["safety"]["live_trading_enabled"] is False
    assert data["safety"]["orders_enabled"] is False
    assert data["safety"]["automatic_promotion"] is False


def test_workflow_lifecycle_registry_marks_manual_s10_diagnostics():
    p = ROOT / "research/governance/workflow_lifecycle_registry_2026_10_03.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["workflow_inventory_count"] == 174
    assert ".github/workflows/s10-runtime-probe.yml" in data["manual_only"]
    assert ".github/workflows/q121r1-sec-reverse-issuer-coverage.yml" in data["canonical_active"]
    assert ".github/workflows/s10-throughput-probe.yml" in data["manual_only"]
    assert ".github/workflows/hosted-deterministic-frontier.yml" in data["canonical_active"]
    assert ".github/workflows/q129-independent-pit-reproduction.yml" in data["canonical_active"]
