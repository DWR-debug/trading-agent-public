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


def test_q218_next_session_is_after_closure():
    session = freeze.next_xnys_session(
        __import__("datetime").datetime.fromisoformat("2025-10-31T06:01:26+00:00"),
        "2025-01-01",
        "2026-10-05",
    )
    assert session == "2025-10-31"
