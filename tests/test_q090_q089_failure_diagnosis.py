import automation.q090_q089_failure_diagnosis as q090


def test_regime_is_prior_only():
    values = [0.01] * 400
    values[-1] = -0.8
    a = q090.classify_regime(values)
    values[-1] = 0.8
    b = q090.classify_regime(values)
    assert a[:-1] == b[:-1]


def test_drawdown_interval_peak_to_trough():
    dd = q090.max_drawdown_interval([0.10, -0.20, -0.10, 0.20])
    assert dd["start_index"] == 1
    assert dd["end_index"] == 2
    assert dd["max_drawdown_percent"] > 20.0


def test_jaccard_is_symmetric_and_bounded():
    a = {"AEE", "AES"}
    b = {"AES", "ATO"}
    assert q090.jaccard(a, b) == q090.jaccard(b, a)
    assert 0.0 <= q090.jaccard(a, b) <= 1.0


def test_frozen_source_contract_constants():
    assert q090.Q089_RUNNER_SHA == "0546bebae018acb0b530f094462b3c9cd79d96aba7ed66c8b17dc720ab13057b"
    assert q090.Q069_BANK_SHA == "84e008a6152cbea128e5e5f2ac0dfdde0b0172310fe4c510241c60edfd3ff617"
    assert q090.Q089_SNAPSHOT_FP == "bb82aeaed86411a8675be7f8ecb1c99e9c144f017466a836b8cafeb9d3b55e1d"


def test_prereg_is_diagnostic_only():
    from pathlib import Path
    p = Path("research/preregistrations/q090_q089_failure_mechanism_diagnosis_2026_09_29.json")
    data = p.read_text(encoding="utf-8")
    assert '"new_performance_evaluation": false' in data
    assert '"selection": false' in data
    assert '"parameter_search": false' in data
    assert '"holdout_used_for_selection": false' in data
