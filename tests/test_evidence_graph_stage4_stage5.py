from pathlib import Path
import json
from automation.evidence_graph_stage4_stage5 import (
    candidate_signature,
    jaccard,
    novelty_analysis,
    bridge_proposals,
    candidate_inventory,
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

def test_overlap_inventory_includes_legacy_waves_and_discovery_seeds():
    inventory = candidate_inventory()
    # Q157 lives in a legacy wave; Q233 lives in the discovery seed pack.
    # Q227/Q231 are in the current candidate contract. All must be compared.
    assert {"Q157", "Q227", "Q231", "Q233"}.issubset(inventory)
    assert any(
        source.endswith("q152_q165_candidate_wave_2026_10_03.json")
        for source in inventory["Q157"]["inventory_sources"]
    )
    assert any(
        source.endswith("orthogonal_discovery_seed_pack_2026_10_06.json")
        for source in inventory["Q233"]["inventory_sources"]
    )
    # Current canonical contracts take precedence over copies in older waves.
    assert inventory["Q227"]["inventory_source"] == (
        "research/candidates/orthogonal_candidate_specs_2026-10-05.json"
    )


def test_legacy_overlap_comparison_is_review_only_and_deterministic():
    inventory_a = candidate_inventory()
    inventory_b = candidate_inventory()
    assert list(inventory_a) == list(inventory_b)
    signatures = {
        cid: candidate_signature(spec, {})
        for cid, spec in inventory_a.items()
    }
    rows = novelty_analysis(signatures)
    ids = {row["candidate"] for row in rows}
    assert {"Q157", "Q227", "Q231", "Q233"}.issubset(ids)
    assert len(rows) == len(signatures)
    assert all(
        "POTENTIAL_CONVERGENCE" in row["overlap_class"]
        or "AMBIGUOUS" in row["overlap_class"]
        or "LIKELY_ORTHOGONAL" in row["overlap_class"]
        for row in rows
    )


def test_missing_signature_dimensions_fail_closed_as_ambiguous():
    signatures = {
        "Q104:I22": {
            "tokens": ["filing", "arrival", "density"],
            "components": [],
            "source_domains": [],
            "mechanism_text": "filing arrival density",
        },
        "Q231": {
            "tokens": ["filing", "foia", "acquisition"],
            "components": [],
            "source_domains": [],
            "mechanism_text": "filing foia acquisition",
        },
    }

    result = next(
        row for row in novelty_analysis(signatures)
        if row["candidate"] == "Q104:I22"
    )

    # Missing metadata is not evidence of equality and is not evidence of
    # orthogonality. Only one of the three frozen dimensions is observable.
    assert result["overlap_class"] == "AMBIGUOUS"
    assert result["max_convergence_score"] is None
    assert result["novelty_score"] is None
    assert result["signature_coverage"] == {
        "required_dimensions": 3,
        "complete_peer_comparisons": 0,
        "incomplete_peer_comparisons": 1,
        "peer_comparison_count": 1,
        "complete": False,
    }
    peer = result["top_peers"][0]
    assert peer["score"] is None
    assert peer["token_jaccard"] is not None
    assert peer["component_jaccard"] is None
    assert peer["domain_jaccard"] is None
    assert peer["signature_coverage_complete"] is False


def test_empty_component_and_domain_sets_are_not_similarity_evidence():
    # Public helper retains its historical numeric contract, but Stage 5 must
    # not interpret two absent dimensions as perfect convergence.
    assert jaccard(set(), set()) == 1.0
    signatures = {
        "A": {
            "tokens": ["filing", "arrival"],
            "components": [],
            "source_domains": [],
            "mechanism_text": "",
        },
        "B": {
            "tokens": ["award", "release"],
            "components": [],
            "source_domains": [],
            "mechanism_text": "",
        },
    }
    rows = novelty_analysis(signatures)
    assert all(row["overlap_class"] == "AMBIGUOUS" for row in rows)
    assert all(row["signature_coverage"]["complete"] is False for row in rows)
