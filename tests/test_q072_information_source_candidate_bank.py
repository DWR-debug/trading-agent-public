import json
from pathlib import Path


def test_q072_candidate_bank_is_unranked_and_safe():
    p=json.loads(Path("research/exploration/q072_information_candidate_bank_2026_09_28.json").read_text(encoding="utf-8"))
    assert p["status"]=="DESIGN_ONLY"
    assert len(p["candidates"])==10
    assert p["governance"]["performance_trial_authorized"] is False
    assert p["governance"]["family_ranking"] is False
    assert p["governance"]["holdout_used_for_selection"] is False
    assert p["safety"]=={
        "paper_only":True,
        "live_trading_enabled":False,
        "orders_enabled":False,
        "automatic_promotion":False,
    }


def test_q072_document_is_explicitly_design_only():
    t=Path("docs/research_design/Q072-information-source-candidate-bank-2026-09-28.md").read_text(encoding="utf-8")
    assert "DESIGN_ONLY" in t
    assert "No candidate has been ranked" in t
    for token in ("FINRA","SEC Form 4","ALFRED","CFTC","Wikimedia","GDELT"):
        assert token in t
    assert "X1" in t and "X2" in t
