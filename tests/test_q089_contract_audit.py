from __future__ import annotations

import ast
import json

from automation.q089_contract_audit import audit


def test_audit_detects_result_requested_candle_drift(monkeypatch, tmp_path) -> None:
    (tmp_path / "research/preregistrations").mkdir(parents=True)
    (tmp_path / "research/governance").mkdir(parents=True)
    (tmp_path / "automation").mkdir(parents=True)
    (tmp_path / "execution").mkdir(parents=True)
    (tmp_path / "config").mkdir(parents=True)

    prereg = {
        "trial_id": "T-2026-09-28-089-PERFORMANCE",
        "requested_candles": 5000,
        "target_common_candles": 3500,
        "research_periods": 2798,
        "holdout_periods": 700,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "source_contract": {},
    }
    (tmp_path / "research/preregistrations/q089_performance_2026_09_28.json").write_text(
        json.dumps(prereg), encoding="utf-8"
    )
    registry = {
        "active_trials": [{
            "code": "089",
            "trial_id": prereg["trial_id"],
            "performance_authorization_allowed": False,
        }]
    }
    (tmp_path / "research/governance/active_research_registry.json").write_text(
        json.dumps(registry), encoding="utf-8"
    )

    perf = """
N=3500; RESEARCH=2798; HOLDOUT=700
result={"requested_candles":4000}
"""
    coverage = """
REQUESTED=5000; RAW=5000; TARGET=3500
"""
    (tmp_path / "automation/q089_performance.py").write_text(perf, encoding="utf-8")
    (tmp_path / "automation/q089_coverage_pit.py").write_text(coverage, encoding="utf-8")
    for path in (
        tmp_path / "automation/q069_candidate_bank.py",
        tmp_path / "execution/cost_contract.py",
        tmp_path / "config/settings.py",
    ):
        path.write_text("fixture", encoding="utf-8")

    result = audit(tmp_path)
    codes = {item["code"] for item in result["findings"]}
    assert result["status"] == "FINDINGS_PRESENT"
    assert "Q089_REPORT_REQUESTED_CANDLES_MISMATCH" in codes
    assert "Q089_SOURCE_CONTRACT_MISMATCH" in codes


def test_result_literal_helper_is_ast_based() -> None:
    from automation.q089_contract_audit import _find_result_literal
    tree = ast.parse('result={"requested_candles": 123}')
    assert _find_result_literal(tree, "requested_candles") == 123


def test_audit_requires_fail_closed_execution_guards(tmp_path) -> None:
    # Reuse the fixture strategy above, but make the performance runner omit
    # both authorization/source-contract calls. The audit must block.
    (tmp_path / "research/preregistrations").mkdir(parents=True)
    (tmp_path / "research/governance").mkdir(parents=True)
    (tmp_path / "automation").mkdir(parents=True)
    (tmp_path / "execution").mkdir(parents=True)
    (tmp_path / "config").mkdir(parents=True)
    prereg = {
        "trial_id": "T-2026-09-28-089-PERFORMANCE",
        "requested_candles": 5000,
        "target_common_candles": 3500,
        "research_periods": 2798,
        "holdout_periods": 700,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "source_contract": {},
    }
    (tmp_path / "research/preregistrations/q089_performance_2026_09_28.json").write_text(json.dumps(prereg), encoding="utf-8")
    (tmp_path / "research/governance/active_research_registry.json").write_text(
        json.dumps({"active_trials": [{"code": "089", "trial_id": prereg["trial_id"], "performance_authorization_allowed": False}]}),
        encoding="utf-8",
    )
    (tmp_path / "automation/q089_performance.py").write_text(
        "N=3500; RESEARCH=2798; HOLDOUT=700\nrequested={'requested_candles':5000}\n",
        encoding="utf-8",
    )
    (tmp_path / "automation/q089_coverage_pit.py").write_text(
        "REQUESTED=5000; RAW=5000; TARGET=3500\n", encoding="utf-8"
    )
    for path in (
        tmp_path / "automation/q069_candidate_bank.py",
        tmp_path / "execution/cost_contract.py",
        tmp_path / "config/settings.py",
    ):
        path.write_text("fixture", encoding="utf-8")

    result = audit(tmp_path)
    codes = {item["code"] for item in result["findings"]}
    assert "Q089_FAIL_CLOSED_GUARD_MISSING" in codes

def test_audit_accepts_valid_authorized_q089_state(tmp_path) -> None:
    import hashlib

    (tmp_path / "research/preregistrations").mkdir(parents=True)
    (tmp_path / "research/governance").mkdir(parents=True)
    (tmp_path / "research/authorizations").mkdir(parents=True)
    (tmp_path / "automation").mkdir(parents=True)
    (tmp_path / "execution").mkdir(parents=True)
    (tmp_path / "config").mkdir(parents=True)

    perf_body = '''
N=3500
RESEARCH=2798
HOLDOUT=700
def _assert_authorization(): pass
def _assert_source_contract(): pass
def run():
    _assert_authorization()
    _assert_source_contract()
result={"requested_candles":5000}
'''
    coverage_body = "REQUESTED=5000\nRAW=5000\nTARGET=3500\n"
    (tmp_path / "automation/q089_performance.py").write_text(perf_body, encoding="utf-8")
    (tmp_path / "automation/q089_coverage_pit.py").write_text(coverage_body, encoding="utf-8")
    candidate = tmp_path / "automation/q069_candidate_bank.py"
    cost = tmp_path / "execution/cost_contract.py"
    settings = tmp_path / "config/settings.py"
    candidate.write_text("fixture", encoding="utf-8")
    cost.write_text("fixture", encoding="utf-8")
    settings.write_text("fixture", encoding="utf-8")

    prereg = {
        "trial_id": "T-2026-09-28-089-PERFORMANCE",
        "requested_candles": 5000,
        "target_common_candles": 3500,
        "research_periods": 2798,
        "holdout_periods": 700,
        "governance": {"performance_trial_authorized": True},
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    prereg["source_contract"] = {
        "performance_runner_path": "automation/q089_performance.py",
        "performance_runner_sha256": hashlib.sha256(
            (tmp_path / "automation/q089_performance.py").read_bytes()
        ).hexdigest(),
        "candidate_bank_path": "automation/q069_candidate_bank.py",
        "candidate_bank_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "cost_contract_path": "execution/cost_contract.py",
        "cost_contract_sha256": hashlib.sha256(cost.read_bytes()).hexdigest(),
        "settings_path": "config/settings.py",
        "settings_sha256": hashlib.sha256(settings.read_bytes()).hexdigest(),
    }
    prereg_path = tmp_path / "research/preregistrations/q089_performance_2026_09_28.json"
    prereg_path.write_text(json.dumps(prereg), encoding="utf-8")
    canonical = json.dumps(
        prereg, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    fp = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    (tmp_path / "research/governance/active_research_registry.json").write_text(
        json.dumps({"active_trials": [{
            "code": "089",
            "trial_id": prereg["trial_id"],
            "performance_authorization_allowed": True,
        }]}),
        encoding="utf-8",
    )
    (tmp_path / "research/authorizations/q089_performance_2026_09_28.json").write_text(
        json.dumps({
            "trial_id": prereg["trial_id"],
            "authorized": True,
            "performance_execution_authorized": True,
            "one_shot": True,
            "preregistration_fingerprint": fp,
        }),
        encoding="utf-8",
    )

    result = audit(tmp_path)
    assert result["status"] == "PASS"
    assert result["performance_authorization_changed"] is False
    assert result["performance_executed"] is False
