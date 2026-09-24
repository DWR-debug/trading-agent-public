from automation.exploratory_cs_reversal_followthrough_2026_09_24 import (
    CS_LOOKBACK,
    CS_REBALANCE,
    CS_SKIP,
    CS_TOP_N,
    RESEARCH_COUNT,
    TARGET_COUNT,
)


def test_fixed_followthrough_contract():
    assert TARGET_COUNT == 3500
    assert RESEARCH_COUNT == 2798
    assert (CS_LOOKBACK, CS_SKIP, CS_REBALANCE, CS_TOP_N) == (252, 21, 21, 2)
