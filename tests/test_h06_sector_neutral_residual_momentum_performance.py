import json
from pathlib import Path
from config import settings

ROOT=Path(__file__).resolve().parents[1]
PREREG=ROOT/"research"/"preregistrations"/"h06_sector_neutral_residual_momentum_performance_2026_09_27.json"
AUTH=ROOT/"research"/"authorizations"/"h06_sector_neutral_residual_momentum_performance_2026_09_27.json"

def test_h06_performance_prereg_is_fixed_and_safe():
    d=json.loads(PREREG.read_text(encoding="utf-8"))
    assert d["trial_id"]=="T-2026-09-27-049"
    assert d["fixed_signal"]["formation_lookback_sessions"]==252
    assert d["fixed_signal"]["skip_sessions"]==21
    assert d["fixed_signal"]["top_n"]==2
    assert d["execution"]["rebalance_every_sessions"]==21
    assert d["execution"]["gross_exposure"]==1.0
    assert d["evaluation"]["parameter_search"] is False
    assert d["evaluation"]["asset_search"] is False
    assert d["evaluation"]["holdout_blind"] is True
    assert d["authorization"]["performance_trial_authorized"] is False
    assert d["safety"]=={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}

def test_h06_authorization_is_bound_to_exact_artifacts():
    a=json.loads(AUTH.read_text(encoding="utf-8"))
    assert a["trial_id"]=="T-2026-09-27-049-PERFORMANCE"
    assert a["authorized"] is True
    assert a["performance_execution_authorized"] is True
    assert a["execution_scope"]=="PERFORMANCE"
    assert a["coverage_artifact_id"]==10901872543
    assert a["coverage_workflow_run_id"]==36230165868
    assert a["snapshot_fingerprint"]=="22a32d2c6785b4f04f935148d3bd3e6978af8eb49e3a32d46073ee3f0cb93522"
    assert a["source_mechanism_result_fingerprint"]=="45546b7a2b69c39f961cab85f9ab091d165f5e9a711777fb23dd717f82fc9fbd"
    assert settings.PAPER_ONLY is True
    assert settings.LIVE_TRADING_ENABLED is False
    assert settings.ORDERS_ENABLED is False
    assert settings.AUTOMATIC_PROMOTION is False
