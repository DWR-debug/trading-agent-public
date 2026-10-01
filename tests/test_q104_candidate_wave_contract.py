from __future__ import annotations

import json
from pathlib import Path

from automation.q104_candidate_wave_contract import validate


def test_q104_design_contract_is_valid():
    root = Path(__file__).parents[1]
    data = json.loads(
        (root / "research/frontier/q104_candidate_wave_2026_10_01.json").read_text(
            encoding="utf-8"
        )
    )
    result = validate(data)
    assert result["status"] == "DESIGN_CONTRACT_VALIDATED"
    assert result["candidate_count"] == 6
    assert result["governance"]["performance_authorization"] is False
    assert result["safety"]["paper_only"] is True
    assert result["safety"]["live_trading_enabled"] is False


def test_q104_candidate_ids_are_unique():
    root = Path(__file__).parents[1]
    data = json.loads(
        (root / "research/frontier/q104_candidate_wave_2026_10_01.json").read_text(
            encoding="utf-8"
        )
    )
    ids = [row["id"] for row in data["candidates"]]
    assert len(ids) == len(set(ids))
    assert all(cid.startswith("Q104:") for cid in ids)
