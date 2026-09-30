from pathlib import Path
from automation.q100_frontier_feasibility_synthesis import synthesize


def test_q100_classifies_c29_without_ranking() -> None:
    q096 = {
        "status": "SOURCE_AND_PIT_FEASIBILITY_ONLY",
        "inventory_count": 1,
        "candidate_gate_matrix": [{
            "candidate": "frontier:C29",
            "name": "Illusion momentum gap",
            "source": "daily close",
            "existing_state": "MACHINE_FEASIBILITY_IMPLEMENTED",
            "source_state": "CANONICAL_PROJECT_DATA_OR_DETERMINISTIC_INPUT",
            "pit_state": "MACHINE_FEASIBILITY_PRESENT",
            "archive_state": "NO_NEW_EXTERNAL_ARCHIVE_GATE",
        }],
        "live_source_probes": [],
        "governance": {
            "performance_evaluation": False,
            "holdout_evaluation": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "automatic_promotion": False,
            "performance_authorized": False,
        },
    }
    q098 = {
        "status": "HISTORICAL_SOURCE_DEPTH_ONLY",
        "probes": [],
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "candidate_ranking": False,
        "candidate_selection": False,
        "parameter_search": False,
        "performance_authorized": False,
    }
    r = synthesize(q096, q098)
    assert r["summary"]["ready_for_next_gate_count"] == 1
    assert r["candidates"][0]["candidate"] == "frontier:C29"
    assert r["candidates"][0]["performance_authorized"] is False


def test_q100_rejects_authorizing_input() -> None:
    q096 = {
        "status": "SOURCE_AND_PIT_FEASIBILITY_ONLY",
        "inventory_count": 0,
        "candidate_gate_matrix": [],
        "live_source_probes": [],
        "governance": {"performance_evaluation": True},
    }
    q098 = {
        "status": "HISTORICAL_SOURCE_DEPTH_ONLY",
        "probes": [],
        "performance_evaluation": False,
        "candidate_ranking": False,
        "candidate_selection": False,
        "parameter_search": False,
        "performance_authorized": False,
    }
    try:
        synthesize(q096, q098)
    except ValueError as exc:
        assert str(exc) == "Q096_AUTHORIZATION_GUARD_FAILED:performance_evaluation"
    else:
        raise AssertionError("authorizing Q096 input was not rejected")
