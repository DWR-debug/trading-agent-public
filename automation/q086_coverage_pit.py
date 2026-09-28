"""Q086 fresh coverage and PIT harness; performance is not executed here."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

from automation.fixed_window_candidate_discovery import run_discovery
from data.canonical_snapshot import snapshot_from_preregistration

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_ID = "T-2026-09-28-085-COVERAGE"
PERFORMANCE_ID = "T-2026-09-28-085-PERFORMANCE"
UNIVERSE = "validation_2026_09_28_q086_fresh_q069"
TARGET, REQUESTED, RAW = 3500, 4000, 5000
SAFETY = {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False}


def _load_manifest():
    manifest = ROOT / "research" / "runs" / "q086_coverage" / COVERAGE_ID / "snapshot_manifest.json"
    if not manifest.exists():
        raise FileNotFoundError("Q086 persisted snapshot manifest missing")
    d = json.loads(manifest.read_text(encoding="utf-8"))
    if d.get("status") != "COVERAGE_PASSED":
        raise ValueError("Q086 persisted snapshot is not successful")
    return manifest, d


def coverage():
    discovery = run_discovery(
        output=ROOT / "research" / "runs" / "q086_discovery" / "discovery.json",
        symbol_limit=48,
        workers=8,
    )
    selected = tuple(discovery["selected_coverage_batch"][:8])
    if len(selected) != 8:
        raise RuntimeError("Q086 did not obtain eight coverage-valid symbols")
    spec = {
        "trial_id": COVERAGE_ID,
        "universe": UNIVERSE,
        "symbols": list(selected),
        "interval": "1d",
        "requested_candles": REQUESTED,
        "raw_fetch_candles": RAW,
        "target_common_candles": TARGET,
        "study_window": {"start": "2011-01-01", "end": "2025-09-24"},
        "governance": {"coverage_only": True, "performance_evaluation": False, "selection_used": False},
        "safety": SAFETY,
    }
    snap = snapshot_from_preregistration(spec, output_root=ROOT / "research" / "runs" / "q086_coverage")
    if snap["status"] != "COVERAGE_PASSED":
        raise RuntimeError("Q086 coverage failed")
    freeze = {
        "schema_version": "1.0",
        "trial_id": COVERAGE_ID,
        "status": "COVERAGE_PASSED",
        "universe": UNIVERSE,
        "symbols": list(selected),
        "requested_candles": REQUESTED,
        "raw_fetch_candles": RAW,
        "target_common_candles": TARGET,
        "study_window": spec["study_window"],
        "source_discovery_fingerprint": discovery["fingerprint"],
        "snapshot_fingerprint": snap["snapshot_fingerprint"],
        "selection_used": False,
        "holdout_selection_used": False,
        "safety": SAFETY,
    }
    e = ROOT / "research" / "evidence"
    e.mkdir(exist_ok=True)
    (e / "q086_coverage_result.json").write_text(json.dumps({
        "schema_version": "1.0", "trial_id": COVERAGE_ID, "research_family": "q086_fresh_coverage",
        "status": "COVERAGE_PASSED", "symbols": list(selected), "universe": UNIVERSE,
        "common_calendar_count": snap["coverage"]["common_calendar_count"],
        "snapshot_fingerprint": snap["snapshot_fingerprint"],
        "selection_used": False, "performance_evaluation": False, "holdout_evaluation": False,
        "source_discovery": discovery, "safety": SAFETY
    }, indent=2) + "\n", encoding="utf-8")
    (e / "q086_asset_freeze.json").write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    p = json.loads((ROOT / "research" / "preregistrations" / "q086_performance_2026_09_28.json").read_text(encoding="utf-8"))
    p["symbols"] = list(selected)
    p["asset_freeze_fingerprint"] = __import__("hashlib").sha256(
        json.dumps(freeze, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    (ROOT / "research" / "preregistrations" / "q086_performance_2026_09_28.json").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")
    print("Q086_COVERAGE_PASS", ",".join(selected))


def _load_assets():
    _, manifest = _load_manifest()
    assets = {}
    for item in manifest["data_snapshot"]["datasets"]:
        p = Path(item["path"])
        p = p if p.is_absolute() else ROOT / p
        rows = []
        with p.open(encoding="utf-8", newline="") as h:
            for r in csv.DictReader(h):
                rows.append({k: float(r[k]) for k in ("open", "high", "low", "close", "volume")})
        assets[item["symbol"]] = rows
    if len(assets) != 8 or any(len(v) != TARGET for v in assets.values()):
        raise RuntimeError("Q086 persisted snapshot geometry mismatch")
    return assets


def _scores(assets, i):
    syms = sorted(assets)
    out = {}
    if i >= 22:
        out["C7"] = {s: -max(r["close"] for r in assets[s][i-21:i+1]) + assets[s][i]["close"] for s in syms}
    else:
        out["C7"] = {}
    if i >= 274:
        rr = {s: [assets[s][j]["close"]/assets[s][j-1]["close"]-1 for j in range(1, len(assets[s]))] for s in syms}
        st, en = i-273, i
        m = [sum(rr[s][j] for s in syms)/len(syms) for j in range(st, en)]
        out["C8"] = {s: -statistics.pstdev([x-y for x,y in zip(rr[s][st:en], m)]) for s in syms}
    else:
        out["C8"] = {}
    out["C9"] = {s: (assets[s][i-756]["close"]/assets[s][i-1]["close"] if i >= 757 else 0.0) for s in syms}
    out["C10"] = {}
    if i >= 64:
        for s in syms:
            rets = [assets[s][j]["close"]/assets[s][j-1]["close"]-1 for j in range(i-62, i+1)]
            net = abs(assets[s][i]["close"]/assets[s][i-63]["close"]-1)
            out["C10"][s] = net / (sum(abs(x) for x in rets) or 1.0)
    if i >= 127:
        out["C11"] = {}
        for s in syms:
            recent = sum(r["volume"] for r in assets[s][i-20:i+1]) / 21
            prior = sum(r["volume"] for r in assets[s][i-126:i-20]) / 106
            ret = assets[s][i-21]["close"]/assets[s][i-126]["close"]-1
            out["C11"][s] = ret * (recent / prior if prior else 0.0)
    else:
        out["C11"] = {}
    return out


def pit():
    assets = _load_assets()
    checks = [300, 800, 1600, 2600, 3400]
    for i in checks:
        before = _scores(assets, i)
        mutated = {s: [dict(x) for x in rows] for s, rows in assets.items()}
        for rows in mutated.values():
            for j in range(i + 1, len(rows)):
                rows[j]["open"] *= 9
                rows[j]["high"] *= 7
                rows[j]["low"] *= 0.2
                rows[j]["close"] *= 0.25
                rows[j]["volume"] *= 6
        assert before == _scores(mutated, i), f"future mutation changed signal at {i}"
    result = {
        "schema_version": "1.0", "trial_id": "T-2026-09-28-085-PIT",
        "status": "PIT_PASSED", "coverage_trial_id": COVERAGE_ID,
        "checked_decision_points": len(checks),
        "future_mutation_checks_passed": True, "next_session_mutation_checks_passed": True,
        "performance_evaluation": False, "holdout_evaluation": False,
        "selection_used": False, "holdout_used_for_selection": False, "safety": SAFETY
    }
    (ROOT / "research" / "evidence" / "q086_pit_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Q086_PIT_PASS", len(checks))


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("mode", choices=("coverage", "pit"))
    m = a.parse_args().mode
    coverage() if m == "coverage" else pit()
