"""Fail-closed H06-P2 readiness contract.

Binds the corrected global-ranking signal definition to the already reconciled
H06 PIT evidence. This is a design/readiness receipt only: it performs no
forward-return, P&L, holdout, parameter, asset, threshold, horizon, or
candidate-selection work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation import h06_p2_signal as signal

ROOT = Path(__file__).resolve().parents[1]
PIT_PATH = ROOT / "research/evidence/h06_pit_independent_reproduction_2026_10_01.json"
EXPECTED_SYMBOLS = signal.SYMBOLS
EXPECTED_SECTORS = signal.SECTOR_MAP
REQUIRED_PIT_STATUS = "PIT_REPRODUCED_RECONCILED"
EXPECTED_DECISION_POINTS = 2545


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_closes() -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for symbol_index, symbol in enumerate(EXPECTED_SYMBOLS):
        out[symbol] = [
            100.0 + 0.17 * idx + 0.031 * symbol_index + ((idx + symbol_index) % 7) * 0.01
            for idx in range(340)
        ]
    return out


def validate() -> dict:
    pit = json.loads(PIT_PATH.read_text(encoding="utf-8"))
    if pit.get("status") != REQUIRED_PIT_STATUS:
        raise SystemExit("H06P2_READINESS_PIT_STATUS_INVALID")
    if pit.get("governance", {}).get("performance_trial_authorized") is not False:
        raise SystemExit("H06P2_READINESS_PIT_AUTHORIZATION_INVALID")
    if pit.get("governance", {}).get("holdout_evaluation") is not False:
        raise SystemExit("H06P2_READINESS_PIT_HOLDOUT_INVALID")
    if pit.get("checked_decision_points") != EXPECTED_DECISION_POINTS:
        raise SystemExit("H06P2_READINESS_DECISION_POINT_COUNT_INVALID")

    signal_def = pit.get("signal_definition", {})
    if signal_def.get("formation_lookback_sessions") != signal.LOOKBACK:
        raise SystemExit("H06P2_READINESS_LOOKBACK_MISMATCH")
    if signal_def.get("skip_sessions") != signal.SKIP:
        raise SystemExit("H06P2_READINESS_SKIP_MISMATCH")
    if signal_def.get("residualization") != "equal_weight_sector_demean":
        raise SystemExit("H06P2_READINESS_RESIDUALIZATION_MISMATCH")
    if signal_def.get("action_rule") != "decision_bar_next_bar":
        raise SystemExit("H06P2_READINESS_ACTION_RULE_MISMATCH")

    if tuple(signal.SYMBOLS) != tuple(EXPECTED_SYMBOLS):
        raise SystemExit("H06P2_READINESS_SYMBOL_ORDER_MISMATCH")
    if set(EXPECTED_SECTORS) != {
        "technology",
        "healthcare",
        "industrials",
        "consumer_staples",
        "utilities",
    }:
        raise SystemExit("H06P2_READINESS_SECTOR_KEYS_INVALID")
    if any(len(members) != 3 for members in EXPECTED_SECTORS.values()):
        raise SystemExit("H06P2_READINESS_SECTOR_CARDINALITY_INVALID")
    if len(EXPECTED_SYMBOLS) != 15 or sum(len(v) for v in EXPECTED_SECTORS.values()) != 15:
        raise SystemExit("H06P2_READINESS_UNIVERSE_SIZE_INVALID")

    closes = synthetic_closes()
    arms = signal.build_arms(closes, 300)
    expected_arm_ids = {
        "H06-P2-RAW-GLOBAL-T5/B5",
        "H06-P2-RESIDUAL-GLOBAL-T5/B5",
    }
    if set(arms) != expected_arm_ids:
        raise SystemExit("H06P2_READINESS_ARM_SET_INVALID")
    for arm_id, arm in arms.items():
        weights = arm["weights"]
        if signal.gross_exposure(weights) != 1.0:
            raise SystemExit(f"H06P2_READINESS_GROSS_INVALID:{arm_id}")
        if signal.net_exposure(weights) != 0.0:
            raise SystemExit(f"H06P2_READINESS_NET_INVALID:{arm_id}")
        if sum(v == signal.WEIGHT for v in weights.values()) != signal.TOP_K:
            raise SystemExit(f"H06P2_READINESS_LONG_COUNT_INVALID:{arm_id}")
        if sum(v == -signal.WEIGHT for v in weights.values()) != signal.TOP_K:
            raise SystemExit(f"H06P2_READINESS_SHORT_COUNT_INVALID:{arm_id}")

    return {
        "schema_version": "1.0",
        "task_id": "H06-P2-READINESS-2026-10-01",
        "status": "H06_P2_READINESS_VALIDATED",
        "signal_source_sha256": sha256_file(ROOT / "automation/h06_p2_signal.py"),
        "pit_receipt_sha256": sha256_file(PIT_PATH),
        "pit_check_fingerprint": pit["reconciliation"]["check_fingerprint"],
        "pit_coverage_fingerprint": pit["data_contract"]["coverage_fingerprint"],
        "pit_snapshot_fingerprint": pit["data_contract"]["snapshot_fingerprint"],
        "checked_decision_points": pit["data_contract"]["checked_decision_points"],
        "fixed_signal": {
            "formation_lookback_sessions": signal.LOOKBACK,
            "skip_sessions": signal.SKIP,
            "global_top_k": signal.TOP_K,
            "per_name_weight": signal.WEIGHT,
            "gross_exposure": 1.0,
            "net_exposure": 0.0,
        },
        "universe": {
            "symbol_count": len(EXPECTED_SYMBOLS),
            "sector_count": len(EXPECTED_SECTORS),
            "symbols": list(EXPECTED_SYMBOLS),
            "sector_map": {k: list(v) for k, v in EXPECTED_SECTORS.items()},
        },
        "synthetic_contract": {
            "deterministic_arms": True,
            "fixed_gross_exposure": True,
            "fixed_zero_net_exposure": True,
            "fixed_long_short_counts": True,
        },
        "governance": {
            "performance": False,
            "holdout": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "promotion": False,
            "performance_authorized": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/runs/self_hosted/h06_p2_readiness/result.json"),
    )
    args = parser.parse_args()
    result = validate()
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    path = args.output if args.output.is_absolute() else ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("H06P2_STATUS=" + result["status"])
    print("H06P2_CHECKED_DECISION_POINTS=" + str(result["checked_decision_points"]))
    print("H06P2_RECEIPT_FINGERPRINT=" + result["receipt_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
