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
        "q218_sec_pair_census": {"issuer_results": issuers},
        "q219_q129_contract": {
            "contract_present": True,
            "independent_pit_receipt_present": True,
            "same_day_use_allowed": False,
        },
        "q220_sec_notes_census": {
            "zip_parse_ok": True,
            "required_member_markers_present": {
                "sub": True, "tag": True, "dim": True,
                "num": True, "txt": True,
            },
        },
        "q221_usa_rdtne_census": {
            "rdtne_marker_found": True,
            "competition_marker_found": True,
            "transaction_marker_found": True,
            "lookahead_used": False,
        },
    }


def test_compiler_keeps_all_four_candidates_non_authorizing():
    result = compile_gate(_census(), _specs())
    assert set(result["results"]) == {"Q218", "Q219", "Q220", "Q221"}
    assert result["all_source_structure_components_ready"] is True
    assert result["performance_authorization"] is False
    assert result["promotion_authorization"] is False
    assert result["live_execution"] is False
    assert result["results"]["Q219"]["same_day_use_allowed"] is False


def test_compiler_handles_missing_latest_8k_without_crashing():
    census = _census()
    for issuer in census["q218_sec_pair_census"]["issuer_results"].values():
        issuer["latest_8k_earnings_release"] = None
        issuer["pairability_observed"] = False
    result = compile_gate(census, _specs())
    assert result["results"]["Q218"]["status"] == "SOURCE_STRUCTURE_INCOMPLETE"
    assert result["results"]["Q218"]["accepted_latest_8k_earnings_release_count"] == 0
    assert result["performance_authorization"] is False
    assert result["promotion_authorization"] is False
    assert result["live_execution"] is False
