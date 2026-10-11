from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone

from automation.q220_historical_representation_pit import textblock_states as primary_textblock_states
from automation.q220_independent_pit_reproduction import (
    NUMERIC_QNAMES,
    canonical_fingerprint,
    change_states,
    parse_structured_states,
    parse_textblock_states,
    prefix_summaries,
    reproduce,
    sha256,
)


def _record(cik, accession, form, filed_date, accepted):
    return {
        "canonical_key": {
            "cik": cik,
            "accession": accession,
            "form": form,
            "filed_date": filed_date,
        },
        "acceptance_datetime": accepted,
    }


def test_tree_parser_preserves_adjacent_self_closing_and_populated_textblocks():
    document = """
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
      <ix:nonNumeric name="us-gaap:EmptyTextBlock" contextRef="C0" id="empty" />
      <ix:nonNumeric name="us-gaap:RiskTextBlock" contextRef="C1" id="risk"><p>Risk <b>disclosure</b></p></ix:nonNumeric>
      <ix:nonNumeric name="us-gaap:SecondEmptyTextBlock" contextRef="C2" id="empty2"></ix:nonNumeric>
      <ix:nonNumeric name="us-gaap:OtherTextBlock" contextRef="C3" id="other">Other disclosure</ix:nonNumeric>
    </html>
    """
    states = parse_textblock_states(document)
    assert set(states) == {
        "us-gaap:EmptyTextBlock",
        "us-gaap:RiskTextBlock",
        "us-gaap:SecondEmptyTextBlock",
        "us-gaap:OtherTextBlock",
    }
    assert states["us-gaap:EmptyTextBlock"][0]["normalized_character_count"] == 0
    assert states["us-gaap:EmptyTextBlock"][0]["content_sha256"] is None
    assert states["us-gaap:RiskTextBlock"][0]["normalized_character_count"] == len("Risk disclosure")
    assert states["us-gaap:OtherTextBlock"][0]["normalized_character_count"] == len("Other disclosure")


def test_continuation_chain_is_reconstructed_and_hashed():
    document = """
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
      <ix:nonNumeric name="us-gaap:RiskTextBlock" contextRef="C1" id="risk" continuedAt="c1"><p>Alpha <b>Beta</b></p></ix:nonNumeric>
      <ix:continuation id="c1" continuedAt="c2"><p>Gamma</p></ix:continuation>
      <ix:continuation id="c2">Delta</ix:continuation>
      <ix:nonNumeric name="us-gaap:OtherTextBlock" contextRef="C2" id="other">Second fact</ix:nonNumeric>
    </html>
    """
    state = parse_textblock_states(document)["us-gaap:RiskTextBlock"][0]
    expected = "Alpha Beta Gamma Delta"
    assert state["continued_chain_length"] == 2
    assert state["continued_chain_complete"] is True
    assert state["normalized_character_count"] == len(expected)
    assert state["content_sha256"] == hashlib.sha256(expected.encode()).hexdigest()


def test_broken_or_cyclic_continuation_remains_explicitly_incomplete():
    missing = """
    <ix:nonNumeric name="us-gaap:RiskTextBlock" contextRef="C1" id="risk" continuedAt="missing">Alpha</ix:nonNumeric>
    """
    missing_state = parse_textblock_states(missing)["us-gaap:RiskTextBlock"][0]
    assert missing_state["continued_chain_complete"] is False
    assert missing_state["continued_chain_length"] == 1

    cyclic = """
    <ix:nonNumeric name="us-gaap:RiskTextBlock" contextRef="C1" id="risk" continuedAt="c1">Alpha</ix:nonNumeric>
    <ix:continuation id="c1" continuedAt="c2">Beta</ix:continuation>
    <ix:continuation id="c2" continuedAt="c1">Gamma</ix:continuation>
    """
    cycle_state = parse_textblock_states(cyclic)["us-gaap:RiskTextBlock"][0]
    assert cycle_state["continued_chain_complete"] is False
    assert cycle_state["continued_chain_length"] == 2


