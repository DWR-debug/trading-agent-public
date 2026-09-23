from automation.one_command_research import run_universe


def test_runner_has_effective_common_history():
    import inspect
    source = inspect.getsource(run_universe)
    assert "spec.target_count" in source
    assert "minimum_count" in source
    assert "common_count = min(" in source


def test_runner_falls_back_to_common_history(monkeypatch, tmp_path):
    import automation.one_command_research as runner

    monkeypatch.chdir(tmp_path)
    calls = []

    class Spec:
        target_count = 2500

    def fake_prepare(*, target_count, **_kwargs):
        calls.append(target_count)
        count = 1000 if target_count == 1000 else min(1103, target_count)
        return {
            "datasets": [
                {"symbol": "A", "candle_count": count, "data_start": "a", "data_end": "b"},
                {"symbol": "B", "candle_count": count, "data_start": "a", "data_end": "b"},
            ]
        }, None

    def fake_run_research(*_args, **_kwargs):
        return {"status": "PASSED", "failed_gates": []}, tmp_path / "report.json"

    monkeypatch.setattr(runner, "get_universe", lambda _name: Spec())
    monkeypatch.setattr(runner, "prepare", fake_prepare)
    monkeypatch.setattr(
        runner,
        "datasets_for",
        lambda _name: [("A", "1d", 2500), ("B", "1d", 2500)],
    )
    monkeypatch.setattr(runner, "run_research", fake_run_research)

    report = run_universe("test")

    assert report["status"] == "PASSED"
    assert calls == [2500, 2000, 1500, 1000]


def test_yahoo_loader_supports_partial_history():
    import inspect
    from data.yahoo_loader import load_yahoo_history

    assert "allow_partial" in inspect.signature(load_yahoo_history).parameters


def test_prepare_supports_minimum_history_gate():
    import inspect
    from automation.prepare_research_data import prepare

    assert "minimum_count" in inspect.signature(prepare).parameters