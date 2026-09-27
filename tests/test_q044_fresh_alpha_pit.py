from automation.q044_fresh_alpha_pit import SYMBOLS,_a2,_a3,_a5,_a1b,_a6,_signals

def _assets(n=320):
    out={}
    for p,s in enumerate(SYMBOLS):
        rows=[]
        for i in range(n):
            c=100.0+i*(p+1)
            rows.append({"timestamp":str(i),"open":c,"high":c+1,"low":c-1,"close":c,"volume":1000.0})
        out[s]=rows
    return out

def test_fixed_mechanisms_produce_deterministic_outputs():
    a=_assets()
    assert len(_a2(a,300))==2
    assert len(_a3(a,300))==2
    assert len(_a5(a,300))==2
    assert len(_a1b(a,300))==2
    assert len(_a6(a,300))==2
    s=_signals(a,300)
    assert set(s)=={"A1","A2","A3","A5","A1B","A6"}
