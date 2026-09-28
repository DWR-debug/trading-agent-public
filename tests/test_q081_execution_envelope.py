from automation.q067_alpha_mechanisms import GROSS_EXPOSURE_CAP
from automation.q081_corrected_e1_e2_performance import (
    SYMBOLS,
    apply_execution_gross_cap,
)


def test_gross_cap_correction_is_identity_under_cap():
    row = {symbol: 0.0 for symbol in SYMBOLS}
    row[SYMBOLS[0]] = 0.5
    row[SYMBOLS[1]] = 0.5
    assert apply_execution_gross_cap(row) == row


def test_gross_cap_correction_pro_rata_fits_existing_envelope():
    row = {symbol: 0.0 for symbol in SYMBOLS}
    row[SYMBOLS[0]] = 0.5
    row[SYMBOLS[1]] = 0.34
    row[SYMBOLS[2]] = 0.20
    corrected = apply_execution_gross_cap(row)

    raw_gross = sum(abs(row[s]) for s in SYMBOLS)
    corrected_gross = sum(abs(corrected[s]) for s in SYMBOLS)
    assert raw_gross == 1.04
    assert corrected_gross <= GROSS_EXPOSURE_CAP + 1e-12

    scale = GROSS_EXPOSURE_CAP / raw_gross
    for symbol in SYMBOLS:
        assert abs(corrected[symbol] - row[symbol] * scale) < 1e-12


def test_gross_cap_correction_preserves_long_only_and_zero_structure():
    row = {symbol: 0.0 for symbol in SYMBOLS}
    row[SYMBOLS[0]] = 0.55
    row[SYMBOLS[1]] = 0.45
    row[SYMBOLS[2]] = 0.15
    corrected = apply_execution_gross_cap(row)

    assert all(corrected[symbol] >= 0.0 for symbol in SYMBOLS)
    assert corrected[SYMBOLS[3]] == 0.0
