import json
from pathlib import Path
from config import settings
from research.asset_universes import get_universe

ROOT=Path(__file__).resolve().parents[1]
PREREG=ROOT/"research"/"preregistrations"/"q022_h2_r1_treasury_release_timing_2026_09_27.json"

def test_q022_h2_r1_preregistration_is_fixed_and_safe():
    d=json.loads(PREREG.read_text(encoding="utf-8"))
    assert d["status"]=="PREREGISTERED_DESIGN_ONLY"
    assert d["trial_id"]=="T-2026-09-27-048R1"
    assert d["parent_trial_id"]=="T-2026-09-27-048"
    assert d["parent_outcome"]=="DATA_INVALID"
    assert d["data_contract"]["target_common_calendar"]==3500
    assert d["selection"]["coverage_discovery_workflow_run_id"]==36320528295
    assert d["selection"]["coverage_discovery_artifact_id"]==10932332338
    assert d["selection"]["coverage_discovery_fingerprint"]=="8c901bc3ac25510a7be3895fa933ff896727a8abb15876f32757ea4860e15903"
    assert d["authorization"]["performance_trial_authorized"] is False
    assert settings.PAPER_ONLY is True
    assert settings.LIVE_TRADING_ENABLED is False
    assert settings.ORDERS_ENABLED is False
    assert settings.AUTOMATIC_PROMOTION is False

def test_q022_h2_r1_universe_is_fixed_and_fresh():
    d=json.loads(PREREG.read_text(encoding="utf-8"))
    u=get_universe(d["universe"])
    assert tuple(u.symbols)==tuple(d["symbols"])
    assert tuple(d["symbols"])==("TAP","CLX","HSY","KR","SYY","STT","USB","TROW","BEN","NTRS","PNC","MET")
    assert len(d["symbols"])==12
