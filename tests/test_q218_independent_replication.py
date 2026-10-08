from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "research/governance/q218_independent_replication_contract_2026_10_08.json"
PRIMARY = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"


def test_replication_contract_is_frozen_and_symbol_disjoint():
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert data["status"] == "FROZEN_INDEPENDENT_REPLICATION_CONTRACT"
    assert data["source_trial_id"] == "T-2026-10-08-Q218-PERFORMANCE-01"
    assert data["replication_trial_id"] == "T-2026-10-08-Q218-REPLICATION-01"
    assert data["base_contract_sha256"] == hashlib.sha256(PRIMARY.read_bytes()).hexdigest()
    assert data["universe"]["issuers"] == {
        "GOOGL": "1652044",
        "META": "1326801",
        "ORCL": "1341439",
        "PFE": "78003",
    }
    assert data["replication_boundaries"]["fresh_symbol_disjoint"] is True
    assert data["replication_boundaries"]["no_primary_result_reuse_for_rule_changes"] is True
    assert data["replication_boundaries"]["no_post_pass_optimization"] is True
    assert data["feature_construction"]["topic_hash_buckets"] == 64
    assert data["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_replication_scripts_run_as_files():
    for name in (
        "automation/q218_independent_replication_event_gate.py",
        "automation/q218_independent_replication_input_freeze.py",
        "automation/q218_independent_replication_preperformance.py",
        "automation/q218_independent_replication_executor.py",
    ):
        completed = subprocess.run(
            [sys.executable, name, "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, f"{name}: {completed.stderr}"


def test_executor_is_separate_from_primary_trial_id():
    text = (ROOT / "automation/q218_independent_replication_executor.py").read_text(encoding="utf-8")
    assert 'TRIAL_ID="T-2026-10-08-Q218-REPLICATION-01"' in text
    assert 'SOURCE_TRIAL_ID="T-2026-10-08-Q218-PERFORMANCE-01"' in text
    assert '"primary_performance_output_used_for_rule_changes":False' in text
