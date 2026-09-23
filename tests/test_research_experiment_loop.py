from automation.research_experiment_loop import (
    _classify_result,
    run_loop,
)


def test_classification():
    assert _classify_result({"status": "PASSED", "failed_gates": []}) == "PASSED"
    assert _classify_result(
        {"status": "BLOCKED", "failed_gates": ["SOUN 1d: data_quality"]}
    ) == "BLOCKED"
    assert _classify_result(
        {"status": "BLOCKED", "failed_gates": ["SOUN 1d: walk_forward"]}
    ) == "REJECT"
    assert _classify_result({"status": "BLOCKED", "failed_gates": []}) == "BLOCKED"


def test_loop_checkpoints_and_resumes(tmp_path, monkeypatch):
    calls = []

    b_attempts = 0

    def fake_run_universe(universe, **_kwargs):
        nonlocal b_attempts
        calls.append(universe)
        if universe == "B":
            b_attempts += 1
            if b_attempts == 1:
                raise ValueError("simulierter Datenfehler")
            return {"status": "PASSED", "failed_gates": []}
        if universe == "C":
            return {"status": "BLOCKED", "failed_gates": ["C 1d: holdout"]}
        return {"status": "PASSED", "failed_gates": []}

    monkeypatch.setattr(
        "automation.research_experiment_loop.run_universe",
        fake_run_universe,
    )

    state_path = tmp_path / "loop.json"

    first = run_loop(
        universes=("A", "B", "C"),
        state_path=state_path,
        max_universes=2,
    )

    assert first["status"] == "PARTIAL"
    assert calls == ["A", "B"]
    assert [item["classification"] for item in first["results"]] == [
        "PASSED",
        "BLOCKED",
    ]

    second = run_loop(
        universes=("A", "B", "C"),
        state_path=state_path,
        resume=True,
    )

    assert second["status"] == "COMPLETED"
    assert calls == ["A", "B", "B", "C"]
    assert {
        item["universe"]: item["classification"]
        for item in second["results"]
    } == {
        "A": "PASSED",
        "B": "PASSED",
        "C": "REJECT",
    }


def test_loop_refuses_changed_universe_state(tmp_path):
    state_path = tmp_path / "loop.json"

    run_loop(
        universes=("A", "B"),
        state_path=state_path,
        max_universes=1,
    )

    import pytest

    with pytest.raises(RuntimeError, match="Universum"):
        run_loop(
            universes=("A", "C"),
            state_path=state_path,
            resume=True,
        )



def test_loop_state_fingerprint_rejects_tampering(tmp_path, monkeypatch):
    import json
    import pytest

    state_path = tmp_path / "loop.json"

    monkeypatch.setattr(
        "automation.research_experiment_loop.run_universe",
        lambda _universe, **_kwargs: {
            "status": "PASSED",
            "failed_gates": [],
        },
    )

    run_loop(
        universes=("A",),
        state_path=state_path,
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["completed"] = []
    state_path.write_text(json.dumps(state), encoding="utf-8")

    with pytest.raises(RuntimeError, match="gültigen Fingerprint"):
        run_loop(
            universes=("A",),
            state_path=state_path,
            resume=True,
        )


def test_loop_state_without_fingerprint_is_rejected(tmp_path):
    import json
    import pytest

    state_path = tmp_path / "loop.json"

    run_loop(
        universes=("A",),
        state_path=state_path,
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.pop("state_fingerprint")
    state_path.write_text(json.dumps(state), encoding="utf-8")

    with pytest.raises(RuntimeError, match="gültigen Fingerprint"):
        run_loop(
            universes=("A",),
            state_path=state_path,
            resume=True,
        )
