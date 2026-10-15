import json
from pathlib import Path

import pytest

from automation.q220_hash_provenance_diagnostic import (
    CANDIDATE,
    COMPILER_FP,
    EXPECTED_SHA,
    LAST_MODIFIED,
    PRIMARY_URL,
    POPULATION_FP,
    SENSITIVITY_BODY_BYTES,
    SENSITIVITY_BODY_SHA,
    SENSITIVITY_REQUEST_FP,
    SENSITIVITY_RESPONSE_COUNT,
    SOURCE_RECEIPT_FP,
    DiagnosticError,
    classify_primary_hashes,
    fp,
    validate_sensitivity_observations,
)


def test_distinct_whole_document_hashes_same_metadata_remain_unresolved():
    observations = [
        {"scope": "whole_primary_document", "sha256": EXPECTED_SHA, "url": "u", "last_modified": "t"},
        {"scope": "whole_primary_document", "sha256": "a" * 64, "url": "u", "last_modified": "t"},
        {"scope": "whole_primary_document", "sha256": "b" * 64, "url": "u", "last_modified": "t"},
        {"scope": "raw_textblock_body", "sha256": "c" * 64, "url": None, "last_modified": None},
    ]
    out = classify_primary_hashes(EXPECTED_SHA, observations)
    assert out["distinct_whole_primary_sha256_count"] == 3
    assert out["frozen_expected_hash_reproduced"] is True
    assert out["same_url_same_last_modified_multiple_hashes"] is True
    assert out["body_variants_are_separately_scoped"] is True


def test_absent_expected_hash_is_not_mistaken_for_reproduction():
    out = classify_primary_hashes(EXPECTED_SHA, [
        {"scope": "whole_primary_document", "sha256": "a" * 64, "url": "u", "last_modified": "t"},
        {"scope": "whole_primary_document", "sha256": "b" * 64, "url": "u", "last_modified": "t"},
    ])
    assert out["frozen_expected_hash_reproduced"] is False
    assert out["distinct_whole_primary_sha256_count"] == 2


def test_textblock_and_submission_member_hashes_are_not_whole_primary_hashes():
    out = classify_primary_hashes(EXPECTED_SHA, [
        {"scope": "complete_submission_member", "sha256": "a" * 64},
        {"scope": "raw_textblock_body", "sha256": "b" * 64},
    ])
    assert out["whole_primary_observation_count"] == 0
    assert out["frozen_expected_hash_reproduced"] is False


def _valid_sensitivity_receipt():
    names = (
        "population_baseline_first",
        "pit_user_agent_only",
        "pit_accept_only",
        "forensic_combined_profile",
        "population_baseline_repeat",
    )
    profiles = [
        {
            "profile_name": name,
            "status": "FETCHED",
            "http_status": 200,
            "complete_http_200_response": True,
            "response_sha256": SENSITIVITY_BODY_SHA,
            "response_bytes": SENSITIVITY_BODY_BYTES,
            "requested_url": PRIMARY_URL,
            "final_url": PRIMARY_URL,
            "last_modified": LAST_MODIFIED,
        }
        for name in names
    ]
    return {
        "record_type": "q220_http_representation_sensitivity",
        "status": "HTTP_REPRESENTATION_INVARIANT_AT_PROBE_TIME",
        "request_validation_passed": True,
        "source_validation_passed": True,
        "requested_profile_count": SENSITIVITY_RESPONSE_COUNT,
        "completed_request_count": SENSITIVITY_RESPONSE_COUNT,
        "source_download_bytes": SENSITIVITY_BODY_BYTES * SENSITIVITY_RESPONSE_COUNT,
        "source_receipt_fingerprint": SOURCE_RECEIPT_FP,
        "source_population_receipt_fingerprint": POPULATION_FP,
        "request_fingerprint": SENSITIVITY_REQUEST_FP,
        "response_profiles": profiles,
        "comparison": {
            "baseline_repeat_stable": True,
            "profile_body_differences_observed": 0,
            "all_responses_complete_http_200": True,
            "source_responses_share_same_requested_url": True,
            "no_source_bodies_persisted": True,
            "prior_expected_hash_match_count": 0,
        },
    }


def test_pinned_http_sensitivity_receipt_becomes_a_separately_scoped_hash_observation():
    out = validate_sensitivity_observations(_valid_sensitivity_receipt())
    assert out["scope"] == "whole_primary_document"
    assert out["sha256"] == SENSITIVITY_BODY_SHA
    assert out["bytes"] == SENSITIVITY_BODY_BYTES
    assert out["replicate_count"] == 5
    assert out["probe_receipt_fingerprint"]


def test_sensitivity_receipt_rejects_mutated_body_hash_or_metadata():
    receipt = _valid_sensitivity_receipt()
    receipt["response_profiles"][2]["response_sha256"] = "f" * 64
    with pytest.raises(DiagnosticError, match="PROFILE_OBSERVATION_MISMATCH"):
        validate_sensitivity_observations(receipt)


def test_current_canonical_compiler_receipt_matches_current_pin():
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
