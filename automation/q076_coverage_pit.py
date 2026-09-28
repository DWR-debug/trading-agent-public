"""Q076 coverage and PIT for a fresh fixed E1/E2 replication universe."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from automation.q067_alpha_mechanisms import (
    E1_CORRELATION_LOOKBACK,
    Q067_SLEEVES,
    TARGET_CANDLES,
    alpha_sleeve_targets_at,
    apply_turnover_hysteresis,
    build_alpha_sleeves,
    equal_weight_ensemble,
    mean_pairwise_correlation,
    sleeve_period_returns,
    sleeve_return_history_at,
)
from data.canonical_snapshot import load_frozen_snapshot, snapshot_from_preregistration

ROOT = Path(__file__).resolve().parents[1]
SYMBOLS = ("SPG","CCI","EQIX","ESS","ARE","WY","PLD","KIM")
COVERAGE_ID = "T-2026-09-28-076-COVERAGE"
PIT_ID = "T-2026-09-28-076-PIT"
STEP = 113
MIN_HISTORY = E1_CORRELATION_LOOKBACK + 210

SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def used_symbols(ledger_path: Path, universe_module_path: Path) -> set[str]:
    # Q076 symbols are selected from a fixed source-order pool already frozen
    # by the discovery that produced Q068. This guard protects against any
    # unexpected registration overlap introduced after preregistration.
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    used: set[str] = set()
    for trial in payload.get("trials", []):
        scope = trial.get("data_scope", {})
        if not isinstance(scope, dict):
            continue
        for key in ("symbols","trend_symbols","cross_sectional_symbols","requested_symbols","universe_symbols"):
            vals = scope.get(key)
            if isinstance(vals, list):
                used.update(str(v) for v in vals)
    # The fixed Q076 universe is independently checked by the preregistered
    # source-order discovery evidence. No runtime candidate ranking occurs.
    return used


def make_pit(root: Path, assets) -> dict:
    sleeves = build_alpha_sleeves(assets, symbols=SYMBOLS)
    aggregate = equal_weight_ensemble(sleeves, symbols=SYMBOLS)
    returns = sleeve_period_returns(assets, sleeves, symbols=SYMBOLS)
    from automation.q067_alpha_mechanisms import common_mode_multipliers
    multipliers = common_mode_multipliers(returns)
    e2_path = apply_turnover_hysteresis(aggregate, symbols=SYMBOLS)

    def mutate(index: int, mode: str):
        out = {s:list(b) for s,b in assets.items()}
        for symbol,bars in out.items():
            start=index+1
            stop=len(bars) if mode=="future" else index+2
            for i in range(start,stop):
                bars[i]=type(bars[i])(
                    timestamp=bars[i].timestamp,
                    open=bars[i].open*9.0,
                    high=bars[i].high*9.0,
                    low=bars[i].low*0.1,
                    close=bars[i].close*0.1,
                    volume=bars[i].volume,
                )
        return {s:tuple(b) for s,b in out.items()}

    def aggregate_at(local_assets, index):
        sleeves_at=alpha_sleeve_targets_at(local_assets,index,symbols=SYMBOLS)
        return {
            symbol: sum(float(sleeves_at[name].get(symbol,0.0)) for name in Q067_SLEEVES)/len(Q067_SLEEVES)
            for symbol in SYMBOLS
        }

    def history_equal(original, mutated, index):
        o=sleeve_return_history_at(original,index,symbols=SYMBOLS)
        m=sleeve_return_history_at(mutated,index,symbols=SYMBOLS)
        assert o==m
        assert abs(mean_pairwise_correlation(o)-mean_pairwise_correlation(m))<1e-15

    checks=[]
    for index in range(MIN_HISTORY, TARGET_CANDLES-1, STEP):
        original_target=aggregate[index]
        original_prev=aggregate[index-1]
        original_e2=e2_path[index]
        for mode in ("future","next"):
            mutated=mutate(index,mode)
            mutated_target=aggregate_at(mutated,index)
            mutated_prev=aggregate_at(mutated,index-1)
            mutated_e2=apply_turnover_hysteresis(
                (e2_path[index-1],mutated_target),symbols=SYMBOLS
            )[1]
            assert original_target==mutated_target
            assert original_prev==mutated_prev
            assert original_e2==mutated_e2
            history_equal(assets,mutated,index)
            assert multipliers[index] in (1.0,0.5)
            checks.append({"index":index,"mode":mode,"e1_multiplier":multipliers[index]})

    result={
        "schema_version":"1.0",
        "trial_id":PIT_ID,
        "status":"PIT_PASSED",
        "coverage_trial_id":COVERAGE_ID,
        "symbols":list(SYMBOLS),
        "checked_decision_points":len(checks),
        "mechanisms":["E1_ALPHA_COMMON_MODE_THROTTLE","E2_TURNOVER_HYSTERESIS"],
        "future_mutation_checks_passed":True,
        "next_session_mutation_checks_passed":True,
        "performance_evaluation":False,
        "oos_evaluation":False,
        "holdout_evaluation":False,
        "selection_used":False,
        "performance_trial_authorized":False,
        "checks_fingerprint":fp(checks),
        "safety":SAFETY,
    }
    result["result_fingerprint"]=fp(result)
    return result


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--preregistration",required=True)
    parser.add_argument("--output-root",required=True)
    parser.add_argument("--coverage-result",required=True)
    parser.add_argument("--pit-result",required=True)
    args=parser.parse_args()

    prereg=json.loads(Path(args.preregistration).read_text(encoding="utf-8"))
    if prereg.get("status")!="PREREGISTERED_PERFORMANCE":
        raise ValueError("Q076 preregistration must be performance-preregistered")
    if tuple(prereg.get("symbols",())) != SYMBOLS:
        raise ValueError("Q076 symbol order mismatch")

    assets=used_symbols(ROOT/"research/evidence/trial_ledger.json", ROOT/"research/asset_universes.py")
    overlap=set(SYMBOLS) & assets
    if overlap:
        raise RuntimeError(f"Q076 registered-state overlap detected: {sorted(overlap)}")

    scoped=dict(prereg)
    scoped["trial_id"]=COVERAGE_ID
    coverage=snapshot_from_preregistration(scoped,output_root=Path(args.output_root))
    if coverage.get("status")!="COVERAGE_PASSED":
        raise RuntimeError("Q076 coverage did not pass")
    coverage_result={
        "schema_version":"1.0",
        "trial_id":COVERAGE_ID,
        "research_family":"q076_fresh_e1_e2_coverage",
        "status":"COVERAGE_PASSED",
        "symbols":list(SYMBOLS),
        "requested_candles":prereg["requested_candles"],
        "target_common_candles":prereg["target_common_candles"],
        "study_window":prereg["study_window"],
        "common_calendar_count":coverage["coverage"]["common_calendar_count"],
        "snapshot_fingerprint":coverage["snapshot_fingerprint"],
        "coverage_errors":coverage["coverage"]["errors"],
        "selection_used":False,
        "performance_evaluation":False,
        "oos_evaluation":False,
        "holdout_evaluation":False,
        "performance_trial_authorized":False,
        "source_basis":"next fixed source-order coverage batch after Q068",
        "governance":prereg["governance"],
        "safety":SAFETY,
    }
    coverage_result["result_fingerprint"]=fp(coverage_result)
    Path(args.coverage_result).parent.mkdir(parents=True,exist_ok=True)
    Path(args.coverage_result).write_text(json.dumps(coverage_result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    manifest=Path(args.output_root)/COVERAGE_ID/"snapshot_manifest.json"
    frozen=load_frozen_snapshot(manifest)
    pit=make_pit(ROOT,frozen)
    Path(args.pit_result).parent.mkdir(parents=True,exist_ok=True)
    Path(args.pit_result).write_text(json.dumps(pit,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Q076_COVERAGE_STATUS:",coverage_result["status"])
    print("Q076_SNAPSHOT_FINGERPRINT:",coverage_result["snapshot_fingerprint"])
    print("Q076_PIT_STATUS:",pit["status"])
    print("Q076_PIT_FINGERPRINT:",pit["result_fingerprint"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
