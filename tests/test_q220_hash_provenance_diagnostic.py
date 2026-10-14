import json
from pathlib import Path

from automation.q220_hash_provenance_diagnostic import (
    CANDIDATE,
    COMPILER_FP,
    EXPECTED_SHA,
    POPULATION_FP,
    classify_primary_hashes,
    fp,
)


def test_distinct_whole_document_hashes_same_metadata_remain_unresolved():
    observations = [
        {"scope":"whole_primary_document","sha256":EXPECTED_SHA,"url":"u","last_modified":"t"},
        {"scope":"whole_primary_document","sha256":"a"*64,"url":"u","last_modified":"t"},
        {"scope":"whole_primary_document","sha256":"b"*64,"url":"u","last_modified":"t"},
        {"scope":"raw_textblock_body","sha256":"c"*64,"url":None,"last_modified":None},
    ]
    out = classify_primary_hashes(EXPECTED_SHA, observations)
    assert out["distinct_whole_primary_sha256_count"] == 3
    assert out["frozen_expected_hash_reproduced"] is True
    assert out["same_url_same_last_modified_multiple_hashes"] is True
    assert out["body_variants_are_separately_scoped"] is True


def test_absent_expected_hash_is_not_mistaken_for_reproduction():
    out = classify_primary_hashes(EXPECTED_SHA, [
        {"scope":"whole_primary_document","sha256":"a"*64,"url":"u","last_modified":"t"},
        {"scope":"whole_primary_document","sha256":"b"*64,"url":"u","last_modified":"t"},
    ])
    assert out["frozen_expected_hash_reproduced"] is False
    assert out["distinct_whole_primary_sha256_count"] == 2


def test_textblock_and_submission_member_hashes_are_not_whole_primary_hashes():
    out = classify_primary_hashes(EXPECTED_SHA, [
        {"scope":"complete_submission_member","sha256":"a"*64},
        {"scope":"raw_textblock_body","sha256":"b"*64},
    ])
    assert out["whole_primary_observation_count"] == 0
    assert out["frozen_expected_hash_reproduced"] is False


def test_current_canonical_compiler_receipt_matches_frozen_pin():
    root = Path(__file__).resolve().parents[1]
    compiler = json.loads(
        (root / "research/evidence/q220_historical_representation_pit_latest.json")
        .read_text(encoding="utf-8")
    )

    assert compiler["candidate_id"] == CANDIDATE
    assert compiler["status"] == "Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED"
    assert compiler["receipt_fingerprint"] == COMPILER_FP
    assert fp(compiler) == COMPILER_FP
    assert compiler["source_population_receipt_fingerprint"] == POPULATION_FP
    assert compiler["source_hash_failure_count"] == 55
    assert len(compiler["source_hash_failures"]) == 55
    assert compiler["verified_primary_document_count"] == 0
    assert compiler["gate_positive"] is False
