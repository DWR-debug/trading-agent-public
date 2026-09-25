"""Q014: one-year extension of the fixed GDELT mechanism/redundancy diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from automation.information_alpha_redundancy import run_redundancy_diagnostic

DEFAULT_START = date(2025, 9, 25)
DEFAULT_END = date(2026, 9, 24)
MIN_TOTAL_OBSERVATIONS = 80
MIN_EVENT_WINDOWS = 40


def run_q014(
    start: date = DEFAULT_START,
    end: date = DEFAULT_END,
    *,
    output_dir: str | Path = "research/runs/information_alpha_redundancy/q014",
) -> dict:
    if (end - start).days != 364:
        raise ValueError("Q014 requires an exact 365-calendar-day inclusive window.")
    root = Path(output_dir)
    base = run_redundancy_diagnostic(
        start,
        end,
        output_dir=root / "base_q013_diagnostic",
    )
    total = base["observations"]["total"]
    events = base["observations"]["event_windows"]

    result = dict(base)
    result["task_id"] = "Q-014-INFORMATION-ALPHA-MECHANISM-REDUNDANCY-LONG-WINDOW"
    result["status"] = (
        "COMPLETED_DISCOVERY_ONLY"
        if total >= MIN_TOTAL_OBSERVATIONS and events >= MIN_EVENT_WINDOWS
        else "DATA_INSUFFICIENT"
    )
    result["source_task"] = "Q-013-INFORMATION-ALPHA-MECHANISM-REDUNDANCY-DIAGNOSTIC"
    result["window_contract"] = {
        "calendar_days": 365,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "min_total_observations": MIN_TOTAL_OBSERVATIONS,
        "min_event_windows": MIN_EVENT_WINDOWS,
    }
    result["performance_trial_authorized"] = False
    result["selection_used"] = False
    result["holdout_used"] = False
    result["parameter_search_used"] = False
    result["feature_selection_used"] = False
    result["asset_selection_used"] = False
    result["horizon_selection_used"] = False

    canonical = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    result["fingerprint"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    root.mkdir(parents=True, exist_ok=True)
    (root / "q014_redundancy_long_window.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=DEFAULT_START.isoformat())
    parser.add_argument("--end", default=DEFAULT_END.isoformat())
    args = parser.parse_args()
    report = run_q014(
        date.fromisoformat(args.start),
        date.fromisoformat(args.end),
    )
    print("Q014_STATUS:", report["status"])
    print("Q014_FINGERPRINT:", report["fingerprint"])
    print("Q014_OBSERVATIONS:", report["observations"]["total"])
    print("Q014_EVENT_WINDOWS:", report["observations"]["event_windows"])
    return 0 if report["status"] != "DATA_INSUFFICIENT" else 3


if __name__ == "__main__":
    raise SystemExit(main())
