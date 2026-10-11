from automation.candidate_intake_capacity_plan import build_plan_from_payload


def candidate(candidate_id="Q999"):
    return {
        "id": candidate_id,
        "name": "Synthetic public-information state",
        "hypothesis": "A newly public operational state may alter issuer information processing.",
        "construction": "Frozen deterministic PIT boundary with fixed issuer identity mapping.",
        "sources": ["https://www.sec.gov/"],
        "next_gate": "free_source_availability_and_historical_clock",
        "cheap_falsifiers": [
            "Shift public clock by one session and check the predeclared invariant.",
            "Shuffle issuer mapping within the fixed universe.",
        ],
        "gates": [
            "Historical public-observation boundary",
            "Frozen issuer mapping and revision lineage",
        ],
    }


def test_empty_queue_does_not_consume_capacity_or_widen_focus():
    plan = build_plan_from_payload(
        {"schema_version": 1, "candidates": []},
        active_focus=["Q104:I19", "Q220", "Q221"],
    )
    assert plan["status"] == "EMPTY_QUEUE"
    assert plan["summary"] == {
        "total_candidates": 0,
        "validated_quarantined": 0,
        "blocked": 0,
        "dispatchable_now": 0,
        "capacity_consumed": 0,
    }
    assert plan["active_focus_lock"] == ["Q104:I19", "Q220", "Q221"]
    assert plan["policy"]["active_focus_auto_widening"] is False


def test_valid_candidate_is_quarantined_not_dispatched():
    plan = build_plan_from_payload(
        {"schema_version": 1, "candidates": [candidate()]},
        known_ids={"Q194", "Q220"},
    )
    row = plan["candidates"][0]
    assert row["status"] == "VALIDATED_QUARANTINED_WAITING_FOR_FOCUS_RELEASE"
    assert row["candidate_fingerprint"]
    assert row["dispatchable"] is False
    assert row["capacity_assignment"] is None
    assert row["performance_authorized"] is False
    assert plan["summary"]["validated_quarantined"] == 1
    assert plan["summary"]["dispatchable_now"] == 0
    assert plan["scientific_authority"] is False


def test_project_id_alias_collision_is_blocked():
    plan = build_plan_from_payload(
        {"schema_version": 1, "candidates": [candidate("104")]},
        known_ids={"Q104:I19"},
    )
    assert plan["candidates"][0]["status"] == "BLOCKED_ID_ALREADY_IN_PROJECT"
    assert plan["candidates"][0]["dispatchable"] is False


def test_duplicate_ids_in_queue_block_every_alias_collision():
    plan = build_plan_from_payload(
        {"schema_version": 1, "candidates": [candidate("Q999"), candidate("999")]},
        known_ids=set(),
    )
    assert {row["status"] for row in plan["candidates"]} == {"BLOCKED_DUPLICATE_QUEUE_ID"}
    assert plan["summary"]["validated_quarantined"] == 0


def test_candidate_without_falsifiers_is_blocked():
    incoming = candidate()
    incoming["cheap_falsifiers"] = []
    plan = build_plan_from_payload(
        {"schema_version": 1, "candidates": [incoming]},
        known_ids=set(),
    )
    assert plan["candidates"][0]["status"] == "BLOCKED_MISSING_FALSIFIERS_OR_GATES"


def test_performance_fields_fail_closed_under_existing_hypothesis_compiler():
    incoming = candidate()
    incoming["holdout_return"] = 0.15
    plan = build_plan_from_payload(
        {"schema_version": 1, "candidates": [incoming]},
        known_ids=set(),
    )
    assert plan["candidates"][0]["status"] == "BLOCKED_ROBUSTNESS_OR_SCHEMA"
    assert "DISCOVERY_FORBIDDEN_FIELDS" in plan["candidates"][0]["reason"]
    assert plan["policy"]["performance_authorization"] is False
