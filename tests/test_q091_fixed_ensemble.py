from automation.q069_candidate_bank import CANDIDATES
from portfolio.q091_fixed_ensemble import (
    ENSEMBLE_ID,
    RESIDUAL_ID,
    cross_sectional_residualized_ensemble,
    demean_weights,
    equal_weight_ensemble,
    gross_normalize,
)


SYMBOLS = ("A", "B", "C", "D")


def test_demeaning_is_zero_net_and_translation_invariant():
    x = {"A": 0.5, "B": 0.5, "C": 0.0, "D": 0.0}
    y = demean_weights(x, SYMBOLS)
    assert abs(sum(y.values())) < 1e-12
    shifted = {k: v + 7.0 for k, v in x.items()}
    assert demean_weights(shifted, SYMBOLS) == y


def test_gross_normalization_is_fixed_and_bounded():
    x = {"A": 0.75, "B": -0.25, "C": -0.25, "D": -0.25}
    y = gross_normalize(x, SYMBOLS)
    assert abs(sum(y.values())) < 1e-12
    assert abs(sum(abs(v) for v in y.values()) - 1.0) < 1e-12


def test_equal_weight_ensemble_uses_all_five_sleeves():
    sleeves = {name: {s: 0.25 for s in SYMBOLS} for name in CANDIDATES}
    out = equal_weight_ensemble(sleeves, SYMBOLS)
    assert out == {s: 0.25 for s in SYMBOLS}


def test_residualized_ensemble_is_net_zero_and_unit_gross():
    sleeves = {
        "C7_LOW_MAX_21": {"A": 0.5, "B": 0.5, "C": 0.0, "D": 0.0},
        "C8_LOW_IDIO_VOL_273": {"A": 0.5, "B": 0.0, "C": 0.5, "D": 0.0},
        "C9_LONG_TERM_REVERSAL_756": {"A": 0.0, "B": 0.5, "C": 0.0, "D": 0.5},
        "C10_TREND_EFFICIENCY_63": {"A": 0.0, "B": 0.5, "C": 0.5, "D": 0.0},
        "C11_VOLUME_CONFIRMED_TREND_126": {"A": 0.5, "B": 0.0, "C": 0.0, "D": 0.5},
    }
    out = cross_sectional_residualized_ensemble(sleeves, SYMBOLS)
    assert abs(sum(out.values())) < 1e-12
    assert abs(sum(abs(v) for v in out.values()) - 1.0) < 1e-12


def test_variant_ids_are_distinct():
    assert ENSEMBLE_ID != RESIDUAL_ID
