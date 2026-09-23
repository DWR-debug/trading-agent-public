from pathlib import Path

import pytest

from automation.selection_profile_experiments import (
    run_selection_profile_experiments,
)


def test_selection_profile_experiment_runs_and_resumes(
    tmp_path,
    monkeypatch,
):
    calls = []

    def fake_run_universe(universe, **kwargs):
        profile = kwargs["selection_profile"]
        root = Path(kwargs["run_root"])
        report_dir = root / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "analysis_test.json").write_text(
            "{}",
            encoding="utf-8",
        )
        manifest_path = root / "run_manifest.json"
        manifest_path.write_text("{}", encoding="utf-8")

        calls.append(
            (
                profile,
                kwargs["prepare_data"],
                kwargs.get("prepared_data_manifest"),
            )
        )
        return {
            "status": "PASSED" if profile == "score_max" else "BLOCKED",
            "failed_gates": (
                []
                if profile == "score_max"
                else ["TEST 1d: walk_forward"]
            ),
            "run_manifest": {
                "path": str(manifest_path),
                "run_fingerprint": f"fp-{profile}",
            },
        }

    monkeypatch.setattr(
        "automation.selection_profile_experiments.run_universe",
        fake_run_universe,
    )

    root = tmp_path / "experiment"
    state_path = root / "state.json"
    profiles = ("score_max", "boundary_averse", "risk_averse")

    first = run_selection_profile_experiments(
        "test",
        profiles=profiles,
        root=root,
        state_path=state_path,
    )

    assert first["status"] == "COMPLETED"
    assert calls[0][0:2] == ("score_max", True)
    assert calls[1][0:2] == ("boundary_averse", False)
    assert calls[2][0:2] == ("risk_averse", False)
    assert calls[0][2] is None
    assert calls[1][2] == root / "score_max" / "data_manifest.json"
    assert calls[2][2] == root / "score_max" / "data_manifest.json"
    assert {
        item["profile"]: item["run_manifest"]
        for item in first["results"]
    } == {
        "score_max": str(root / "score_max" / "run_manifest.json"),
        "boundary_averse": str(root / "boundary_averse" / "run_manifest.json"),
        "risk_averse": str(root / "risk_averse" / "run_manifest.json"),
    }
    assert {
        item["profile"]: item["classification"]
        for item in first["results"]
    } == {
        "score_max": "PASSED",
        "boundary_averse": "REJECT",
        "risk_averse": "REJECT",
    }

    second = run_selection_profile_experiments(
        "test",
        profiles=profiles,
        root=root,
        state_path=state_path,
        resume=True,
    )

    assert second["status"] == "COMPLETED"
    assert calls == [
        ("score_max", True, None),
        ("boundary_averse", False, root / "score_max" / "data_manifest.json"),
        ("risk_averse", False, root / "score_max" / "data_manifest.json"),
    ]


def test_selection_profile_experiment_refuses_changed_configuration(
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "state.json"

    def fake_run_universe(_universe, **_kwargs):
        return {
            "status": "PASSED",
            "failed_gates": [],
            "run_manifest": {
                "path": str(tmp_path / "run_manifest.json"),
                "run_fingerprint": "fp",
            },
        }

    monkeypatch.setattr(
        "automation.selection_profile_experiments.run_universe",
        fake_run_universe,
    )

    run_selection_profile_experiments(
        "test",
        profiles=("score_max", "boundary_averse"),
        root=tmp_path / "root",
        state_path=state_path,
    )

    with pytest.raises(RuntimeError, match="Konfiguration"):
        run_selection_profile_experiments(
            "test",
            profiles=("score_max", "risk_averse"),
            root=tmp_path / "root",
            state_path=state_path,
            resume=True,
        )



def test_selection_experiment_state_fingerprint_rejects_tampering(
    tmp_path,
    monkeypatch,
):
    import json

    def fake_run_universe(_universe, **_kwargs):
        return {
            "status": "PASSED",
            "failed_gates": [],
            "run_manifest": {
                "path": str(tmp_path / "run_manifest.json"),
                "run_fingerprint": "fp",
            },
        }

    monkeypatch.setattr(
        "automation.selection_profile_experiments.run_universe",
        fake_run_universe,
    )

    state_path = tmp_path / "state.json"
    run_selection_profile_experiments(
        "test",
        profiles=("score_max",),
        root=tmp_path / "root",
        state_path=state_path,
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["completed"] = []
    state_path.write_text(json.dumps(state), encoding="utf-8")

    with pytest.raises(RuntimeError, match="gültigen State-Fingerprint"):
        run_selection_profile_experiments(
            "test",
            profiles=("score_max",),
            root=tmp_path / "root",
            state_path=state_path,
            resume=True,
        )


def test_selection_experiment_state_without_fingerprint_is_rejected(
    tmp_path,
    monkeypatch,
):
    import json

    def fake_run_universe(_universe, **_kwargs):
        return {
            "status": "PASSED",
            "failed_gates": [],
            "run_manifest": {
                "path": str(tmp_path / "run_manifest.json"),
                "run_fingerprint": "fp",
            },
        }

    monkeypatch.setattr(
        "automation.selection_profile_experiments.run_universe",
        fake_run_universe,
    )

    state_path = tmp_path / "state.json"
    run_selection_profile_experiments(
        "test",
        profiles=("score_max",),
        root=tmp_path / "root",
        state_path=state_path,
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.pop("state_fingerprint")
    state_path.write_text(json.dumps(state), encoding="utf-8")

    with pytest.raises(RuntimeError, match="gültigen State-Fingerprint"):
        run_selection_profile_experiments(
            "test",
            profiles=("score_max",),
            root=tmp_path / "root",
            state_path=state_path,
            resume=True,
        )



def test_selection_experiment_records_statistical_family(
    tmp_path,
    monkeypatch,
):
    def fake_run_universe(_universe, **_kwargs):
        return {
            "status": "PASSED",
            "failed_gates": [],
            "run_manifest": {
                "path": str(tmp_path / "run_manifest.json"),
                "run_fingerprint": "fp",
            },
        }

    monkeypatch.setattr(
        "automation.selection_profile_experiments.run_universe",
        fake_run_universe,
    )

    state = run_selection_profile_experiments(
        "test",
        profiles=("score_max", "boundary_averse"),
        root=tmp_path / "root",
        state_path=tmp_path / "state.json",
    )

    family = state["statistical_family"]
    assert family["family_type"] == "selection_profile_comparison"
    assert family["profile_count"] == 2
    assert family["shared_input_universe"] == "test"
    assert family["shared_input_dataset"] is True
    assert family["multiple_selection_profiles"] is True
