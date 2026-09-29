from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def test_emit_q089_authorized_preregistration_fingerprint() -> None:
    path = Path("research/preregistrations/q089_performance_2026_09_28.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["governance"]["performance_trial_authorized"] = True
    payload["revision"] = 3
    payload["supersedes"] = "q089_performance_2026_09_28.json@revision-2"
    payload["revision_reason"] = (
        "Authorized once after Q089 coverage/PIT/input-freeze prerequisites, "
        "dual-lane contract audit success, and green master CI/gate checks. "
        "No signal, universe, split, cost, gate, holdout, parameter, threshold, "
        "asset, horizon, variant or performance rule changed."
    )
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    fp = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    pytest.fail(f"Q089_PREREG_FP={fp}")
