import hashlib

from automation.q218_publish_focus_gate_receipt import (
    blob_sha,
    paper_only_boundary_is_closed,
    performance_boundary_is_closed,
    select_run_artifact,
)


def test_q218_publisher_accepts_event_pair_receipt_schema_with_closed_performance():
    receipt = {
        "performance_authorization": False,
        "promotion": False,
        "live_execution": False,
    }
    assert performance_boundary_is_closed(receipt) is True


def test_q218_publisher_accepts_explicit_scientific_boundary_schema():
    receipt = {
        "scientific_boundary": {"performance_authorized": False},
    }
    assert performance_boundary_is_closed(receipt) is True


def test_q218_publisher_rejects_conflicting_open_performance_boundary():
    receipt = {
        "scientific_boundary": {"performance_authorized": True},
        "performance_authorization": False,
    }
    assert performance_boundary_is_closed(receipt) is False


def test_q218_publisher_rejects_missing_or_non_boolean_performance_boundary():
    assert performance_boundary_is_closed({}) is False
    assert performance_boundary_is_closed({"performance_authorization": "false"}) is False


def test_q218_publisher_accepts_root_paper_only_receipt_schema():
    assert paper_only_boundary_is_closed({"paper_only": True}) is True


def test_q218_publisher_accepts_uppercase_nested_safety_schema():
    assert paper_only_boundary_is_closed({"safety": {"PAPER_ONLY": True}}) is True


def test_q218_publisher_accepts_consistent_duplicate_safety_declarations():
    assert paper_only_boundary_is_closed({
        "paper_only": True,
        "safety": {"paper_only": True, "PAPER_ONLY": True},
    }) is True


def test_q218_publisher_rejects_missing_non_boolean_or_conflicting_safety_flags():
    assert paper_only_boundary_is_closed({}) is False
    assert paper_only_boundary_is_closed({"paper_only": "true"}) is False
    assert paper_only_boundary_is_closed({"safety": {"paper_only": False}}) is False
    assert paper_only_boundary_is_closed({
        "paper_only": True,
        "safety": {"PAPER_ONLY": False},
    }) is False


def test_q218_blob_sha_matches_git_blob_object_format(tmp_path):
    path = tmp_path / "fixture.txt"
    path.write_bytes(b"test")
    expected = hashlib.sha1(b"blob 4\\0test").hexdigest()
    assert blob_sha(path) == expected


def test_q218_artifact_selection_ignores_expired_and_digestless_artifacts():
    payload = {
        "artifacts": [
            {"id": 1, "digest": "sha256:expired", "expired": True},
            {"id": 2, "digest": None, "expired": False},
            {"id": 3, "digest": "sha256:current", "expired": False},
        ]
    }
    assert select_run_artifact(payload) == (3, "sha256:current")


def test_q218_artifact_selection_fails_closed_without_a_current_digested_artifact():
    assert select_run_artifact({"artifacts": []}) is None
    assert select_run_artifact({"artifacts": [{"id": 1, "digest": "sha256:x", "expired": True}]}) is None
    assert select_run_artifact({"artifacts": [{"id": 1, "digest": None, "expired": False}]}) is None
