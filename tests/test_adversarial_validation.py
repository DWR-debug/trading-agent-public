from research.adversarial_validation import clip_returns, delayed, leave_one_out_total, multiply_costs, sign_permutation_probability, summarize_path

def test_delay_preserves_length():
    assert delayed((0.1, 0.2, 0.3), 1) == (0.0, 0.1, 0.2)

def test_cost_stress_and_clipping():
    assert multiply_costs((0.02, -0.01), extra_cost_per_period=0.005) == (0.015, -0.015)
    assert clip_returns((0.2, -0.2), absolute_limit=0.05) == (0.05, -0.05)

def test_leave_one_out_and_permutation_are_finite():
    values = leave_one_out_total((0.01, -0.005, 0.02))
    assert len(values) == 3
    assert 0.0 <= sign_permutation_probability((0.01, -0.005, 0.02), trials=100) <= 1.0

def test_summary_path():
    result = summarize_path((0.1, -0.05))
    assert result.observation_count == 2
    assert abs(result.total_return - 0.045) < 1e-12
