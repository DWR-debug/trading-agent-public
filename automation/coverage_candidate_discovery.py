"""Coverage-only discovery for a deterministic successor to T039.

The candidate pool and ordering are fixed in source. This module measures only
data availability and never evaluates strategy performance or a holdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from data.yahoo_loader import load_yahoo_history
from research.asset_universes import list_universes

ROOT = Path(__file__).resolve().parents[1]

TARGET_COUNT = 3520
CANDIDATE_POOL = (
    "BIV",
    "BSV",
    "DBV",
    "DGL",
    "FXB",
    "JNK",
    "RJI",
    "UDN",
    "VCLT",
    "VGIT",
)


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        _canonical(value).encode("utf-8")
    ).hexdigest()


def run_discovery(
    *,
    output: str | Path = "research/runs/coverage_discovery/t040_candidates.json",
) -> dict:
    if settings.PAPER_ONLY is not True:
        raise RuntimeError("Coverage discovery requires PAPER_ONLY=True.")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError(
            "Coverage discovery requires LIVE_TRADING_ENABLED=False."
        )
    if len(CANDIDATE_POOL) != len(set(CANDIDATE_POOL)):
        raise RuntimeError("Candidate pool contains duplicates.")

    used_symbols = {
        symbol
        for universe in list_universes()
        for symbol in universe.symbols
    }
    reserved_replacement = None
    reserved_path = (
        ROOT
        / "research"
        / "preregistrations"
        / "trial_040_network_momentum_2026_09_24.json"
    )
    if reserved_path.exists():
        try:
            reserved_replacement = json.loads(
                reserved_path.read_text(encoding="utf-8")
            ).get("replacement", {}).get("replaced_with")
        except (OSError, json.JSONDecodeError):
            reserved_replacement = None
    if reserved_replacement:
        used_symbols.discard(reserved_replacement)

    overlap = sorted(
        symbol
        for symbol in CANDIDATE_POOL
        if symbol in used_symbols
    )
    if overlap:
        raise RuntimeError(
            "Candidate pool overlaps an existing universe: "
            + ", ".join(overlap)
        )

    results = []
    for symbol in CANDIDATE_POOL:
        quality: dict[str, int] = {}
        try:
            bars = load_yahoo_history(
                symbol,
                "1d",
                TARGET_COUNT,
                allow_partial=True,
                skip_invalid_ohlc=True,
                quality_report=quality,
            )
            count = len(bars)
            status = (
                "COVERAGE_VALID"
                if count == TARGET_COUNT
                else "DATA_INVALID"
            )
            results.append({
                "symbol": symbol,
                "count": count,
                "status": status,
                "start": bars[0].timestamp.isoformat() if bars else None,
                "end": bars[-1].timestamp.isoformat() if bars else None,
                "quality": quality,
            })
        except ValueError as exc:
            results.append({
                "symbol": symbol,
                "count": 0,
                "status": "DATA_INVALID",
                "start": None,
                "end": None,
                "quality": quality,
                "error": str(exc),
            })

    valid = [
        item["symbol"]
        for item in results
        if item["status"] == "COVERAGE_VALID"
    ]

    payload = {
        "schema_version": "1.0",
        "discovery_id": "T040-COVERAGE-CANDIDATES-2026-09-24",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "target_count": TARGET_COUNT,
        "candidate_pool": list(CANDIDATE_POOL),
        "selection_rule": (
            "The first coverage-valid symbol in the fixed source order "
            "may be used as the sole replacement candidate for a new "
            "pre-registered trial. No performance metric is consulted."
        ),
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "results": results,
        "coverage_valid_candidates": valid,
        "next_deterministic_candidate": valid[0] if valid else None,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    payload["fingerprint"] = _fingerprint(payload)

    path = Path(output)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="research/runs/coverage_discovery/t040_candidates.json",
    )
    args = parser.parse_args()

    report = run_discovery(output=args.output)
    print(
        "COVERAGE_DISCOVERY_STATUS:",
        "CANDIDATES_AVAILABLE"
        if report["coverage_valid_candidates"]
        else "NO_COVERAGE_VALID_CANDIDATE",
    )
    print(
        "NEXT_DETERMINISTIC_CANDIDATE:",
        report["next_deterministic_candidate"],
    )
    print(
        "DISCOVERY_FINGERPRINT:",
        report["fingerprint"],
    )


if __name__ == "__main__":
    main()
