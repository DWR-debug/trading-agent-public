from __future__ import annotations

import hashlib
import json
from pathlib import Path

from automation import q218_independent_replication_executor as executor

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_replication_contract_base_fingerprint_is_git_blob_sha() -> None:
    primary_contract = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"
    replication_contract = ROOT / "research/governance/q218_independent_replication_contract_2026_10_08.json"

    data = primary_contract.read_bytes()
    expected = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    recorded = json.loads(replication_contract.read_text(encoding="utf-8"))["base_contract_sha256"]

    assert recorded == expected
    assert executor.git_blob_sha(primary_contract) == expected


def test_git_blob_fingerprint_changes_when_base_contract_changes(tmp_path: Path) -> None:
    source = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"
    original = tmp_path / "contract.json"
    changed = tmp_path / "contract_changed.json"
    original.write_bytes(source.read_bytes())
    changed.write_bytes(source.read_bytes() + b" ")

    assert executor.git_blob_sha(original) != executor.git_blob_sha(changed)
