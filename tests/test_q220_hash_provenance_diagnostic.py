from automation.q220_hash_provenance_diagnostic import classify_primary_hashes, EXPECTED_SHA


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
