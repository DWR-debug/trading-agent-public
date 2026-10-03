"""Q171 deterministic issuer web-state compiler.

Discovery/PIT feasibility only. This module compiles state transitions from a
frozen Common Crawl CDXJ capture history. It never uses returns, outcomes,
ranking, tuning, holdout selection, or live execution.

The conservative information boundary is the Common Crawl capture timestamp.
The compiler therefore makes no claim about exact first-public-availability;
downstream use must remain next-eligible-session or later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAP_PATH = Path("research/governance/q171_issuer_web_url_map_2026_10_03.json")
EXPECTED_SYMBOLS = ["SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN"]


def digest(value: object) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _timestamp(value: object) -> str:
    text = str(value)
    if len(text) != 14 or not text.isdigit():
        raise ValueError("Q171_INVALID_CAPTURE_TIMESTAMP")
    return text


def _row_key(row: dict[str, Any]) -> tuple[str, str, int, int]:
    return (
        _timestamp(row["timestamp"]),
        str(row["digest"]),
        int(row["offset"]),
        int(row["length"]),
    )


def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []

    unique: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            raise ValueError("Q171_CAPTURE_ROW_NOT_OBJECT")
        key = _row_key(raw)
        unique[key] = {
            "timestamp": key[0],
            "digest": key[1],
            "offset": key[2],
            "length": key[3],
            "indexed_url": str(raw.get("indexed_url", "")),
        }

    by_timestamp: dict[str, list[dict[str, Any]]] = {}
    for row in unique.values():
        by_timestamp.setdefault(row["timestamp"], []).append(row)

    normalized: list[dict[str, Any]] = []
    for timestamp in sorted(by_timestamp):
        candidates = sorted(
            by_timestamp[timestamp],
            key=lambda row: (
                row["digest"],
                row["offset"],
                row["length"],
                row["indexed_url"],
            ),
        )
        digests = {row["digest"] for row in candidates}
        if len(digests) > 1:
            raise ValueError("Q171_TIMESTAMP_DIGEST_CONFLICT")
        normalized.append(candidates[0])
    return normalized


def compile_symbol(
    symbol: str,
    capture_rows: list[dict[str, Any]],
    *,
    cutoff_timestamp: str | None = None,
) -> dict[str, Any]:
    rows = _normalize_rows(capture_rows)
    cutoff = _timestamp(cutoff_timestamp) if cutoff_timestamp is not None else None
    if cutoff is not None:
        rows = [row for row in rows if row["timestamp"] <= cutoff]

    states: list[dict[str, Any]] = []
    previous_digest: str | None = None
    for row in rows:
        current_digest = row["digest"]
        if previous_digest is None:
            state = "BASELINE"
        elif current_digest == previous_digest:
            state = "STATE_UNCHANGED"
        else:
            state = "STATE_CHANGE"
        states.append(
            {
                "symbol": symbol,
                "capture_timestamp": row["timestamp"],
                "state": state,
                "capture_digest": current_digest,
                "observed_after": row["timestamp"],
                "information_boundary": "COMMON_CRAWL_CAPTURE_TIMESTAMP",
                "downstream_eligibility": "NEXT_ELIGIBLE_SESSION_OR_LATER",
            }
        )
        previous_digest = current_digest

    return {
        "symbol": symbol,
        "status": "NO_CAPTURE_HISTORY" if not rows else "COMPILED",
        "capture_count": len(rows),
        "states": states,
    }


def synthetic_future_invariance() -> dict[str, bool]:
    base = [
        {
            "timestamp": "20250101000000",
            "digest": "AAA",
            "offset": 1,
            "length": 10,
        },
        {
            "timestamp": "20250102000000",
            "digest": "BBB",
            "offset": 2,
            "length": 10,
        },
    ]
    future = base + [
        {
            "timestamp": "20260101000000",
            "digest": "CCC",
            "offset": 3,
            "length": 10,
        }
    ]
    cutoff = "20251231235959"
    first = compile_symbol("TEST", base)
    bounded = compile_symbol("TEST", future, cutoff_timestamp=cutoff)
    future_free_state = compile_symbol("TEST", base)
    bounded_states = bounded["states"]
    return {
        "future_row_invariance": bounded_states == first["states"],
        "future_row_after_cutoff_not_visible": bounded_states == future_free_state["states"],
    }


def run(coverage_path: Path, output: Path) -> dict[str, Any]:
    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    symbols = [item["symbol"] for item in mapping["symbols"]]
    if symbols != EXPECTED_SYMBOLS:
        raise RuntimeError(f"Q171_FROZEN_UNIVERSE_MISMATCH:{symbols!r}")

    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    if coverage.get("url_map_fingerprint") != digest(mapping):
        raise RuntimeError("Q171_URL_MAP_FINGERPRINT_MISMATCH")
    if coverage.get("scientific_boundary", {}).get("performance") is not False:
        raise RuntimeError("Q171_COVERAGE_BOUNDARY_INVALID")

    compiled: dict[str, Any] = {}
    for symbol, item in coverage.get("results", {}).items():
        if item.get("status") != "CAPTURE_FOUND":
            continue
        compiled[symbol] = compile_symbol(symbol, item.get("capture_rows", []))

    mutations = synthetic_future_invariance()
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-Q171-WEBSTATE-STATE-COMPILER",
        "status": "Q171_WEBSTATE_STATE_COMPILER_COMPLETED",
        "coverage_receipt_fingerprint": coverage.get("receipt_fingerprint"),
        "url_map_fingerprint": digest(mapping),
        "compiled_states": compiled,
        "summary": {
            "frozen_issuers": len(symbols),
            "issuers_with_capture_history": len(compiled),
            "total_compiled_states": sum(
                int(item["capture_count"]) for item in compiled.values()
            ),
        },
        "synthetic_mutation_checks": mutations,
        "information_boundary": {
            "source_clock": "COMMON_CRAWL_CAPTURE_TIMESTAMP",
            "exact_public_availability_claim": False,
            "same_day_use": False,
            "future_capture_invariance_required": True,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    if not all(mutations.values()):
        raise RuntimeError("Q171_SYNTHETIC_MUTATION_CHECK_FAILED")
    payload["receipt_fingerprint"] = digest(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage_path", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.coverage_path, args.output)
    return 0 if result["status"] == "Q171_WEBSTATE_STATE_COMPILER_COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
