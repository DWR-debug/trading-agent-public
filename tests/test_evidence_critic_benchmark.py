from automation.evidence_critic_benchmark import brier, metrics

def test_brier_perfect_distribution():
    assert brier("SUPPORTED", {"SUPPORTED": 1.0, "REFUTED": 0.0, "INSUFFICIENT": 0.0}) == 0.0

def test_metrics_perfect_balanced_sample():
    rows = [
        {"gold_label":"SUPPORTED","predicted_label":"SUPPORTED","probabilities":{"SUPPORTED":1.0,"REFUTED":0.0,"INSUFFICIENT":0.0},"brier":0.0},
        {"gold_label":"REFUTED","predicted_label":"REFUTED","probabilities":{"SUPPORTED":0.0,"REFUTED":1.0,"INSUFFICIENT":0.0},"brier":0.0},
        {"gold_label":"INSUFFICIENT","predicted_label":"INSUFFICIENT","probabilities":{"SUPPORTED":0.0,"REFUTED":0.0,"INSUFFICIENT":1.0},"brier":0.0},
    ]
    out = metrics(rows)
    assert out["accuracy"] == 1.0
    assert out["brier_mean"] == 0.0
    assert out["malformed_or_no_decision"] == 0

def test_request_for_contains_all_substantive_labels():
    from automation.evidence_critic_benchmark import request_for
    case={"id":"X","domain":"PIT","claim":"claim","evidence":"evidence","gold_label":"SUPPORTED"}
    req=request_for(case)
    assert req["questions"]["verdict"]["criteria"] == {
        "SUPPORTED": "The supplied evidence establishes the claim.",
        "REFUTED": "The supplied evidence contradicts the claim.",
        "INSUFFICIENT": "The supplied evidence is not enough to decide the claim.",
    }
