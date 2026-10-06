from pathlib import Path
import json
from automation.evidence_graph_stage4_stage5 import (
    candidate_signature,
    jaccard,
    novelty_analysis,
    bridge_proposals,
)

def test_signature_is_deterministic():
    spec={"id":"Q1","mechanism":"filing disclosure state","event_clock":"SEC acceptance","economic_relation":"disclosure to response"}
    links={"Q1":{"SEC_CLOCK"}}
    a=candidate_signature(spec,links)
    b=candidate_signature(spec,links)
    assert a==b
    assert "disclosure" in a["tokens"]

def test_jaccard_bounds():
    assert jaccard({"a","b"},{"b","c"})==1/3
    assert 0 <= jaccard(set(),{"x"}) <= 1

def test_convergence_classification_is_review_only():
    c={
      "Q1":{"tokens":["filing","disclosure","response"],"components":["SEC"],"source_domains":["sec.gov"],"mechanism_text":""},
      "Q2":{"tokens":["filing","disclosure","response"],"components":["SEC"],"source_domains":["sec.gov"],"mechanism_text":""},
      "Q3":{"tokens":["procurement","award","exposure"],"components":["USA"],"source_domains":["usaspending.gov"],"mechanism_text":""},
    }
    rows=novelty_analysis(c)
    q1=next(x for x in rows if x["candidate"]=="Q1")
    assert q1["overlap_class"]=="POTENTIAL_CONVERGENCE"
    q3=next(x for x in rows if x["candidate"]=="Q3")
    assert q3["novelty_score"] > 0.5

def test_bridge_proposals_do_not_create_candidates():
    c={
      "Q1":{"tokens":["filing","disclosure"],"components":["SEC"],"source_domains":["sec.gov"],"mechanism_text":""},
      "Q2":{"tokens":["options","smirk","response"],"components":["SEC"],"source_domains":["options"],"mechanism_text":""},
    }
    p=bridge_proposals(c)
    assert p
    assert all(x["status"]=="HYPOTHESIS_PROPOSAL_REVIEW_REQUIRED" for x in p)
    assert all("composite candidate" in x["text"] for x in p)

def test_safety_contract_exists_and_is_closed():
    root=Path(__file__).parents[1]
    contract=json.loads((root/"research/governance/evidence_graph_stage4_stage5_contract_2026_10_06.json").read_text())
    assert contract["status"].startswith("ACTIVE")
    assert contract["safety"]["PAPER_ONLY"] is True
    assert contract["stage_5"]["no_optimization_rule"].startswith("Novelty/convergence")


def test_live_contract_relations_are_materialized():
    from automation.evidence_graph_stage4_stage5 import build
    graph, novelty, bridges, negatives, candidates = build()
    assert any(edge["type"] == "reuses_component" for edge in graph["edges"])
    assert any(edge["type"] == "shares_clock_and_filing_substrate" for edge in graph["edges"])
    assert len(novelty) == len(candidates)
    assert isinstance(negatives, list)