def test_textblock_parser_excludes_script_and_style_payload_but_keeps_boundaries():
    document = """
    <ix:nonNumeric name="us-gaap:RiskTextBlock" contextRef="C1" id="risk">
      Alpha<script>NONPUBLIC FUTURE TEXT</script><style>.x { value: 9 }</style><b>Beta</b>
    </ix:nonNumeric>
    """
    state = parse_textblock_states(document)["us-gaap:RiskTextBlock"][0]
    assert state["normalized_character_count"] == len("Alpha Beta")
    assert state["content_sha256"] == hashlib.sha256(b"Alpha Beta").hexdigest()


def test_numeric_parser_handles_scale_sign_and_nil_without_qname_substitution():
    document = """
    <ix:nonFraction name="us-gaap:Assets" contextRef="C1" unitRef="USD" scale="3" decimals="-6" sign="-">1,234</ix:nonFraction>
    <ix:nonFraction name="us-gaap:NetIncomeLoss" contextRef="C1" unitRef="USD" xsi:nil="true">ignored</ix:nonFraction>
    <ix:nonFraction name="us-gaap:Revenue" contextRef="C1" unitRef="USD">999</ix:nonFraction>
    """
    facts = parse_structured_states(document)
    assert facts["us-gaap:Assets"][0]["normalized_value"] == "-1234000"
    assert facts["us-gaap:Assets"][0]["parse_status"] == "PARSED"
    assert facts["us-gaap:NetIncomeLoss"][0]["normalized_value"] is None
    assert facts["us-gaap:NetIncomeLoss"][0]["parse_status"] == "NIL"
    assert "us-gaap:Revenue" not in facts
    assert set(facts).issubset(set(NUMERIC_QNAMES))


def test_strict_prefix_uses_acceptance_clock_and_never_orders_ties_by_accession():
    records = [
        _record("0000064040", "0000064040-20-000001", "10-K", "2020-02-01", "2020-02-01T18:00:00Z"),
        _record("0000064040", "0000064040-21-000001", "10-K/A", "2021-02-01", "2021-02-01T18:00:00Z"),
        _record("0000064040", "0000064040-22-000001", "10-K", "2022-02-01", "2022-02-01T18:00:00Z"),
        _record("0000064040", "0000064040-22-000002", "10-K", "2022-02-01", "2022-02-01T18:00:00Z"),
        _record("0000064040", "0000064040-23-000001", "10-K", "2023-02-01", "2023-02-01T18:00:00Z"),
    ]
    summaries = prefix_summaries(records)
    tied_a = "0000064040|0000064040-22-000001|10-K|2022-02-01"
    tied_b = "0000064040|0000064040-22-000002|10-K|2022-02-01"
    latest = "0000064040|0000064040-20-000001|10-K|2020-02-01"
    assert summaries[tied_a]["prior_same_issuer_filing_count"] == 2
    assert summaries[tied_b]["prior_same_issuer_filing_count"] == 2
    assert summaries[tied_a]["prior_same_issuer_original_10k_count"] == 1
    assert summaries[tied_a]["latest_prior_original_10k"] == latest
    assert summaries[tied_b]["latest_prior_original_10k"] == latest

    reversed_summaries = prefix_summaries(list(reversed(records)))
    assert summaries == reversed_summaries
    future = copy.deepcopy(records[0])
    future["canonical_key"]["accession"] = "0000064040-24-000999"
    future["acceptance_datetime"] = "2024-02-01T18:00:00Z"
    with_future = prefix_summaries(records + [future])
    assert all(with_future[key] == value for key, value in summaries.items())


