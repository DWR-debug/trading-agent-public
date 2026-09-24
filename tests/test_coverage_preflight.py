import json
from pathlib import Path

from automation.coverage_preflight import run_preflight


def test_coverage_preflight_passes_without_performance(monkeypatch, tmp_path):
    spec_path = Path("research/preregistrations/trial_039_network_momentum_2026_09_24.json")
    symbols = tuple(json.loads(spec_path.read_text())["symbols"])

    from datetime import datetime, timedelta, timezone

    base = datetime(2010, 1, 1, tzinfo=timezone.utc)

    class Bar:
        def __init__(self, ts, value):
            self.timestamp = ts
            self.open = value
            self.high = value + 1.0
            self.low = value - 1.0
            self.close = value + 0.25
            self.volume = value

    bars = tuple(
        Bar(base + timedelta(days=i), 100.0 + i)
        for i in range(3520)
    )

    def fake_loader(symbol, interval, total, **kwargs):
        assert symbol in symbols
        assert interval == "1d"
        assert total == 3520
        return list(bars)

    monkeypatch.setattr("automation.coverage_preflight.load_yahoo_history", fake_loader)
    result = run_preflight(spec_path, output_root=tmp_path)

    assert result["status"] == "coverage_passed"
    assert result["common_calendar_count"] == 3520
    assert result["performance_evaluation"] is False
    assert result["holdout_evaluation"] is False
    assert result["selection_used"] is False
    assert result["safety"]["paper_only"] is True
    assert Path(result["output"]).is_absolute() is True


def test_coverage_preflight_marks_short_history_data_invalid(monkeypatch, tmp_path):
    spec_path = Path("research/preregistrations/trial_039_network_momentum_2026_09_24.json")
    symbols = tuple(json.loads(spec_path.read_text())["symbols"])

    from datetime import datetime, timedelta, timezone

    base = datetime(2010, 1, 1, tzinfo=timezone.utc)
    full = [type("Bar", (), {"timestamp": base + timedelta(days=i)})() for i in range(3520)]
    short = full[:-10]

    def fake_loader(symbol, interval, total, **kwargs):
        return short if symbol == symbols[0] else full

    monkeypatch.setattr("automation.coverage_preflight.load_yahoo_history", fake_loader)
    result = run_preflight(spec_path, output_root=tmp_path)

    assert result["status"] == "DATA_INVALID"
    assert result["insufficient_symbols"] == {symbols[0]: 3510}
    assert result["scientific_outcome"] == "NO_SCIENTIFIC_OUTCOME"
    assert result["performance_evaluation"] is False
    assert result["holdout_evaluation"] is False
