import json
from pathlib import Path

from automation.pre_pit_falsification_checks import CANDIDATES, main


def test_pre_pit_falsification_battery_passes_for_all_candidates(tmp_path, monkeypatch):
    out = tmp_path / "receipt.json"
    monkeypatch.setattr("sys.argv", ["pre_pit_falsification_checks", "--output", str(out)])
    assert main() == 0
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert receipt["status"] == "PRE_PIT_FALSIFICATION_CHECKS_COMPLETED"
    assert [x["candidate_id"] for x in receipt["candidates"]] == list(CANDIDATES)
    assert all(x["pit_authorized"] is False for x in receipt["candidates"])
    assert all(x["performance_evidence"] is False for x in receipt["candidates"])


def test_pre_pit_module_is_non_authorizing():
    source = Path("automation/pre_pit_falsification_checks.py").read_text(encoding="utf-8")
    assert '"performance_evidence": False' in source
    assert '"live_execution": False' in source
    assert '"pit_authorized": False' in source
