from automation.q045_fixed_alpha_replication_performance import SYMBOLS,_a1_signal,_summary

def test_q045_universe_is_fixed():
    assert SYMBOLS == ("AON","CVS","ADSK","BA","T","F","LUV","NFLX")

def test_q045_summary_split_is_fixed():
    s=_summary([0.001]*3498)
    assert s["research"]["day_count"]==2798
    assert s["holdout"]["day_count"]==700
