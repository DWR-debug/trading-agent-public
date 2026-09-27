from datetime import datetime, timedelta, timezone

from automation.q042_additional_price_alpha_pit import _a1b_scores,_a6_scores,_signals,SYMBOLS

def _assets(n=320):
    base=datetime(2020,1,1,tzinfo=timezone.utc)
    out={}
    for pos,s in enumerate(SYMBOLS):
        rows=[]
        for i in range(n):
            c=100.0+i*(pos+1)
            rows.append({"timestamp":(base+timedelta(days=i)).isoformat(),"open":c,"high":c+1,"low":c-1,"close":c,"volume":1000.0})
        out[s]=rows
    return out

def test_52_week_high_and_overnight_scores_are_deterministic():
    assets=_assets()
    assert len(_a1b_scores(assets,300))==8
    assert len(_a6_scores(assets,300))==8
    signals=_signals(assets,300)
    assert len(signals["A1B_52W_HIGH_TOP2"])==2
    assert len(signals["A6_OVERNIGHT_TUGWAR_TOP2"])==2

def test_overlapping_future_data_is_not_required():
    assets=_assets()
    original=_signals(assets,300)
    for s in SYMBOLS:
        for i in range(301,320):
            assets[s][i]["close"]*=7
    assert original==_signals(assets,300)
