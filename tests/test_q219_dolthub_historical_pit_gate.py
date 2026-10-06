from pathlib import Path
import json
from automation.q219_dolthub_historical_pit_gate import TARGET_DATE, TARGET_SYMBOLS, API_BASE, HEAD_LOG_LIMIT

ROOT = Path(__file__).parents[1]

def test_q219_historical_pit_contract_is_frozen():
    assert TARGET_DATE == "2025-08-01"
    assert TARGET_SYMBOLS == ["AAPL","AMZN","DIS","JPM","MSFT","NVDA","WMT","XOM"]
    assert HEAD_LOG_LIMIT == 50
    assert API_BASE.endswith("/post-no-preference/options/master")


def test_q219_top4_routes_historical_pit_gate():
    workflow = (ROOT / ".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert "automation/q219_dolthub_historical_pit_gate.py" in workflow
    assert "research/preregistrations/q219_dolthub_historical_pit_gate_2026_10_06.json" in workflow
    assert 'automation/q219_dolthub_historical_pit_gate.py' in workflow
    lane = (ROOT / 'automation/top4_candidate_capacity.py').read_text(encoding='utf-8')
    assert 'automation/q219_dolthub_historical_pit_gate.py' in lane
    assert 'q219_dolthub_historical_pit_gate.json' in lane


def test_q219_pit_gate_is_non_authorizing():
    gate = (ROOT / "automation/q219_dolthub_historical_pit_gate.py").read_text(encoding="utf-8")
    for token in ("performance_authorization", "holdout_selection", "ranking", "tuning", "promotion", "live_execution"):
        assert f'"{token}": False' in gate
