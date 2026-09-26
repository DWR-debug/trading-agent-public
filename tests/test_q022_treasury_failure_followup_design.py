import json
from pathlib import Path

from research.research_queue import default_research_queue

ROOT = Path(__file__).parents[1]


def test_q022_design_is_unranked_and_non_executing():
    payload = json.loads(
        (ROOT / "research" / "preregistrations" / "q022_treasury_failure_followup_design_2026_09_26.json")
        .read_text(encoding="utf-8")
    )
    assert payload["task_id"] == "Q-022-TREASURY-FAILURE-FOLLOWUP-DESIGN"
    assert payload["status"] == "DESIGN_ONLY"
    assert payload["ranked"] is False
    assert payload["selection_used"] is False
    assert payload["performance_trial_authorized"] is False
    assert payload["holdout_used_for_selection"] is False
    assert payload["q020_retuning"] is False
    assert payload["gate_changes"] is False
    assert payload["live_execution"] is False
    assert [item["id"] for item in payload["candidates"]] == ["H1", "H2", "H3", "H4", "H5", "H6"]
    assert all(item["status"] == "UNRANKED" for item in payload["candidates"])
    assert payload["common_protocol"]["fresh_symbol_disjoint_validation"] is True
    assert payload["common_protocol"]["coverage_first"] is True
    assert payload["common_protocol"]["holdout_blind"] is True
    assert payload["common_protocol"]["parameter_search"] is False
    assert payload["common_protocol"]["asset_search"] is False
    assert payload["common_protocol"]["threshold_search"] is False
    assert payload["common_protocol"]["variant_search"] is False
    assert payload["common_protocol"]["horizon_search"] is False
    assert payload["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_q022_is_next_deterministic_queue_item():
    queue = default_research_queue()
    assert queue.next_task() is not None
    assert queue.next_task().task_id == "Q-022-TREASURY-FAILURE-FOLLOWUP-DESIGN"
    by_id = {task.task_id: task for task in queue.all()}
    assert by_id["Q-021-TREASURY-AUCTION-FAILURE-MECHANISM-DIAGNOSIS"].status == "COMPLETED"
    assert by_id["Q-022-TREASURY-FAILURE-FOLLOWUP-DESIGN"].status == "PENDING"
