"""Predeclared persistence diagnostics for the fixed 63-session risk layer.

Event definitions are fixed:
- activation: scale crosses from >=1.0 to <1.0
- recovery: scale crosses from <1.0 to >=1.0
- forward returns are next-day onward cumulative net portfolio returns
  over exactly 5, 20, and 60 available days.
No threshold or parameter is estimated from these outcomes.

No tuning, selection, new data, gate changes, or production mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from automation import candidate_validation_50_50_vol_budget as base
from config import settings

CASES = (
    {
        "name": "second_validation",
        "artifact_id": 10740188093,
        "run_id": 35839443616,
        "root": "research/independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_trend",
        "cs_universe": "validation_2026_09_23_cs",
    },
    {
        "name": "third_validation",
        "artifact_id": 10745697729,
        "run_id": 35851876264,
        "root": "research/third_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_third_trend",
        "cs_universe": "validation_2026_09_23_third_cs",
    },
)

HORIZONS = (5, 20, 60)

def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)

def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode()).hexdigest()

def _load_rows(artifact_root: Path, case: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    root = artifact_root / case["root"]
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    stored = report["report_fingerprint"]
    payload = dict(report)
    payload.pop("report_fingerprint", None)
    if _fp(payload) != stored or report["status"] != "COMPLETED":
        raise ValueError(f'{case["name"]}: invalid report fingerprint/status')
    archive = json.loads((root / "adjusted_close_archive.json").read_text(encoding="utf-8"))
    archive_fp = archive["archive_fingerprint"]
    archive_payload = dict(archive)
    archive_payload.pop("archive_fingerprint", None)
    if _fp(archive_payload) != archive_fp:
        raise ValueError(f'{case["name"]}: invalid archive fingerprint')
    if archive_fp != report["source"]["adjusted_close_archive_fingerprint"]:
        raise ValueError(f'{case["name"]}: archive/report mismatch')
    trend_manifest = base._manifest(root / "data_trend_manifest.json", case["trend_universe"])
    cs_manifest = base._manifest(root / "data_cs_manifest.json", case["cs_universe"])
    data_dir = artifact_root / "data/market_data"
    trend = base._assets(data_dir, trend_manifest)
    cs = base._assets(data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError(f'{case["name"]}: overlapping universes')
    adjusted = {
        symbol: {datetime.fromisoformat(ts): value for ts, value in values}
        for symbol, values in archive["datasets"].items()
    }
    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)
    return base._align(
        trend, trend_weights, {s: adjusted[s] for s in trend},
        cs, cs_weights, {s: adjusted[s] for s in cs},
    )

def _cum_return(rows: list[dict[str, Any]], start: int, horizon: int) -> float | None:
    end = start + horizon
    if end > len(rows):
        return None
    equity = 1.0
    for row in rows[start:end]:
        equity *= 1.0 + row["net_return"]
    return equity - 1.0

def _event_stats(simulated: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    segment = simulated[start:end]
    if not segment:
        return {"event_count": 0}
    activations: list[dict[str, Any]] = []
    recoveries: list[dict[str, Any]] = []
    for i, row in enumerate(segment):
        previous_scale = 1.0 if i == 0 else segment[i - 1]["scale"]
        if previous_scale >= 1.0 and row["scale"] < 1.0:
            activations.append({"index": i, "row": row})
        elif previous_scale < 1.0 and row["scale"] >= 1.0:
            recoveries.append({"index": i, "row": row})

    def summarize(events: list[dict[str, Any]], label: str) -> dict[str, Any]:
        complete = [
            event for event in events
            if all(_cum_return(segment, event["index"] + 1, h) is not None for h in HORIZONS)
        ]
        out: dict[str, Any] = {
            "event_count": len(events),
            "events_with_complete_5_20_60_forward_windows": len(complete),
            "discarded_for_incomplete_forward_window": len(events) - len(complete),
        }
        if not complete:
            out["forward_mean_return"] = {str(h): None for h in HORIZONS}
            out["forward_median_return"] = {str(h): None for h in HORIZONS}
            out["mean_pre_event_realized_vol"] = None
            out["median_pre_event_realized_vol"] = None
            out["mean_event_scale"] = None
            return out

        forward = {
            h: [_cum_return(segment, e["index"] + 1, h) for e in complete]
            for h in HORIZONS
        }
        out["forward_mean_return"] = {str(h): sum(forward[h]) / len(forward[h]) for h in HORIZONS}
        out["forward_median_return"] = {
            str(h): sorted(forward[h])[len(forward[h]) // 2] for h in HORIZONS
        }
        vols = [e["row"]["realized_vol_estimate"] for e in complete if e["row"]["realized_vol_estimate"] is not None]
        scales = [e["row"]["scale"] for e in complete]
        out["mean_pre_event_realized_vol"] = sum(vols) / len(vols) if vols else None
        out["median_pre_event_realized_vol"] = sorted(vols)[len(vols) // 2] if vols else None
        out["mean_event_scale"] = sum(scales) / len(scales)
        return out

    return {
        "activation": summarize(activations, "activation"),
        "recovery": summarize(recoveries, "recovery"),
    }

def analyze(artifact_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only safety contract violated.")
    cases = {}
    for case in CASES:
        rows = _load_rows(artifact_root, case)
        simulated = base._simulate(rows, 1.0, True, False)
        cases[case["name"]] = {
            "source": {"validation_run_id": case["run_id"], "artifact_id": case["artifact_id"]},
            "research": _event_stats(simulated, 0, base.RESEARCH_COUNT),
            "holdout": _event_stats(simulated, base.RESEARCH_COUNT, len(simulated)),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_persistence_control_2026_09_23",
        "status": "COMPLETED",
        "question": "How persistent are fixed 63-session de-risking phases, and what are the fixed-horizon portfolio outcomes after activation and recovery events?",
        "methodology": {
            "vol_window_sessions": 63,
            "target_annualized_volatility": base.TARGET_VOL,
            "event_definition_activation": "scale crosses from >=1.0 to <1.0",
            "event_definition_recovery": "scale crosses from <1.0 to >=1.0",
            "forward_return_definition": "next-day onward cumulative net portfolio return",
            "fixed_forward_horizons_days": list(HORIZONS),
            "same_data_and_split": True,
            "no_parameter_search": True,
            "no_selection": True,
            "no_gate_changes": True,
            "no_new_data_downloads": True,
            "descriptive_not_causal": True,
        },
        "cases": cases,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
    }
    result["diagnostic_fingerprint"] = _fp(result)
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze(Path(args.artifact_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print("RISK_LAYER_PERSISTENCE_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    for name, case in result["cases"].items():
        for segment in ("research", "holdout"):
            data = case[segment]
            for event in ("activation", "recovery"):
                e = data[event]
                print(f"{name.upper()}_{segment.upper()}_{event.upper()}_COUNT:", e["event_count"])
                print(f"{name.upper()}_{segment.upper()}_{event.upper()}_MEAN_PRE_EVENT_VOL:", e["mean_pre_event_realized_vol"])
                for h in HORIZONS:
                    print(f"{name.upper()}_{segment.upper()}_{event.upper()}_MEAN_FWD_{h}D_PP:", (e["forward_mean_return"][str(h)] * 100.0) if e["forward_mean_return"][str(h)] is not None else None)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