def _make_tiny_inputs():
    contract = {
        "candidate_id": "Q220",
        "fixed_universe": {"ciks": {"SPGI": "0000064040"}},
    }
    contract_bytes = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    documents = {
        "0000064040-20-000001": b"""
            <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
              <ix:nonNumeric name="us-gaap:RiskTextBlock" contextRef="C1" id="risk1">Risk disclosure</ix:nonNumeric>
              <ix:nonFraction name="us-gaap:Assets" contextRef="C1" unitRef="USD" scale="0">100</ix:nonFraction>
            </html>
        """,
        "0000064040-21-000001": b"""
            <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
              <ix:nonNumeric name="us-gaap:RiskTextBlock" contextRef="C2" id="risk2">Updated risk disclosure</ix:nonNumeric>
              <ix:nonFraction name="us-gaap:Assets" contextRef="C2" unitRef="USD" scale="0">125</ix:nonFraction>
            </html>
        """,
    }
    raw_rows = [
        ("0000064040-20-000001", "2020-02-01", "2020-02-01T18:00:00Z"),
        ("0000064040-21-000001", "2021-02-01", "2021-02-01T18:00:00Z"),
    ]
    records = []
    for accession, filed, accepted in raw_rows:
        body = documents[accession]
        records.append({
            "canonical_key": {
                "cik": "0000064040",
                "accession": accession,
                "form": "10-K",
                "filed_date": filed,
            },
            "acceptance_datetime": accepted,
            "primary_document": "filing.htm",
            "primary_document_sha256": sha256(body),
            "textblock_concepts": ["us-gaap:RiskTextBlock"],
            "presentation_mapped_textblock_concepts": ["us-gaap:RiskTextBlock"],
            "presentation_mapping_complete_for_observed_textblocks": True,
        })

    population = {
        "candidate_id": "Q220",
        "mode": "population",
        "status": "Q220_AS_FILED_XBRL_POPULATION_COMPLETED",
        "failure_count": 0,
        "record_count": len(records),
        "records": records,
        "fixed_universe": {"SPGI": "0000064040"},
        "window": {"start": "2019-01-01", "end": "2025-09-24"},
        "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
        "gate_code_sha256": "a" * 64,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    population["receipt_fingerprint"] = canonical_fingerprint(population)

    prefix = prefix_summaries(records)
    parsed_text = {
        record["canonical_key"]["accession"]: parse_textblock_states(documents[record["canonical_key"]["accession"]].decode())
        for record in records
    }
    parsed_numeric = {
        record["canonical_key"]["accession"]: parse_structured_states(documents[record["canonical_key"]["accession"]].decode())
        for record in records
    }
    compiler_events = []
    for record in records:
        key = record["canonical_key"]
        accession = key["accession"]
        row_key = "|".join(str(key[name]) for name in ("cik", "accession", "form", "filed_date"))
        summary = prefix[row_key]
        previous_key = summary["latest_prior_original_10k"]
        previous_accession = previous_key.split("|")[1] if previous_key else None
        if previous_accession is None:
            narrative_changed = structured_changed = None
        else:
            narrative_changed, structured_changed = change_states(
                parsed_text[accession],
                parsed_text[previous_accession],
                parsed_numeric[accession],
                parsed_numeric[previous_accession],
            )
        compiler_events.append({
            "record_key": row_key,
            "cik": key["cik"],
            "accession": accession,
            "form": key["form"],
            "filed_date": key["filed_date"],
            "acceptance_datetime_utc": datetime.fromisoformat(record["acceptance_datetime"].replace("Z", "+00:00")).astimezone(timezone.utc).isoformat(),
            "primary_document": record["primary_document"],
            "primary_document_sha256": record["primary_document_sha256"],
            "source_hash_verified": True,
            **summary,
            "textblock_fact_count": sum(len(rows) for rows in parsed_text[accession].values()),
            "distinct_textblock_qname_count": len(parsed_text[accession]),
            "textblock_content_states": parsed_text[accession],
            "presentation_mapping_complete_in_population_receipt": True,
            "unmapped_textblock_qnames": [],
            "narrative_changed_qnames_vs_latest_prior_original": narrative_changed,
            "narrative_changed_qname_count_vs_latest_prior_original": None if narrative_changed is None else len(narrative_changed),
            "structured_facts_by_qname": parsed_numeric[accession],
            "structured_fact_counts_by_exact_qname": {q: len(parsed_numeric[accession].get(q, [])) for q in NUMERIC_QNAMES},
            "structured_changed_qnames_vs_latest_prior_original": structured_changed,
            "structured_changed_qname_count_vs_latest_prior_original": None if structured_changed is None else len(structured_changed),
            "source_observation_is_not_a_performance_result": True,
        })
    compiler = {
        "schema_version": 1,
        "record_type": "q220_historical_representation_pit_compilation",
        "candidate_id": "Q220",
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
        "source_population_receipt_fingerprint": population["receipt_fingerprint"],
        "source_population_contract_sha256": population["contract_sha256"],
        "source_population_gate_code_sha256": population["gate_code_sha256"],
        "compiler_code_sha256": sha256((__import__("pathlib").Path(__file__).resolve().parents[1] / "automation/q220_historical_representation_pit.py").read_bytes()),
        "fixed_universe": population["fixed_universe"],
        "window": population["window"],
        "exact_numeric_qnames": list(NUMERIC_QNAMES),
        "record_count": len(records),
        "compiled_event_count": len(records),
        "verified_primary_document_count": len(records),
        "source_hash_failure_count": 0,
        "source_hash_failures": [],
        "unmapped_or_reconciled_textblock_gap_count": 0,
        "textblock_mapping_gaps": [],
        "records_with_no_textblock_observed": [],
        "source_complete": True,
        "textblock_mapping_complete": True,
        "historical_prefix_order_valid": True,
        "status": "Q220_HISTORICAL_REPRESENTATION_PIT_COMPILED",
        "gate_positive": True,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "events": compiler_events,
    }
    compiler["receipt_fingerprint"] = canonical_fingerprint(compiler)
    return population, contract, contract_bytes, compiler, documents


def test_independent_reproduction_compares_all_states_and_fails_closed_on_hash_drift():
    population, contract, contract_bytes, compiler, documents = _make_tiny_inputs()
    ok = reproduce(
        population,
        contract,
        compiler,
        contract_bytes=contract_bytes,
        expected_population_fingerprint=population["receipt_fingerprint"],
        expected_record_count=2,
        fetcher=lambda cik, accession, filename: (documents[accession], 200),
    )
    assert ok["gate_positive"] is True
    assert ok["status"] == "Q220_INDEPENDENT_PIT_REPRODUCED"
    assert all(ok["checks"].values())
    assert ok["independently_retrieved_documents"] == 2
    assert ok["scientific_evidence"] is False
    assert ok["performance_authorization"] is False
    assert canonical_fingerprint(ok) == ok["receipt_fingerprint"]

    bad = reproduce(
        population,
        contract,
        compiler,
        contract_bytes=contract_bytes,
        expected_population_fingerprint=population["receipt_fingerprint"],
        expected_record_count=2,
        fetcher=lambda cik, accession, filename: (documents[accession] + b"<!-- changed after freeze -->", 200),
    )
    assert bad["gate_positive"] is False
    assert bad["source_hash_failure_count"] == 2
    assert bad["checks"]["all_primary_sources_independently_retrieved_and_hash_verified"] is False
    assert bad["performance_authorization"] is False


def test_independent_parser_keeps_empty_self_closing_numeric_fact_separate():
    document = """
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
      <ix:nonFraction name="us-gaap:Assets" contextRef="EMPTY" unitRef="USD" />
      <ix:nonFraction name="us-gaap:Assets" contextRef="VALUED" unitRef="USD">100</ix:nonFraction>
    </html>
    """
    facts = parse_structured_states(document)["us-gaap:Assets"]
    by_context = {row["context_ref"]: row for row in facts}

    assert set(by_context) == {"EMPTY", "VALUED"}
    assert by_context["EMPTY"]["normalized_value"] is None
    assert by_context["EMPTY"]["parse_status"] == "UNPARSEABLE_NUMERIC_TEXT"
    assert by_context["EMPTY"]["raw_value_sha256"] == sha256(b"")
    assert by_context["VALUED"]["normalized_value"] == "100"
    assert by_context["VALUED"]["parse_status"] == "PARSED"


def test_independent_and_primary_parsers_agree_on_nested_continuation_chain():
    document = """
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
      <ix:nonNumeric name="custom:RiskTextBlock" contextRef="C1" id="risk" continuedAt="c1">Headline</ix:nonNumeric>
      <ix:continuation id="c1" continuedAt="c3">
        Alpha <span>beta</span>
        <ix:continuation id="c2">Nested continuation text</ix:continuation>
        omega
      </ix:continuation>
      <ix:continuation id="c3">Tail text</ix:continuation>
    </html>
    """
    primary = primary_textblock_states(document)
    independent = parse_textblock_states(document)

    assert primary == independent
    state = independent["custom:RiskTextBlock"][0]
    expected = "Headline Alpha beta Nested continuation text omega Tail text"
    assert state["continued_chain_length"] == 2
    assert state["continued_chain_complete"] is True
    assert state["normalized_character_count"] == len(expected)
    assert state["content_sha256"] == sha256(expected.encode("utf-8"))
