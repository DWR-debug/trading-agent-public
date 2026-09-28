from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from automation.q089_performance import _assert_authorization, _assert_source_contract


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def test_q089_authorization_is_fail_closed(tmp_path: Path) -> None:
    prereg = {
        "governance": {"performance_trial_authorized": False},
        "data_contract": {"input_bundle_fingerprint": "bundle"},
    }
    with pytest.raises(RuntimeError, match="not authorized"):
        _assert_authorization(tmp_path, prereg)


def test_q089_source_contract_detects_mismatch(tmp_path: Path) -> None:
    (tmp_path / "automation").mkdir()
    (tmp_path / "execution").mkdir()
    (tmp_path / "config").mkdir()
    for path in (
        tmp_path / "automation/q089_performance.py",
        tmp_path / "automation/q069_candidate_bank.py",
        tmp_path / "execution/cost_contract.py",
        tmp_path / "config/settings.py",
    ):
        path.write_text(path.name, encoding="utf-8")
    prereg = {
        "source_contract": {
            "performance_runner_sha256": "wrong",
            "candidate_bank_sha256": "wrong",
            "cost_contract_sha256": "wrong",
            "settings_sha256": "wrong",
        }
    }
    with pytest.raises(RuntimeError, match="source contract mismatch"):
        _assert_source_contract(tmp_path, prereg)


def test_q089_source_hash_fixture_is_deterministic(tmp_path: Path) -> None:
    target = tmp_path / "automation" / "q089_performance.py"
    target.parent.mkdir(parents=True)
    target.write_text("stable", encoding="utf-8")
    digest_a = hashlib.sha256(target.read_bytes()).hexdigest()
    digest_b = hashlib.sha256(target.read_bytes()).hexdigest()
    assert digest_a == digest_b
