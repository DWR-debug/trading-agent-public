from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from automation import q218_deterministic_performance_executor as executor
from automation import q218_preperformance_robustness as robustness
from automation import q218_performance_input_freeze as freeze


ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"


def test_q218_contract_is_frozen_and_non_authorizing():
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert data["status"] == "FROZEN_PRE_PERFORMANCE_CONTRACT"
    assert data["trial_id"] == executor.TRIAL_ID
    assert data["governance"]["performance_authorized"] is False
    assert data["governance"]["holdout_selection_used"] is False
    assert data["governance"]["parameter_search"] is False
    assert data["outcome_contract"]["holding_sessions"] == 1
    assert data["outcome_contract"]["entry"] == "session open"
    assert data["outcome_contract"]["exit"] == "same-session close"
    assert data["time_contract"]["acceptance_datetime_timezone"] == "America/New_York"
    assert data["time_contract"]["no_implicit_utc"] is True
    assert data["input_bundle"]["source_loader_path"] == "data/yahoo_loader.py"


def test_q218_feature_construction_is_deterministic():
    a = b"<html><body>Alpha beta beta.</body></html>"
    b = b"<html><body>Alpha gamma.</body></html>"
    first = executor.construct_features(a, b)
    second = executor.construct_features(a, b)
    assert first == second
    assert set(first) == {
        "topic_coverage_gap_mandatory_vs_voluntary",
        "omission_asymmetry_by_topic",
        "secondary_framing_gap",
    }


def test_q218_executor_rejects_amended_documents(tmp_path):
    body = b"<html><body>Alpha beta.</body></html>"
    doc = tmp_path / "doc.html"
    header = tmp_path / "header.html"
    raw = tmp_path / "market.json"
    doc.write_bytes(body)
    header.write_bytes(b"<SEC-HEADER/>")
    raw.write_bytes(b"{}")
    contract_sha = hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    bundle = {
        "trial_id": executor.TRIAL_ID,
        "bundle_fingerprint": "",
        "contract_sha256": contract_sha,
        "executor_network_access": False,
        "selection_used": False,
        "parameter_search": False,
        "events": [{
            "issuer": "TEST",
            "ten_k_accession": "A",
            "item_2_02_8k_accession": "B",
            "pair_closure_clock": "2026-01-01T00:00:00Z",
            "action_session": "2026-01-02",
        }],
        "documents": [
            {"accession": "A", "form": "10-K", "path": "doc.html", "sha256": hashlib.sha256(body).hexdigest(), "header_path": "header.html", "header_sha256": hashlib.sha256(b"<SEC-HEADER/>").hexdigest()},
            {"accession": "B", "form": "8-K/A", "path": "doc.html", "sha256": hashlib.sha256(body).hexdigest(), "header_path": "header.html", "header_sha256": hashlib.sha256(b"<SEC-HEADER/>").hexdigest()},
        ],
        "market_bars": [{"symbol":"TEST","session":"2026-01-02","open":100.0,"close":101.0,"raw_response_path":"market.json","raw_response_sha256":hashlib.sha256(b"{}").hexdigest()}],
        "future_cutoff_session":"2026-10-05",
    }
    unsigned = dict(bundle)
    unsigned.pop("bundle_fingerprint")
    bundle["bundle_fingerprint"] = executor.fp(unsigned)
    path = tmp_path / "input_bundle_manifest.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(RuntimeError, match="amended|unsupported"):
        executor.validate_bundle_sources(bundle, tmp_path)


def test_q218_robustness_receipt_schema():
    assert robustness.TRIAL_ID == "T-2026-10-08-Q218-PERFORMANCE-01"
    assert robustness.EXECUTOR.is_file()
    assert robustness.CONTRACT.is_file()


def test_q218_acceptance_datetime_accepts_sec_compact_clock():
    header = b"<SEC-HEADER><ACCEPTANCE-DATETIME>20250204204140</SEC-HEADER>"
    assert freeze.acceptance_datetime(header, "20250204204140") == "2025-02-04T20:41:40-05:00"



