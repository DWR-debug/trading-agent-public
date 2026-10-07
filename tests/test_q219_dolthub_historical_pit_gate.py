from pathlib import Path
import json
from automation.q219_dolthub_historical_pit_gate import (
    TARGET_DATE, TARGET_SYMBOLS, API_BASE, HEAD_LOG_LIMIT,
    BOUNDED_HISTORY_SCAN_LIMIT, QUERY_TIMEOUT_SECONDS,
    MAX_TRANSIENT_QUERY_ATTEMPTS,
)

ROOT = Path(__file__).parents[1]

def test_q219_historical_pit_contract_is_frozen():
    assert TARGET_DATE == "2025-08-01"
    assert TARGET_SYMBOLS == ["AAPL","AMZN","DIS","JPM","MSFT","NVDA","WMT","XOM"]
    assert HEAD_LOG_LIMIT == 50
    assert API_BASE.endswith("/post-no-preference/options/master")


def test_q219_top4_routes_historical_pit_gate():
    workflow = (ROOT / ".github/workflows/top4-candidate-slot-research.yml").read_text(encoding="utf-8")
    capacity = (ROOT / "automation/top4_candidate_capacity.py").read_text(encoding="utf-8")
    assert "Q219" in workflow
    assert "automation/q219_dolthub_historical_pit_gate.py" in capacity
    assert "q219_dolthub_historical_pit_gate.json" in workflow
    assert 'automation/q219_dolthub_historical_pit_gate.py' in workflow
    lane = (ROOT / 'automation/top4_candidate_capacity.py').read_text(encoding='utf-8')
    assert 'automation/q219_dolthub_historical_pit_gate.py' in lane
    assert 'q219_dolthub_historical_pit_gate.json' in lane


def test_q219_pit_gate_is_non_authorizing():
    gate = (ROOT / "automation/q219_dolthub_historical_pit_gate.py").read_text(encoding="utf-8")
    for token in ("performance_authorization", "holdout_selection", "ranking", "tuning", "promotion", "live_execution"):
        assert f'"{token}": False' in gate


def test_q219_pit_gate_uses_targeted_pre_target_history_query():
    gate = (ROOT / 'automation/q219_dolthub_historical_pit_gate.py').read_text(encoding='utf-8')
    assert 'WHERE date <= ' in gate
    assert 'ORDER BY date DESC LIMIT 1' in gate
    assert 'prior_commit_query' in gate


def test_q219_pit_snapshots_prefer_pre_target_commit():
    gate = (ROOT / 'automation/q219_dolthub_historical_pit_gate.py').read_text(encoding='utf-8')
    assert 'chosen.append(prior_commit)' in gate
    assert 'str(row.get("commit_hash")) != str(prior_commit.get("commit_hash"))' in gate


def test_q219_history_uses_system_table_fastpath():
    gate = (ROOT / 'automation/q219_dolthub_historical_pit_gate.py').read_text(encoding='utf-8')
    assert 'FROM dolt_log' in gate
    assert "message LIKE 'option_chain % update'" in gate
    assert "FROM DOLT_LOG(" not in gate


def test_q219_history_scan_is_bounded_and_filtered_in_memory():
    gate = (ROOT / 'automation/q219_dolthub_historical_pit_gate.py').read_text(encoding='utf-8')
    assert 'FROM dolt_log' in gate
    assert "message LIKE 'option_chain % update'" in gate
    assert 'LIMIT {HEAD_LOG_LIMIT}' in gate
    assert 'summary_query = ' not in gate
    assert BOUNDED_HISTORY_SCAN_LIMIT >= HEAD_LOG_LIMIT


def test_q219_dolthub_retry_policy_is_strictly_bounded():
    assert QUERY_TIMEOUT_SECONDS == 90
    assert MAX_TRANSIENT_QUERY_ATTEMPTS == 2


def test_q219_fetch_sql_retries_transient_deadline_once(monkeypatch):
    import urllib.request
    from automation import q219_dolthub_historical_pit_gate as gate

    calls = {"n": 0}

    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b'{"query_execution_status":"Success","rows":[{"ok":1}]}'

    def fake_urlopen(request, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("timed out")
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(gate.time, "sleep", lambda seconds: None)

    result = gate.fetch_sql("SELECT 1")
    assert result["rows"] == [{"ok": 1}]
    assert calls["n"] == 2
