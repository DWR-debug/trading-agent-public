from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from portfolio.q030_risk_mechanisms import (
    Bar,
    common_mode_exposure_scale,
    drawdown_throttle_scale,
    position_lifecycle_exit_trigger,
    sleeve_volatility_scale,
)


SYMBOLS = ("BSV","FAN","JNK","UDN","VCLT","VGIT","SCHR")


def _fp(value: object) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def _load(root: Path) -> dict[str,list[Bar]]:
    assets={}
    for symbol in SYMBOLS:
        path=root/symbol/"1d.csv"
        rows=[]
        with path.open(newline="",encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows.append(Bar(
                    timestamp=row["timestamp"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                ))
        if len(rows)!=3500:
            raise ValueError(f"{symbol}: expected 3500 rows, got {len(rows)}")
        if any(rows[i].timestamp>=rows[i+1].timestamp for i in range(len(rows)-1)):
            raise ValueError(f"{symbol}: timestamps not strictly increasing")
        assets[symbol]=rows
    return assets


def _returns(bars: list[Bar]) -> list[float]:
    return [bars[i].close/bars[i-1].close-1.0 for i in range(1,len(bars))]


def run(root: Path, output: Path) -> dict:
    assets=_load(root)
    returns={symbol:_returns(bars) for symbol,bars in assets.items()}
    portfolio_returns=[
        sum(returns[s][i] for s in SYMBOLS)/len(SYMBOLS)
        for i in range(len(returns[SYMBOLS[0]]))
    ]
    fixed_weights={s:1.0/len(SYMBOLS) for s in SYMBOLS}

    checks=[]
    for index in range(80, len(assets["BSV"])-1, 97):
        # Session index 'index' is the decision point. Inputs end at index-1.
        sleeve_history=portfolio_returns[:index]
        a=sleeve_volatility_scale(sleeve_history)

        b=drawdown_throttle_scale(sleeve_history)

        active_history={s: returns[s][:index] for s in SYMBOLS}
        c=common_mode_exposure_scale(active_history,fixed_weights)

        entry=max(20,index-40)
        highest=max(bar.close for bar in assets["BSV"][entry:index])
        bars=assets["BSV"]
        d=position_lifecycle_exit_trigger(bars,index,highest_close_since_entry=highest)

        # Mutate only observations after the decision point.
        mutated={s:[Bar(**vars(x)) for x in bars] for s,bars in assets.items()}
        for series in mutated.values():
            for future in range(index+1,len(series)):
                series[future].close*=1.7
                series[future].open*=0.2
                series[future].high*=1.3
                series[future].low*=0.4

        returns_mut={s:_returns(mutated[s]) for s in SYMBOLS}
        portfolio_mut=[
            sum(returns_mut[s][i] for s in SYMBOLS)/len(SYMBOLS)
            for i in range(len(returns_mut[SYMBOLS[0]]))
        ]
        a2=sleeve_volatility_scale(portfolio_mut[:index])
        b2=drawdown_throttle_scale(portfolio_mut[:index])
        c2=common_mode_exposure_scale({s:returns_mut[s][:index] for s in SYMBOLS},fixed_weights)

        highest_mut=max(bar.close for bar in mutated["BSV"][entry:index])
        d2=position_lifecycle_exit_trigger(mutated["BSV"],index,highest_close_since_entry=highest_mut)
        if (a,b,c,d)!=(a2,b2,c2,d2):
            raise AssertionError(f"future mutation changed mechanism decision at {index}")

        # Explicit next-session OHLC mutation must not affect the decision at index.
        next_mut={s:[Bar(**vars(x)) for x in bars] for s,bars in assets.items()}
        if index+1 < len(next_mut["BSV"]):
            for series in next_mut.values():
                series[index+1]=Bar(
                    timestamp=series[index+1].timestamp,
                    open=series[index+1].open*9.0,
                    high=series[index+1].high*9.0,
                    low=series[index+1].low*0.1,
                    close=series[index+1].close*0.1,
                )
        d3=position_lifecycle_exit_trigger(
            next_mut["BSV"],index,highest_close_since_entry=highest
        )
        if d3!=d:
            raise AssertionError(f"next-session OHLC mutation changed RISK-D at {index}")

        checks.append({"index":index,"RISK-A":a,"RISK-B":b,"RISK-C":c,"RISK-D":d})

    result={
        "schema_version":"1.0",
        "trial_id":"T-2026-09-27-055",
        "status":"PIT_PASSED",
        "universe":"validation_2026_09_27_q030_risk_stability_coverage",
        "checked_decision_points":len(checks),
        "mechanisms":["RISK-A","RISK-B","RISK-C","RISK-D"],
        "future_mutation_checks_passed":True,
        "next_session_mutation_checks_passed":True,
        "performance_evaluation":False,
        "oos_evaluation":False,
        "holdout_evaluation":False,
        "selection_used":False,
        "holdout_used_for_selection":False,
        "governance":{"performance_trial_authorized":False,"automatic_promotion":False},
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
        "checks_fingerprint":_fp(checks),
    }
    result["report_fingerprint"]=_fp(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Q034_MECHANISM_PIT_STATUS:",result["status"])
    print("CHECKED_DECISION_POINTS:",result["checked_decision_points"])
    print("REPORT_FINGERPRINT:",result["report_fingerprint"])
    return result


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--universe-root",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    run(Path(args.universe_root),Path(args.output))
