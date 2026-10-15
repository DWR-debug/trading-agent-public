import hashlib
import json
from pathlib import Path

from automation.q221_pre_event_identity_bridge_pilot import (
    MANIFEST_FP,
    PARENT_MAP_FP,
    SOURCE_BY_ID,
    SOURCES,
    TRANSACTIONS,
    canonical_fingerprint,
    make_analysis,
    normalize_text,
    parse_key_value_request,
    validate_request_and_prereg,
)


ROOT = Path(__file__).resolve().parents[1]


def _synthetic_bundle():
    manifest = {
        "candidate_id": "Q221",
        "receipt_fingerprint": MANIFEST_FP,
        "sampled_transaction_count": 348,
    }
    parent_map = {"receipt_fingerprint": PARENT_MAP_FP}
    selected = {}
    for row_id, target in TRANSACTIONS.items():
        selected[row_id] = {
            "current_parent_classification": "CURRENT_PARENT_ENTITY_LEAD",
            "current_profile_observation": {
                "profile": {
                    "parent_name": target["current_parent_name"],
                    "parent_uei": target["current_parent_uei"],
                }
            },
        }
    observations = []
    bodies = {}
    for spec in SOURCES:
        body = ("<html><body>" + " ".join(spec["required_tokens"]) + "</body></html>").encode()
        bodies[spec["id"]] = body
        observations.append({
            "source_id": spec["id"],
            "requested_url": spec["url"],
            "final_url": spec["url"],
            "http_status": 200,
            "content_type": "text/html; charset=utf-8",
            "response_bytes": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest(),
        })
    return manifest, parent_map, selected, observations, bodies


def test_normalizer_decodes_html_and_normalizes_legal_entity_punctuation():
    raw = b"<html><body>CACI, INC. &ndash; FEDERAL, a Delaware corporation</body></html>"
    normalized = normalize_text(raw)
    assert "caci, inc. - federal" in normalized
    assert "a delaware corporation" in normalized


def test_exact_source_token_contract_covers_only_the_seven_frozen_public_pages():
    assert len(SOURCES) == 7
    assert set(SOURCE_BY_ID) == {
        "caci_index",
        "caci_ex21",
        "aurora_index",
        "aurora_agreement",
        "orbital_index",
        "orbital_ex21",
        "northrop_release",
    }
    assert len({x["url"] for x in SOURCES}) == 7
    assert all(x["url"].startswith("https://") for x in SOURCES)
    assert all(x["allowed_host"] in {"www.sec.gov", "investor.northropgrumman.com"} for x in SOURCES)


def test_analysis_preserves_two_pre_event_leads_and_one_legal_form_conflict_without_mapping():
    manifest, parent_map, selected, observations, bodies = _synthetic_bundle()
    analysis = make_analysis(manifest, parent_map, selected, observations, bodies)
    assert analysis["status"] == "Q221_PRE_EVENT_IDENTITY_BRIDGE_PILOT_COMPLETE_MAPPING_UNRESOLVED"
    rows = {x["row_id"]: x for x in analysis["transaction_assessments"]}
    assert rows["CACI_2019"]["pre_event_evidence_classification"] == (
        "PRE_EVENT_SUBSIDIARY_EVIDENCE_FOUND_PERSISTENCE_TO_ACTION_DATE_UNPROVEN"
    )
    assert rows["AURORA_2024"]["pre_event_evidence_classification"] == (
        "PRE_EVENT_PARENT_RELATION_EVIDENCE_FOUND_PERSISTENCE_TO_ACTION_DATE_UNPROVEN"
    )
    assert rows["ATK_2019"]["pre_event_evidence_classification"] == "BLOCKED_LEGAL_ENTITY_FORM_MISMATCH"
    for row in rows.values():
        assert row["issuer_symbol"] is None
        assert row["historical_parent_lineage_proven"] is False
        assert row["persistence_to_action_date_proven"] is False
        assert row["historical_first_public_observation_proven"] is False
        assert row["recipient_to_issuer_mapping_frozen"] is False
    assert analysis["authority"]["performance_authorization"] is False
    assert analysis["authority"]["promotion"] is False
    assert analysis["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_analysis_fails_closed_if_required_atk_legal_entity_text_is_missing():
    manifest, parent_map, selected, observations, bodies = _synthetic_bundle()
    bodies["orbital_ex21"] = b"<html><body>ATK Launch Systems LLC, Delaware</body></html>"
    row = next(x for x in observations if x["source_id"] == "orbital_ex21")
    row["response_bytes"] = len(bodies["orbital_ex21"])
    row["response_sha256"] = hashlib.sha256(bodies["orbital_ex21"]).hexdigest()
    analysis = make_analysis(manifest, parent_map, selected, observations, bodies)
    assert analysis["status"] == "Q221_PRE_EVENT_IDENTITY_BRIDGE_PILOT_SOURCE_EVIDENCE_INCOMPLETE"
    atk = next(x for x in analysis["transaction_assessments"] if x["row_id"] == "ATK_2019")
    assert atk["pre_event_evidence_classification"] == "SOURCE_EVIDENCE_INCOMPLETE"
    assert atk["recipient_to_issuer_mapping_frozen"] is False


def test_frozen_request_and_preregistration_agree_on_limits_urls_and_gate_authority():
    request = parse_key_value_request(ROOT / "research/run_requests/q221_pre_event_identity_bridge_pilot.trigger")
    prereg = json.loads(
        (ROOT / "research/preregistrations/q221_pre_event_identity_bridge_pilot_2026_10_15.json")
        .read_text(encoding="utf-8")
    )
    validate_request_and_prereg(request, prereg)
    assert request["SOURCE_REQUEST_COUNT"] == "7"
    assert request["MAX_BYTES_PER_SOURCE"] == "300000"
    assert request["MAX_TOTAL_BYTES"] == "900000"
    assert request["NO_USASPENDING_API_REQUESTS"] == "true"
    assert request["NO_ISSUER_MAPPING"] == "true"
    assert request["HISTORICAL_FIRST_PUBLIC_OBSERVATION_PROVEN"] == "false"
    assert prereg["decision_boundary"]["recipient_to_issuer_mapping_frozen"] is False


def test_analysis_fingerprint_does_not_include_capture_timestamp_or_workflow_run_id():
    manifest, parent_map, selected, observations, bodies = _synthetic_bundle()
    analysis_a = make_analysis(manifest, parent_map, selected, observations, bodies)
    analysis_b = json.loads(json.dumps(analysis_a))
    assert canonical_fingerprint(analysis_a) == canonical_fingerprint(analysis_b)
