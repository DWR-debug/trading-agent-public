"""Coverage/PIT preflight for the fixed turnover-shock research design.

This runner freezes and validates daily OHLCV inputs and next-session calendar
mapping only. It does not calculate signals, returns, P&L, or performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from backtesting.models import Candle
from config import settings
from data.canonical_snapshot import (
    Loader,
    SnapshotSpec,
    build_frozen_snapshot,
    load_frozen_snapshot,
)
from data.yahoo_loader import load_yahoo_history

ROOT = Path(__file__).resolve().parents[1]
PREREGISTRATION = (
    "research/preregistrations/turnover_shock_candidate_2026_09_27.json"
)
TRIAL_ID = "TURNOVER-SHOCK-CANDIDATE-2026-09-27"
UNIVERSE = "turnover_shock_candidate_2026_09_27"
SYMBOLS = (
    "AFL", "ALL", "AVY", "CAH", "CINF", "CPRT",
    "OXY", "PPG", "ROP", "TROW", "TRV", "WMB",
)
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2026, 9, 25)
REQUESTED_CANDLES = 4000
TARGET_COMMON_CANDLES = 3500
MINIMUM_IN_WINDOW_CANDLES = 3500
REFERENCE_BARS = 20
SOURCE_VINTAGE_GUARANTEE = False


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _xnys_sessions(start: date, end: date) -> tuple[date, ...]:
    import exchange_calendars as xcals
    import pandas as pd

    calendar = xcals.get_calendar("XNYS")
    return tuple(
        session.date()
        for session in calendar.sessions_in_range(
            pd.Timestamp(start.isoformat()), pd.Timestamp(end.isoformat())
        )
    )


def _validate_preregistration(spec: dict) -> None:
    expected = {
        "trial_id": TRIAL_ID,
        "interval": "1d",
        "requested_candles": REQUESTED_CANDLES,
        "target_candles": TARGET_COMMON_CANDLES,
        "minimum_in_window_candles": MINIMUM_IN_WINDOW_CANDLES,
    }
    for key, value in expected.items():
        if spec.get(key) != value:
            raise ValueError(f"Preregistration fixed field mismatch: {key}")
    universe = spec.get("fixed_universe", {})
    if universe.get("name") != UNIVERSE or universe.get("symbols") != list(SYMBOLS):
        raise ValueError("Preregistration fixed universe mismatch.")
    study_window = spec.get("study_window", {})
    if (
        study_window.get("start") != STUDY_START.isoformat()
        or study_window.get("end") != STUDY_END.isoformat()
    ):
        raise ValueError("Preregistration fixed study window mismatch.")
    signal = spec.get("signal", {})
    expected_signal = {
        "signal_day": "current_completed_daily_bar",
        "turnover_proxy": "close * volume",
        "reference": "median_turnover_proxy_of_previous_20_completed_daily_bars",
        "shock_rule": "turnover_proxy / reference >= 2.0",
        "direction": "long",
        "entry": "first_following_XNYS_trading_day",
        "holding_sessions": 1,
        "gross_exposure": 1.0,
    }
    if any(signal.get(key) != value for key, value in expected_signal.items()):
        raise ValueError("Preregistration fixed signal mismatch.")
    if (
        spec.get("coverage_contract", {}).get("source_vintage_guarantee")
        is not SOURCE_VINTAGE_GUARANTEE
    ):
        raise ValueError("Preregistration source-vintage contract mismatch.")
    governance = spec.get("governance", {})
    required_false = (
        "performance_evaluation",
        "holdout_used",
        "parameter_search",
        "asset_search",
        "threshold_search",
        "horizon_search",
        "variant_search",
        "performance_trial_authorized",
        "automatic_promotion",
        "live_execution",
    )
    if governance.get("coverage_only") is not True or any(
        governance.get(key) is not False for key in required_false
    ):
        raise ValueError("Preregistration governance must remain coverage-only.")
    safety = spec.get("safety", {})
    if (
        safety.get("paper_only") is not True
        or safety.get("live_trading_enabled") is not False
        or safety.get("orders_enabled") is not False
        or safety.get("automatic_promotion") is not False
    ):
        raise ValueError("Preregistration safety invariants do not match.")


def _audit_frozen_snapshot(
    datasets: dict[str, tuple[Candle, ...]],
) -> dict:
    if set(datasets) != set(SYMBOLS):
        raise ValueError("Frozen snapshot symbol set does not match preregistration.")
    reference_timestamps = None
    session_mappings = []
    next_calendar_sessions = _xnys_sessions(
        STUDY_START, STUDY_END + timedelta(days=14)
    )
    next_by_session = {
        session: next_calendar_sessions[index + 1]
        for index, session in enumerate(next_calendar_sessions[:-1])
    }

    for symbol in SYMBOLS:
        bars = datasets[symbol]
        if len(bars) != TARGET_COMMON_CANDLES:
            raise ValueError(
                f"{symbol}: frozen candle count {len(bars)} does not match "
                f"{TARGET_COMMON_CANDLES}."
            )
        timestamps = tuple(bar.timestamp for bar in bars)
        if tuple(sorted(set(timestamps))) != timestamps:
            raise ValueError(f"{symbol}: frozen timestamps are not unique and ordered.")
        if reference_timestamps is None:
            reference_timestamps = timestamps
        elif timestamps != reference_timestamps:
            raise ValueError(f"{symbol}: frozen timestamps are not cross-symbol aligned.")
        for bar in bars:
            session_date = bar.timestamp.date()
            if not STUDY_START <= session_date <= STUDY_END:
                raise ValueError(f"{symbol}: frozen bar outside fixed study window.")
            if not all(
                math.isfinite(value)
                for value in (bar.open, bar.high, bar.low, bar.close, bar.volume)
            ) or min(bar.open, bar.high, bar.low, bar.close) <= 0 or bar.volume <= 0:
                raise ValueError(f"{symbol}: invalid close or volume in frozen snapshot.")
            if (
                bar.high < max(bar.open, bar.close)
                or bar.low > min(bar.open, bar.close)
                or bar.low > bar.high
            ):
                raise ValueError(f"{symbol}: inconsistent OHLC values in frozen snapshot.")
            if session_date not in next_by_session:
                raise ValueError(f"{symbol}: no following XNYS session for {session_date}.")

        if symbol == SYMBOLS[0]:
            for timestamp in timestamps:
                session_date = timestamp.date()
                session_mappings.append(
                    {
                        "signal_day": session_date.isoformat(),
                        "first_following_xnys_session": (
                            next_by_session[session_date].isoformat()
                        ),
                    }
                )

    if reference_timestamps is None:
        raise ValueError("Frozen snapshot contains no timestamps.")
    start = reference_timestamps[0].date()
    end = reference_timestamps[-1].date()
    expected_dates = _xnys_sessions(start, end)
    actual_dates = tuple(timestamp.date() for timestamp in reference_timestamps)
    if actual_dates != expected_dates:
        raise ValueError("Frozen snapshot has missing or non-XNYS daily sessions.")

    return {
        "symbol_count": len(datasets),
        "common_bar_count": len(reference_timestamps),
        "first_common_session": start.isoformat(),
        "last_common_session": end.isoformat(),
        "eligible_signal_day_count_after_20_bar_warmup": max(
            0, len(reference_timestamps) - REFERENCE_BARS
        ),
        "reference_warmup_bars": REFERENCE_BARS,
        "mapped_session_count": len(session_mappings),
        "session_mapping_fingerprint": _fingerprint(session_mappings),
        "session_mapping_first": session_mappings[0],
        "session_mapping_last": session_mappings[-1],
    }


def run_coverage(
    *,
    output_root: str | Path = "research/runs/turnover_shock_coverage",
    loader: Loader = load_yahoo_history,
) -> dict:
    prereg_path = ROOT / PREREGISTRATION
    spec = json.loads(prereg_path.read_text(encoding="utf-8"))
    _validate_preregistration(spec)
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
        or settings.ORDERS_ENABLED is not False
        or settings.AUTOMATIC_PROMOTION is not False
    ):
        raise RuntimeError("Turnover-shock coverage requires paper-only safety settings.")

    output_dir = Path(output_root) / TRIAL_ID
    snapshot = build_frozen_snapshot(
        SnapshotSpec(
            universe=UNIVERSE,
            symbols=SYMBOLS,
            interval="1d",
            requested_candles=REQUESTED_CANDLES,
            target_common_candles=TARGET_COMMON_CANDLES,
            minimum_in_window_candles=MINIMUM_IN_WINDOW_CANDLES,
            study_start=STUDY_START,
            study_end=STUDY_END,
            output_dir=output_dir,
        ),
        loader=loader,
    )
    snapshot_passed = (
        "COVERAGE_VALIDATED"
        if snapshot["status"] == "COVERAGE_PASSED"
        else None
    )
    status = snapshot_passed or "DATA_INSUFFICIENT"
    pit_audit = None
    errors = list(snapshot["coverage"]["errors"].values())
    if status == "COVERAGE_VALIDATED":
        try:
            frozen = load_frozen_snapshot(output_dir / "snapshot_manifest.json")
            pit_audit = _audit_frozen_snapshot(frozen)
        except ImportError as exc:
            status = "DATA_INSUFFICIENT"
            errors.append(f"XNYS calendar dependency unavailable: {exc}")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            status = "DATA_INVALID"
            errors.append(str(exc))
        if status == "COVERAGE_VALIDATED" and not SOURCE_VINTAGE_GUARANTEE:
            status = "DATA_INSUFFICIENT"
            errors.append(
                "Historical source-vintage timestamps are unavailable; PIT data "
                "provenance cannot be fully reproduced."
            )

    result = {
        "schema_version": "1.0",
        "task_id": "AGENT-014",
        "trial_id": TRIAL_ID,
        "status": status,
        "preregistration": PREREGISTRATION,
        "preregistration_fingerprint": _fingerprint(spec),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "fixed_study_window": {
            "start": STUDY_START.isoformat(),
            "end": STUDY_END.isoformat(),
        },
        "fixed_universe": list(SYMBOLS),
        "snapshot_fingerprint": snapshot.get("snapshot_fingerprint"),
        "data_snapshot": (
            snapshot.get("data_snapshot")
            if snapshot_passed and pit_audit is not None
            else None
        ),
        "source_vintage_guarantee": SOURCE_VINTAGE_GUARANTEE,
        "pit_audit": pit_audit,
        "errors": errors,
        "governance": {
            "coverage_only": True,
            "signal_calculated": False,
            "performance_evaluation": False,
            "returns_calculated": False,
            "holdout_used": False,
            "selection_used": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["coverage_fingerprint"] = _fingerprint(result)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "turnover_shock_coverage.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "task_id": result["task_id"],
                "status": result["status"],
                "coverage_fingerprint": result["coverage_fingerprint"],
            },
            sort_keys=True,
        )
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root", default="research/runs/turnover_shock_coverage"
    )
    args = parser.parse_args()
    result = run_coverage(output_root=args.output_root)
    return 0 if result["status"] == "COVERAGE_VALIDATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
