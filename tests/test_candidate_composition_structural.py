from automation.candidate_composition_structural import (
    compose_equal_weight_score,
    compose_sign_consensus,
    validate_bundle,
)


def comp(candidate_id, public="2026-10-02T10:00:00Z", universe="U", session="2026-10-02", lineage=None, direction="LONG"):
    return {
        "candidate_id":candidate_id,
        "decision_timestamp":"2026-10-02T12:00:00Z",
        "public_timestamp":public,
        "decision_session":session,
        "value":1.0,
        "source_fingerprint":"fp-"+candidate_id,
        "universe_fingerprint":universe,
        "missing":False,
        "direction":direction,
        "version":"v1",
        "family_lineage":lineage or candidate_id,
    }


def test_order_invariant_bundle_fingerprint():
    common={"decision_timestamp":"2026-10-02T12:00:00Z","decision_session":"2026-10-02","universe_fingerprint":"U"}
    xs=[comp("A",lineage="A"),comp("B",lineage="B",direction="SHORT")]
    a=validate_bundle(xs,common)
    b=validate_bundle(list(reversed(xs)),common)
    assert a["bundle_fingerprint"]==b["bundle_fingerprint"]


def test_future_public_timestamp_fails_pit():
    common={"decision_timestamp":"2026-10-02T12:00:00Z","decision_session":"2026-10-02","universe_fingerprint":"U"}
    try:
        validate_bundle([comp("A",public="2026-10-02T13:00:00Z")],common)
    except RuntimeError as exc:
        assert str(exc)=="PIT_ALIGNMENT_FAIL"
    else:
        raise AssertionError("future information must fail closed")


def test_duplicate_lineage_fails():
    common={"decision_timestamp":"2026-10-02T12:00:00Z","decision_session":"2026-10-02","universe_fingerprint":"U"}
    try:
        validate_bundle([comp("A",lineage="same"),comp("B",lineage="same")],common)
    except RuntimeError as exc:
        assert str(exc)=="DUPLICATE_FAMILY_LINEAGE"
    else:
        raise AssertionError("duplicate lineage must fail closed")


def test_performance_fields_are_forbidden():
    common={"decision_timestamp":"2026-10-02T12:00:00Z","decision_session":"2026-10-02","universe_fingerprint":"U"}
    x=comp("A"); x["holdout_return"]=0.3
    try:
        validate_bundle([x],common)
    except RuntimeError as exc:
        assert "PERFORMANCE_FIELD_PRESENT" in str(exc)
    else:
        raise AssertionError("performance field must be rejected")


def test_consensus_and_equal_weight_are_fixed():
    xs=[comp("A",direction="LONG"),comp("B",direction="SHORT"),comp("C",direction="LONG")]
    assert compose_sign_consensus(xs)["state"]=="LONG_CONSENSUS"
    assert compose_equal_weight_score(xs)["score"]==1.0
