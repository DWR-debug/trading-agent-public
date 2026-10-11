import hashlib
import json
from pathlib import Path

from automation.q220_historical_representation_pit import (
    canonical_fingerprint,
    compile_receipt,
    sha256,
    structured_states,
    textblock_states,
)


def _fixture(tmp_path: Path):
    contract = {
        "concept_spec": {
            "structured_side": {
                "exact_numeric_qnames": [
                    "us-gaap:Assets",
                    "us-gaap:OperatingIncomeLoss",
                    "us-gaap:NetIncomeLoss",
                    "us-gaap:NetCashProvidedByUsedInOperatingActivities",
                    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
                ]
            }
        }
    }
    contract_path = tmp_path / "research/preregistrations/q220_as_filed_xbrl_population_contract_2026_10_06.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    docs = {
        "0000064040-20-000001": b'''<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
          <ix:nonNumeric name="c:RiskTextBlock" contextRef="C1" id="tb1"><p>Risks have changed.</p></ix:nonNumeric>
          <ix:nonFraction name="us-gaap:Assets" contextRef="C1" unitRef="USD" scale="3" decimals="-6">1,234</ix:nonFraction>
        </html>''',
        "0000064040-21-000001": b'''<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
          <ix:nonNumeric name="c:RiskTextBlock" contextRef="C2" id="tb2"><p>Risks have materially changed.</p></ix:nonNumeric>
          <ix:nonFraction name="us-gaap:Assets" contextRef="C2" unitRef="USD" scale="3" decimals="-6">1,500</ix:nonFraction>
        </html>''',
    }
    rows = []
    for accession, filed, accepted in [
        ("0000064040-20-000001", "2020-02-12", "2020-02-12T18:00:00Z"),
        ("0000064040-21-000001", "2021-02-12", "2021-02-12T18:00:00Z"),
    ]:
        body = docs[accession]
        rows.append({
            "canonical_key": {"cik": "0000064040", "accession": accession, "form": "10-K", "filed_date": filed},
            "acceptance_datetime": accepted,
            "primary_document": "filing.htm",
            "primary_document_sha256": sha256(body),
            "textblock_concepts": ["c:RiskTextBlock"],
            "presentation_mapped_textblock_concepts": ["c:RiskTextBlock"],
            "presentation_mapping_complete_for_observed_textblocks": True,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        })
    population = {
        "candidate_id": "Q220",
        "mode": "population",
        "status": "Q220_AS_FILED_XBRL_POPULATION_COMPLETED",
        "failure_count": 0,
        "record_count": len(rows),
        "row_count": len(rows),
        "records": rows,
        "fixed_universe": {"SPGI": "0000064040"},
        "window": {"start": "2019-01-01", "end": "2025-09-24"},
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "gate_code_sha256": "a" * 64,
        "governance": {},
        "source_route": {},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    population["receipt_fingerprint"] = canonical_fingerprint(population)
    return population, contract, docs, tmp_path


def _compile(population, contract, root, **kwargs):
    kwargs.setdefault("expected_population_fingerprint", str(population.get("receipt_fingerprint") or ""))
    kwargs.setdefault("expected_record_count", 2)
    return compile_receipt(population, contract, root=root, **kwargs)


def test_q220_compile_builds_strict_prefix_and_exact_fact_state(tmp_path):
    population, contract, docs, root = _fixture(tmp_path)

    def fetcher(cik, accession, filename):
        return docs[accession], 200

    result = _compile(population, contract, root=root, fetcher=fetcher, sleep_seconds=0)
    assert result["record_count"] == 2
    assert result["compiled_event_count"] == 2
    assert result["source_complete"] is True
    assert result["gate_positive"] is True
    assert result["historical_prefix_order_valid"] is True
    first, second = result["events"]
    assert first["prior_same_issuer_filing_count"] == 0
    assert second["prior_same_issuer_filing_count"] == 1
    assert second["latest_prior_original_10k"].endswith("0000064040-20-000001|10-K|2020-02-12")
    assert second["narrative_changed_qname_count_vs_latest_prior_original"] == 1
    assert second["structured_changed_qname_count_vs_latest_prior_original"] == 1
    assert second["structured_facts_by_qname"]["us-gaap:Assets"][0]["normalized_value"] == "1500000"
    assert result["events"][0]["acceptance_datetime_utc"].endswith("+00:00")
    assert result["performance_authorization"] is False
    assert result["live_execution"] is False


def test_q220_refuses_population_outside_frozen_version_pin(tmp_path):
    population, contract, docs, root = _fixture(tmp_path)
    try:
        compile_receipt(
            population,
            contract,
            root=root,
            fetcher=lambda *args: (_ for _ in ()).throw(AssertionError("must fail before source fetch")),
            expected_population_fingerprint="0" * 64,
            expected_record_count=2,
        )
    except ValueError as exc:
        assert "Q220_POPULATION_RECEIPT_VERSION_MISMATCH" in str(exc)
    else:
        raise AssertionError("a self-consistent but unpinned population must fail closed")


def test_q220_refuses_changed_primary_document_hash(tmp_path):
    population, contract, docs, root = _fixture(tmp_path)
    mutated = dict(docs)
    mutated["0000064040-20-000001"] = docs["0000064040-20-000001"] + b"<!-- mutation -->"

    result = _compile(
        population, contract, root=root,
        fetcher=lambda cik, accession, filename: (mutated[accession], 200),
        sleep_seconds=0,
    )
    assert result["source_hash_failure_count"] == 1
    assert result["gate_positive"] is False
    assert result["status"] == "Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED"
    assert result["historical_prefix_order_valid"] is False


def test_q220_refuses_population_receipt_fingerprint_mutation(tmp_path):
    population, contract, docs, root = _fixture(tmp_path)
    population["records"][0]["canonical_key"]["cik"] = "0000000001"
    try:
        _compile(population, contract, root, fetcher=lambda *args: (b"", 200), sleep_seconds=0)
    except ValueError as exc:
        assert "FINGERPRINT_MISMATCH" in str(exc)
    else:
        raise AssertionError("mutated population receipt must fail closed")


def test_q220_same_acceptance_timestamp_never_enters_strict_prefix(tmp_path):
    population, contract, docs, root = _fixture(tmp_path)
    population["records"][1]["acceptance_datetime"] = population["records"][0]["acceptance_datetime"]
    population["receipt_fingerprint"] = canonical_fingerprint(population)
    result = _compile(population, contract, root=root, fetcher=lambda cik, accession, filename: (docs[accession], 200), sleep_seconds=0)
    assert all(event["prior_same_issuer_filing_count"] == 0 for event in result["events"])
    assert result["historical_prefix_order_valid"] is True


def test_q220_receipt_fingerprint_is_self_consistent(tmp_path):
    population, contract, docs, root = _fixture(tmp_path)
    result = _compile(population, contract, root=root, fetcher=lambda cik, accession, filename: (docs[accession], 200), sleep_seconds=0)
    assert canonical_fingerprint(result) == result["receipt_fingerprint"]


def test_q220_textblock_parser_preserves_facts_after_self_closing_fact():
    document = """
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
      <ix:nonNumeric name="us-gaap:EmptyTextBlock" contextRef="C0" id="empty"/>
      <ix:nonNumeric name="us-gaap:RiskTextBlock" contextRef="C1" id="risk"><p>Risk disclosure</p></ix:nonNumeric>
      <ix:nonNumeric name="us-gaap:SecondEmptyTextBlock" contextRef="C2" id="empty2" />
      <ix:nonNumeric name="us-gaap:OtherTextBlock" contextRef="C3" id="other">Other disclosure</ix:nonNumeric>
    </html>
    """
    states = textblock_states(document)
    assert set(states) == {
        "us-gaap:EmptyTextBlock",
        "us-gaap:RiskTextBlock",
        "us-gaap:SecondEmptyTextBlock",
        "us-gaap:OtherTextBlock",
    }
    assert states["us-gaap:EmptyTextBlock"][0]["normalized_character_count"] == 0
    assert states["us-gaap:RiskTextBlock"][0]["normalized_character_count"] == len("Risk disclosure")
    assert states["us-gaap:SecondEmptyTextBlock"][0]["normalized_character_count"] == 0
    assert states["us-gaap:OtherTextBlock"][0]["normalized_character_count"] == len("Other disclosure")

def test_q220_default_population_pin_matches_verified_master_receipt():
    from automation.q220_historical_representation_pit import EXPECTED_POPULATION_RECEIPT_FINGERPRINT

    assert EXPECTED_POPULATION_RECEIPT_FINGERPRINT == "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"


def test_q220_nested_textblocks_preserve_outer_and_inner_content():
    document = """
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
      <ix:nonNumeric name="custom:RiskFactorsTextBlock" contextRef="C0" id="outer">
        Outer before
        <ix:nonNumeric name="custom:NestedRiskTextBlock" contextRef="C1" id="inner">Inner disclosure</ix:nonNumeric>
        outer after
      </ix:nonNumeric>
    </html>
    """
    states = textblock_states(document)

    assert states["custom:RiskFactorsTextBlock"][0]["normalized_character_count"] == len(
        "Outer before Inner disclosure outer after"
    )
    assert states["custom:NestedRiskTextBlock"][0]["normalized_character_count"] == len(
        "Inner disclosure"
    )
    assert states["custom:RiskFactorsTextBlock"][0]["content_sha256"] == sha256(
        b"Outer before Inner disclosure outer after"
    )


def test_q220_self_closing_numeric_fact_does_not_swallow_following_fact():
    document = """
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
      <ix:nonFraction name="us-gaap:Assets" contextRef="EMPTY" unitRef="USD" />
      <ix:nonFraction name="us-gaap:Assets" contextRef="VALUED" unitRef="USD">100</ix:nonFraction>
    </html>
    """
    states = structured_states(document)["us-gaap:Assets"]
    by_context = {row["context_ref"]: row for row in states}

    assert set(by_context) == {"EMPTY", "VALUED"}
    assert by_context["EMPTY"]["normalized_value"] is None
    assert by_context["EMPTY"]["parse_status"] == "UNPARSEABLE_NUMERIC_TEXT"
    assert by_context["EMPTY"]["raw_value_sha256"] == sha256(b"")
    assert by_context["VALUED"]["normalized_value"] == "100"
    assert by_context["VALUED"]["parse_status"] == "PARSED"
