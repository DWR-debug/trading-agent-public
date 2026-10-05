from automation.q218_q221_candidate_gate_compiler import compile_gate


def _specs():
    return {
        "schema_version": "1.0",
        "candidates": [{"id": cid} for cid in ("Q218", "Q219", "Q220", "Q221")],
        "shared_contract": {
            "pre_formal_robustness_gate": True,
            "performance_authorization": False,
            "promotion_authorization": False,
            "live_execution": False,
        },
    }


def _census():
    issuers = {}
    for symbol in ("A", "B", "C", "D", "E", "F", "G", "H"):
        issuers[symbol] = {
            "pairability_observed": True,
            "latest_10k": {"acceptance_datetime_found": True},
            "latest_8k_earnings_release": {"acceptance_datetime_found": True},
        }
    return {
        "candidate_ids": ["Q218", "Q219", "Q220", "Q221"],
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion_authorization": False,
        "live_execution": False,
        "candidates": [
            {"candidate_id": "Q218", "sec_submission_census": {"issuer_results": issuers}},
            {"candidate_id": "Q219", "q129_contract_check": {
                "contract_present": True,
                "independent_pit_receipt_present": True,
                "same_day_use_allowed": False,
            }},
            {"candidate_id": "Q220", "sec_notes_census": {
                "zip_parse_ok": True,
                "required_member_markers_present": {
                    "sub.txt": True, "tag.txt": True, "dim.txt": True,
                    "num.txt": True, "txt.txt": True,
                },
            }},
            {"candidate_id": "Q221", "usa_rdtne_census": {
                "rdtne_marker_found": True,
                "competition_marker_found": True,
                "transaction_marker_found": True,
                "lookahead_used": False,
            }},
        ],
    }


def test_compiler_keeps_all_four_candidates_non_authorizing():
    result = compile_gate(_census(), _specs())
    assert set(result["results"]) == {"Q218", "Q219", "Q220", "Q221"}
    assert result["all_source_structure_components_ready"] is True
    assert result["performance_authorized"] is False
    assert result["promotion_authorized"] is False
    assert result["live_execution"] is False
    assert result["results"]["Q219"]["same_day_use_allowed"] is False
