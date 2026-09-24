from automation.exploratory_cs_reversal_precursors_2026_09_24 import (
    CS_LOOKBACK,
    CS_REBALANCE,
    CS_SKIP,
    CS_TOP_N,
    PRE_EVENT_LOOKBACK,
    RESEARCH_COUNT,
    TARGET_COUNT,
)


def test_fixed_precursor_contract():
    assert (TARGET_COUNT, RESEARCH_COUNT) == (3500, 2798)
    assert (CS_LOOKBACK, CS_SKIP, CS_REBALANCE, CS_TOP_N) == (252, 21, 21, 2)
    assert PRE_EVENT_LOOKBACK == 21
