import json
from pathlib import Path

import pytest

from automation.q171_webstate_state_compiler import (
    compile_symbol,
    digest,
    synthetic_future_invariance,
)

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "research/governance/q171_issuer_web_url_map_2026_10_03.json"


def test_q171_compiler_marks_digest_transition_and_freezes_boundary():
    rows = [
        {"timestamp": "20250101000000", "digest": "AAA", "offset": 1, "length": 10},
        {"timestamp": "20250102000000", "digest": "AAA", "offset": 2, "length": 10},
        {"timestamp": "20250103000000", "digest": "BBB", "offset": 3, "length": 10},
    ]
    result = compile_symbol("TEST", rows)
    assert [x["state"] for x in result["states"]] == [
        "BASELINE",
        "STATE_UNCHANGED",
        "STATE_CHANGE",
    ]
    assert all(
        x["information_boundary"] == "COMMON_CRAWL_CAPTURE_TIMESTAMP"
        for x in result["states"]
    )
    assert all(x["downstream_eligibility"] == "NEXT_ELIGIBLE_SESSION_OR_LATER" for x in result["states"])


def test_q171_future_rows_do_not_change_bounded_history():
    checks = synthetic_future_invariance()
    assert checks == {
        "future_row_invariance": True,
        "future_row_after_cutoff_not_visible": True,
    }


def test_q171_same_timestamp_conflicting_digests_fail_closed():
    with pytest.raises(ValueError, match="Q171_TIMESTAMP_DIGEST_CONFLICT"):
        compile_symbol(
            "TEST",
            [
                {"timestamp": "20250101000000", "digest": "AAA", "offset": 1, "length": 10},
                {"timestamp": "20250101000000", "digest": "BBB", "offset": 2, "length": 10},
            ],
        )


def test_q171_cutoff_excludes_future_capture():
    rows = [
        {"timestamp": "20250101000000", "digest": "AAA", "offset": 1, "length": 10},
        {"timestamp": "20260101000000", "digest": "BBB", "offset": 2, "length": 10},
    ]
    result = compile_symbol("TEST", rows, cutoff_timestamp="20251231235959")
    assert result["capture_count"] == 1
    assert result["states"][0]["capture_digest"] == "AAA"


def test_q171_frozen_universe_map():
    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    assert [x["symbol"] for x in mapping["symbols"]] == [
        "SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN"
    ]
    assert digest(mapping) == digest(mapping)
