from research.champion_challenger import EvidenceSnapshot, evaluate_challenger, pearson_correlation

def snapshot(name, dd=5.0, pf=1.2, holdout=0.1, stress=0.01):
    return EvidenceSnapshot(name, dd, pf, holdout, pf, stress, (0.01, -0.005, 0.02))

def test_challenger_contract():
    assert evaluate_challenger(snapshot("champion"), snapshot("challenger")).status == "EVIDENCE_ELIGIBLE"

def test_challenger_fails_stress():
    assert evaluate_challenger(snapshot("champion"), snapshot("challenger", stress=-0.01)).status == "NOT_ELIGIBLE"

def test_correlation():
    assert pearson_correlation((1, 2, 3), (1, 2, 3)) == 1.0