def test_q218_input_freezer_records_acceptance_clocks_before_pair_closure(tmp_path, monkeypatch):
    contract = {
        "trial_id": freeze.TRIAL_ID,
        "status": "FROZEN_PRE_PERFORMANCE_CONTRACT",
        "governance": {
            key: False for key in (
                "selection_used", "holdout_selection_used", "parameter_search",
                "threshold_search", "horizon_search", "asset_search",
                "variant_search", "family_ranking", "promotion_decision",
                "performance_authorized",
            )
        },
        "safety": {
            "paper_only": True, "live_trading_enabled": False,
            "orders_enabled": False, "automatic_promotion": False,
        },
        "universe": {"issuers": {"TEST": "1"}},
        "event_pair_population": [[
            "TEST", "0000000001-25-000001", "0000000001-25-000002",
            "2025-02-04T15:00:00", "2025-02-04T16:00:00",
        ]],
        "upstream": {
            "independent_pit_window": {"start": "2025-01-01", "end": "2026-10-05"},
            "future_cutoff_utc": "2026-10-05T23:59:59Z",
        },
    }
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    monkeypatch.setattr(freeze, "CONTRACT", contract_path)
    accessions = ["0000000001-25-000001", "0000000001-25-000002"]
    monkeypatch.setattr(
        freeze, "sec_submission_index",
        lambda cik, root: ({
            "filings": {"recent": {
                "accessionNumber": accessions,
                "form": ["10-K", "8-K"],
                "primaryDocument": ["tenk.html", "earnings.html"],
                "items": ["", "2.02"],
            }}
        }, {}),
    )
    headers = {
        accessions[0]: b"<SEC-HEADER><ACCEPTANCE-DATETIME>20250204150000</SEC-HEADER>",
        accessions[1]: b"<SEC-HEADER><ACCEPTANCE-DATETIME>20250204160000</SEC-HEADER>",
    }
    monkeypatch.setattr(freeze, "accession_header", lambda cik, acc: (headers[acc], f"https://sec.test/{acc}"))
    monkeypatch.setattr(freeze, "primary_document", lambda cik, acc, doc: (f"<html>{doc}</html>".encode(), f"https://sec.test/{acc}/{doc}"))
    monkeypatch.setattr(freeze, "next_xnys_session", lambda closure, start, end: "2025-02-05")
    monkeypatch.setattr(
        freeze, "yahoo_chart",
        lambda symbol, session, root: ({
            "symbol": symbol, "session": session, "open": 100.0, "close": 101.0,
            "raw_response_path": "market_raw/TEST_2025-02-05.json",
            "raw_response_sha256": "0" * 64,
        }, {}),
    )
    receipt_path = tmp_path / "receipt.json"
    receipt = freeze.freeze(tmp_path / "bundle", receipt_path)
    bundle = json.loads((tmp_path / "bundle" / "input_bundle_manifest.json").read_text(encoding="utf-8"))
    assert receipt["status"] == "INPUT_BUNDLE_FROZEN"
    assert bundle["events"][0]["pair_closure_clock"] == "2025-02-04T16:00:00-05:00"
    assert bundle["events"][0]["action_session"] == "2025-02-05"

def test_q218_next_session_is_after_closure():
    session = freeze.next_xnys_session(
        __import__("datetime").datetime.fromisoformat("2025-10-31T06:01:26+00:00"),
        "2025-01-01",
        "2026-10-05",
    )
    assert session == "2025-10-31"


def test_q218_candidate_robustness_delegates_to_canonical_gate():
    from automation import q218_candidate_robustness_receipt as candidate_gate
    result = candidate_gate.build()
    assert result["candidate_id"] == "Q218"
    assert result["status"] == "PRE_FORMAL_ROBUSTNESS_COMPLETED"
    assert result["formalization_allowed"] is False
    assert result["performance_authorization"] is False
    assert result["research_only"] is True


def test_q218_prep_scripts_are_runnable_as_files():
    import subprocess
    import sys

    for name in (
        "automation/q218_candidate_robustness_receipt.py",
        "automation/q218_preperformance_robustness.py",
    ):
        completed = subprocess.run(
            [sys.executable, name, "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
