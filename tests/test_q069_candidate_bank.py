from datetime import datetime, timedelta, timezone
from pathlib import Path
from automation.q069_candidate_bank import CANDIDATES, candidate_scores_at, candidate_targets_at

SYMBOLS = ("AAA", "BBB", "CCC", "DDD")

def _bar(ts, close, volume=1000.0):
    return type("Bar", (), {"timestamp":ts,"open":float(close),"high":float(close)+1,"low":float(close)-1,"close":float(close),"volume":float(volume)})()

def _assets(count=900):
    base = datetime(2015,1,2,tzinfo=timezone.utc)
    return {s: tuple(_bar(base+timedelta(days=i),100+i*(slot+1),1000+(i%17)*10+slot) for i in range(count)) for slot,s in enumerate(SYMBOLS)}

def test_candidate_bank_is_fixed_and_unranked():
    assert CANDIDATES == ("C7_LOW_MAX_21","C8_LOW_IDIO_VOL_273","C9_LONG_TERM_REVERSAL_756","C10_TREND_EFFICIENCY_63","C11_VOLUME_CONFIRMED_TREND_126")

def test_each_candidate_uses_its_declared_ordering():
    assets = _assets()
    for index, name, reverse in ((100,"C7_LOW_MAX_21",False),(400,"C8_LOW_IDIO_VOL_273",False),(800,"C9_LONG_TERM_REVERSAL_756",False),(300,"C10_TREND_EFFICIENCY_63",True),(300,"C11_VOLUME_CONFIRMED_TREND_126",True)):
        scores = candidate_scores_at(assets,index,symbols=SYMBOLS)[name]
        targets = candidate_targets_at(assets,index,symbols=SYMBOLS)[name]
        expected = sorted(SYMBOLS,key=(lambda s:(-scores[s],s)) if reverse else (lambda s:(scores[s],s)))[:2]
        assert tuple(s for s,w in targets.items() if w) == tuple(expected)

def test_insufficient_history_fails_closed():
    targets = candidate_targets_at(_assets(),20,symbols=SYMBOLS)
    assert all(w == 0.0 for path in targets.values() for w in path.values())

def test_future_mutation_does_not_change_current_targets():
    assets = _assets(); index = 780; original = candidate_targets_at(assets,index,symbols=SYMBOLS)
    mutated = {s:list(bars) for s,bars in assets.items()}
    for bars in mutated.values():
        for i in range(index+1,len(bars)):
            b=bars[i]; bars[i]=type(b)(timestamp=b.timestamp,open=b.open*7,high=b.high*7,low=b.low*.2,close=b.close*.2,volume=b.volume*9)
    mutated={s:tuple(b) for s,b in mutated.items()}
    assert candidate_targets_at(mutated,index,symbols=SYMBOLS) == original

def test_next_session_mutation_does_not_change_current_targets():
    assets = _assets(); index = 780; original = candidate_targets_at(assets,index,symbols=SYMBOLS)
    mutated = {s:list(bars) for s,bars in assets.items()}
    for bars in mutated.values():
        b=bars[index+1]; bars[index+1]=type(b)(timestamp=b.timestamp,open=b.open*9,high=b.high*9,low=b.low*.1,close=b.close*.1,volume=b.volume*10)
    mutated={s:tuple(b) for s,b in mutated.items()}
    assert candidate_targets_at(mutated,index,symbols=SYMBOLS) == original

def test_candidate_targets_are_long_only_and_bounded():
    for path in candidate_targets_at(_assets(),800,symbols=SYMBOLS).values():
        assert all(w >= 0 for w in path.values())
        assert sum(path.values()) <= 1.0 + 1e-12

def test_design_contract_disables_performance_and_selection():
    text = Path("research/preregistrations/q069_orthogonal_ohlcv_candidate_bank_2026_09_28.json").read_text(encoding="utf-8")
    for needle in ("performance_evaluation", "selection_used", "family_ranking", "holdout_used_for_selection", "automatic_promotion"):
        assert needle in text