"""Compile the frozen Q220 as-filed population into acceptance-time representation states.

This gate verifies immutable source hashes, builds strict historical prefixes, and
records coverage gaps. It never reads outcomes or authorizes performance.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "research/evidence/q220_as_filed_xbrl_population_latest.json"
CONTRACT = ROOT / "research/preregistrations/q220_as_filed_xbrl_population_contract_2026_10_06.json"
OUTPUT_DEFAULT = ROOT / "research/evidence/q220_historical_representation_pit_latest.json"
EXPECTED_POPULATION_RECEIPT_FINGERPRINT = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
EXPECTED_POPULATION_RECORD_COUNT = 55
SEC_ROOT = "https://www.sec.gov/Archives/edgar/data"
UA = "DWR-debug/trading-agent-public Q220 historical representation PIT/1.0 research@example.invalid"
NUMERIC_QNAMES = (
    "us-gaap:Assets",
    "us-gaap:OperatingIncomeLoss",
    "us-gaap:NetIncomeLoss",
    "us-gaap:NetCashProvidedByUsedInOperatingActivities",
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
)
MAX_PRIMARY_BYTES = 35_000_000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field, None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return sha256(raw)


def normalized_text(fragment: str) -> str:
    fragment = re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>", " ", fragment)
    fragment = re.sub(r"(?s)<[^>]*>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


def attributes(raw: str) -> dict[str, str]:
    return {
        key.lower(): html.unescape(value).strip()
        for key, value in re.findall(r"""([A-Za-z_:][\w:.-]*)\s*=\s*["']([^"']*)["']""", raw, re.I | re.S)
    }


def continuation_map(document: str) -> dict[str, tuple[dict[str, str], str]]:
    found: dict[str, tuple[dict[str, str], str]] = {}
    for match in re.finditer(r"(?is)<ix:continuation\b([^>]*)>(.*?)</ix:continuation\s*>", document):
        attrs = attributes(match.group(1))
        identifier = attrs.get("id")
        if identifier:
            found[identifier] = (attrs, match.group(2))
    return found


def matching_element_content(document: str, start: int, local_tag_name: str) -> str | None:
    """Return an element's inner HTML while respecting nested elements of the same QName.

    SEC TextBlock facts may legally wrap other TextBlock facts, and a raw first-close
    regex truncates the outer fact at the nested fact's closing tag. This scanner is
    still deliberately lexical, but skips comments/script/style payloads and balances
    real ix:<tag> start/end tags. Self-closing facts do not change nesting depth.
    """
    tag = re.escape(local_tag_name)
    token_pattern = re.compile(
        rf"(?is)<!--.*?-->|<script\b[^>]*>.*?</script\s*>|<style\b[^>]*>.*?</style\s*>|</?ix:{tag}\b[^>]*>"
    )
    depth = 1
    for token_match in token_pattern.finditer(document, start):
        token = token_match.group(0)
        lowered = token.lower()
        if lowered.startswith("<!--") or re.match(r"<(?:script|style)\b", lowered):
            continue
        if lowered.startswith("</"):
            depth -= 1
            if depth == 0:
                return document[start:token_match.start()]
        elif not token.rstrip().endswith("/>"):
            depth += 1
    return None


def textblock_states(document: str) -> dict[str, list[dict[str, Any]]]:
    continuations = continuation_map(document)
    states: dict[str, list[dict[str, Any]]] = {}
    # Iterate opening tags independently of their content. SEC Inline XBRL filings
    # include self-closing ix:nonNumeric TextBlock facts; they remain explicit empty
    # states. Balanced matching also preserves outer TextBlocks that wrap inner ones.
    for match in re.finditer(r"(?is)<ix:nonNumeric\b([^>]*)>", document):
        attrs = attributes(match.group(1))
        qname = attrs.get("name", "")
        if not qname or not qname.rsplit(":", 1)[-1].lower().endswith("textblock"):
            continue
        context_ref = attrs.get("contextref")
        opening_is_self_closing = match.group(0).rstrip().endswith("/>")
        if opening_is_self_closing:
            fragment = ""
        else:
            fragment = matching_element_content(document, match.end(), "nonNumeric")
            # A missing closure is not converted into an empty fact. It remains visible
            # as a QName reconciliation gap against the immutable population receipt.
            if fragment is None:
                continue
        chain_ids: list[str] = []
        next_id = attrs.get("continuedat")
        visited: set[str] = set()
        chain_complete = True
        while next_id:
            if next_id in visited or len(chain_ids) >= 30:
                chain_complete = False
                break
            visited.add(next_id)
            chain_ids.append(next_id)
            item = continuations.get(next_id)
            if item is None:
                chain_complete = False
                break
            cont_attrs, cont_fragment = item
            fragment += " " + cont_fragment
            next_id = cont_attrs.get("continuedat")
        text = normalized_text(fragment)
        state = {
            "context_ref": context_ref,
            "fact_id": attrs.get("id"),
            "continued_chain_length": len(chain_ids),
            "continued_chain_complete": chain_complete,
            "normalized_character_count": len(text),
            "content_sha256": sha256(text.encode("utf-8")) if text else None,
        }
        states.setdefault(qname, []).append(state)
    for qname in states:
        states[qname].sort(key=lambda x: (str(x.get("context_ref") or ""), str(x.get("fact_id") or ""), str(x.get("content_sha256") or "")))
    return states


def parse_numeric(raw: str, attrs: dict[str, str]) -> tuple[str | None, str]:
    text = normalized_text(raw).replace("\u2212", "-")
    if attrs.get("xsi:nil", "").lower() == "true" or attrs.get("nil", "").lower() == "true":
        return None, "NIL"
    negative_parentheses = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace(",", "")
    text = re.sub(r"[^0-9.+\-]", "", text)
    if not text or text in {".", "+", "-", "+.", "-."}:
        return None, "UNPARSEABLE_NUMERIC_TEXT"
    try:
        value = Decimal(text)
        if negative_parentheses:
            value = -abs(value)
        if attrs.get("sign") == "-":
            value = -abs(value)
        scale = int(attrs.get("scale", "0") or "0")
        if abs(scale) > 18:
            return None, "SCALE_OUT_OF_BOUND"
        value *= Decimal(10) ** scale
    except (InvalidOperation, ValueError, OverflowError):
        return None, "UNPARSEABLE_NUMERIC_TEXT"
    return format(value.normalize(), "f"), "PARSED"


def structured_states(document: str) -> dict[str, list[dict[str, Any]]]:
    states: dict[str, list[dict[str, Any]]] = {}
    wanted = set(NUMERIC_QNAMES)
    # Handle self-closing facts as explicit empty/unparseable states instead of
    # allowing a first-close regex to consume the following numeric fact.
    for match in re.finditer(r"(?is)<ix:nonFraction\b([^>]*)>", document):
        attrs = attributes(match.group(1))
        qname = attrs.get("name", "")
        if qname not in wanted:
            continue
        opening_is_self_closing = match.group(0).rstrip().endswith("/>")
        if opening_is_self_closing:
            raw = ""
        else:
            raw = matching_element_content(document, match.end(), "nonFraction")
            if raw is None:
                continue
        visible = normalized_text(raw)
        value, parse_status = parse_numeric(raw, attrs)
        states.setdefault(qname, []).append({
            "context_ref": attrs.get("contextref"),
            "unit_ref": attrs.get("unitref"),
            "decimals": attrs.get("decimals"),
            "scale": attrs.get("scale", "0"),
            "sign": attrs.get("sign", "+"),
            "nil": attrs.get("xsi:nil", attrs.get("nil", "false")).lower() == "true",
            "normalized_value": value,
            "parse_status": parse_status,
            "raw_value_sha256": sha256(visible.encode("utf-8")),
        })
    for qname in states:
        states[qname].sort(key=lambda x: (str(x.get("context_ref") or ""), str(x.get("unit_ref") or ""), str(x.get("normalized_value") or ""), str(x.get("raw_value_sha256") or "")))
    return states


def fetch_primary(cik: str, accession: str, filename: str) -> tuple[bytes, int]:
    accession_compact = accession.replace("-", "")
    url = f"{SEC_ROOT}/{int(cik)}/{accession_compact}/{quote(filename, safe='-._')}"
    last = "unknown"
    for attempt in range(4):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*", "Accept-Encoding": "identity"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read(MAX_PRIMARY_BYTES + 1)
                if len(body) > MAX_PRIMARY_BYTES:
                    raise ValueError("PRIMARY_DOCUMENT_EXCEEDS_BYTE_LIMIT")
                return body, int(getattr(response, "status", 200))
        except urllib.error.HTTPError as exc:
            last = f"HTTP_{exc.code}"
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 3:
                raise RuntimeError(f"SEC_PRIMARY_FETCH_{last}:{accession}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = type(exc).__name__
            if attempt == 3:
                raise RuntimeError(f"SEC_PRIMARY_FETCH_FAILED:{accession}:{last}") from exc
        time.sleep(min(8.0, 1.5 * (2 ** attempt)))
    raise RuntimeError(f"SEC_PRIMARY_FETCH_FAILED:{accession}:{last}")


def record_key(record: dict[str, Any]) -> str:
    key = record["canonical_key"]
    return "|".join(str(key[x]) for x in ("cik", "accession", "form", "filed_date"))


def compile_receipt(
    population: dict[str, Any],
    contract: dict[str, Any],
    root: Path = ROOT,
    fetcher=fetch_primary,
    sleep_seconds: float = 0.22,
    expected_population_fingerprint: str = EXPECTED_POPULATION_RECEIPT_FINGERPRINT,
    expected_record_count: int = EXPECTED_POPULATION_RECORD_COUNT,
) -> dict[str, Any]:
    if population.get("candidate_id") != "Q220" or population.get("mode") != "population":
        raise ValueError("Q220_POPULATION_RECEIPT_IDENTITY_MISMATCH")
    if population.get("status") != "Q220_AS_FILED_XBRL_POPULATION_COMPLETED":
        raise ValueError("Q220_POPULATION_RECEIPT_NOT_POSITIVE")
    if int(population.get("failure_count", -1)) != 0:
        raise ValueError("Q220_POPULATION_RECEIPT_HAS_FAILURES")
    stored_fp = str(population.get("receipt_fingerprint") or "")
    if stored_fp != expected_population_fingerprint:
        raise ValueError("Q220_POPULATION_RECEIPT_VERSION_MISMATCH")
    if len(stored_fp) != 64 or canonical_fingerprint(population) != stored_fp:
        raise ValueError("Q220_POPULATION_RECEIPT_FINGERPRINT_MISMATCH")
    contract_bytes = (root / "research/preregistrations/q220_as_filed_xbrl_population_contract_2026_10_06.json").read_bytes()
    if population.get("contract_sha256") != sha256(contract_bytes):
        raise ValueError("Q220_CONTRACT_FINGERPRINT_MISMATCH")
    records = population.get("records")
    if int(population.get("record_count", -1)) != expected_record_count:
        raise ValueError("Q220_FROZEN_POPULATION_RECORD_COUNT_MISMATCH")
    if not isinstance(records, list) or len(records) != expected_record_count:
        raise ValueError("Q220_POPULATION_RECORD_COUNT_MISMATCH")
    qspec = contract.get("concept_spec", population.get("concept_spec", {}))
    numeric_qnames = tuple(qspec.get("structured_side", {}).get("exact_numeric_qnames", NUMERIC_QNAMES))
    if tuple(numeric_qnames) != NUMERIC_QNAMES:
        raise ValueError("Q220_NUMERIC_CONCEPT_SET_MISMATCH")

    ordered: list[tuple[datetime, dict[str, Any]]] = []
    seen_keys: set[str] = set()
    for record in records:
        key = record_key(record)
        if key in seen_keys:
            raise ValueError(f"Q220_DUPLICATE_POPULATION_RECORD:{key}")
        seen_keys.add(key)
        accepted_raw = str(record.get("acceptance_datetime") or "")
        accepted = datetime.fromisoformat(accepted_raw.replace("Z", "+00:00"))
        if accepted.tzinfo is None:
            raise ValueError(f"Q220_ACCEPTANCE_TIME_HAS_NO_ZONE:{key}")
        ordered.append((accepted.astimezone(timezone.utc), record))
    ordered.sort(key=lambda x: (x[0], record_key(x[1])))

    events: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    verified_source_count = 0
    mapping_gap_rows: list[dict[str, Any]] = []
    no_textblock_rows: list[dict[str, Any]] = []
    prior_records: list[dict[str, Any]] = []
    for accepted, record in ordered:
        key = record["canonical_key"]
        accession = str(key["accession"])
        cik = str(key["cik"]).zfill(10)
        primary = str(record.get("primary_document") or "")
        event_key = record_key(record)
        if not primary or "/" in primary or "\\" in primary or primary in {".", ".."}:
            errors.append({"record_key": event_key, "error": "INVALID_PRIMARY_DOCUMENT_NAME"})
            continue
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
        try:
            body, http_status = fetcher(cik, accession, primary)
            actual_sha = sha256(body)
            expected_sha = str(record.get("primary_document_sha256") or "")
            if http_status != 200 or actual_sha != expected_sha:
                raise ValueError(f"PRIMARY_HASH_MISMATCH:status={http_status}:expected={expected_sha}:actual={actual_sha}")
            decoded = body.decode("utf-8", errors="replace")
            textblocks = textblock_states(decoded)
            structured = structured_states(decoded)
            verified_source_count += 1
        except Exception as exc:
            errors.append({"record_key": event_key, "error": str(exc)[:500]})
            continue

        receipt_textblocks = set(str(x) for x in record.get("textblock_concepts", []))
        extracted_textblocks = set(textblocks)
        if receipt_textblocks != extracted_textblocks:
            mapping_gap_rows.append({
                "record_key": event_key,
                "kind": "TEXTBLOCK_QNAME_RECONCILIATION_MISMATCH",
                "receipt_qnames": sorted(receipt_textblocks),
                "reparsed_qnames": sorted(extracted_textblocks),
            })
        mapped = set(str(x) for x in record.get("presentation_mapped_textblock_concepts", []))
        unmapped = sorted(extracted_textblocks - mapped)
        if unmapped:
            mapping_gap_rows.append({"record_key": event_key, "kind": "UNMAPPED_TEXTBLOCK_CONCEPTS", "qnames": unmapped})
        if not extracted_textblocks:
            no_textblock_rows.append({"record_key": event_key, "form": key.get("form"), "filed_date": key.get("filed_date")})

        eligible_prior = [
            prior for prior in prior_records
            if str(prior["canonical_key"]["cik"]).zfill(10) == cik and prior["_accepted_datetime"] < accepted
        ]
        prior_originals = [p for p in eligible_prior if p["canonical_key"].get("form") == "10-K"]
        previous = max(prior_originals, key=lambda p: (p["_accepted_datetime"], record_key(p))) if prior_originals else None
        prior_textblocks = previous.get("_compiled_textblocks", {}) if previous else {}
        prior_structured = previous.get("_compiled_structured", {}) if previous else {}
        current_text_hashes = {q: [x["content_sha256"] for x in rows] for q, rows in textblocks.items()}
        previous_text_hashes = {
            q: [x["content_sha256"] for x in rows] for q, rows in prior_textblocks.items()
        }
        all_text_qnames = set(current_text_hashes) | set(previous_text_hashes)
        narrative_changed = sorted(q for q in all_text_qnames if current_text_hashes.get(q, []) != previous_text_hashes.get(q, []))
        current_structured_values = {
            q: [(x["context_ref"], x["unit_ref"], x["normalized_value"], x["parse_status"], x["raw_value_sha256"]) for x in rows]
            for q, rows in structured.items()
        }
        previous_structured_values = {
            q: [(x["context_ref"], x["unit_ref"], x["normalized_value"], x["parse_status"], x["raw_value_sha256"]) for x in rows]
            for q, rows in prior_structured.items()
        }
        all_structured_qnames = set(current_structured_values) | set(previous_structured_values)
        structured_changed = sorted(q for q in all_structured_qnames if current_structured_values.get(q, []) != previous_structured_values.get(q, []))
        event = {
            "record_key": event_key,
            "cik": cik,
            "accession": accession,
            "form": str(key.get("form")),
            "filed_date": str(key.get("filed_date")),
            "acceptance_datetime_utc": accepted.isoformat(),
            "event_boundary": "SEC acceptance datetime from the source population receipt; no intra-timestamp ordering is inferred",
            "primary_document": primary,
            "primary_document_sha256": actual_sha,
            "source_hash_verified": True,
            "prior_same_issuer_filing_count": len(eligible_prior),
            "prior_same_issuer_original_10k_count": len(prior_originals),
            "latest_prior_original_10k": record_key(previous) if previous else None,
            "textblock_fact_count": sum(len(v) for v in textblocks.values()),
            "distinct_textblock_qname_count": len(textblocks),
            "textblock_content_states": textblocks,
            "presentation_mapping_complete_in_population_receipt": bool(record.get("presentation_mapping_complete_for_observed_textblocks")),
            "unmapped_textblock_qnames": unmapped,
            "narrative_changed_qnames_vs_latest_prior_original": narrative_changed if previous else None,
            "narrative_changed_qname_count_vs_latest_prior_original": len(narrative_changed) if previous else None,
            "structured_facts_by_qname": structured,
            "structured_fact_counts_by_exact_qname": {q: len(structured.get(q, [])) for q in NUMERIC_QNAMES},
            "structured_changed_qnames_vs_latest_prior_original": structured_changed if previous else None,
            "structured_changed_qname_count_vs_latest_prior_original": len(structured_changed) if previous else None,
            "source_observation_is_not_a_performance_result": True,
        }
        events.append(event)
        record_copy = dict(record)
        record_copy["_accepted_datetime"] = accepted
        record_copy["_compiled_textblocks"] = textblocks
        record_copy["_compiled_structured"] = structured
        prior_records.append(record_copy)

    record_count = len(records)
    source_complete = verified_source_count == record_count and not errors
    textblock_mapping_complete = not any(
        row.get("kind") in {"UNMAPPED_TEXTBLOCK_CONCEPTS", "TEXTBLOCK_QNAME_RECONCILIATION_MISMATCH"}
        for row in mapping_gap_rows
    )
    # Independently reconcile each emitted prefix against the complete compiled
    # event sequence. Equal acceptance timestamps are never ordered by accession.
    strict_prefix_valid = source_complete and len(events) == record_count
    if strict_prefix_valid:
        for event in events:
            current_ts = datetime.fromisoformat(event["acceptance_datetime_utc"])
            eligible = [
                candidate for candidate in events
                if candidate["cik"] == event["cik"]
                and datetime.fromisoformat(candidate["acceptance_datetime_utc"]) < current_ts
            ]
            prior_originals = [candidate for candidate in eligible if candidate["form"] == "10-K"]
            latest = max(
                prior_originals,
                key=lambda candidate: (
                    datetime.fromisoformat(candidate["acceptance_datetime_utc"]),
                    candidate["record_key"],
                ),
            ) if prior_originals else None
            if (
                event["prior_same_issuer_filing_count"] != len(eligible)
                or event["prior_same_issuer_original_10k_count"] != len(prior_originals)
                or event["latest_prior_original_10k"] != (latest["record_key"] if latest else None)
            ):
                strict_prefix_valid = False
                break
            if latest and datetime.fromisoformat(latest["acceptance_datetime_utc"]) >= current_ts:
                strict_prefix_valid = False
                break
    positive = source_complete and textblock_mapping_complete and strict_prefix_valid and len(events) == record_count
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q220_historical_representation_pit_compilation",
        "candidate_id": "Q220",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_population_receipt_fingerprint": stored_fp,
        "source_population_contract_sha256": population.get("contract_sha256"),
        "source_population_gate_code_sha256": population.get("gate_code_sha256"),
        "compiler_code_sha256": sha256(Path(__file__).read_bytes()),
        "fixed_universe": population.get("fixed_universe"),
        "window": population.get("window"),
        "exact_numeric_qnames": list(NUMERIC_QNAMES),
        "record_count": record_count,
        "compiled_event_count": len(events),
        "verified_primary_document_count": verified_source_count,
        "source_hash_failure_count": len(errors),
        "source_hash_failures": errors,
        "unmapped_or_reconciled_textblock_gap_count": len(mapping_gap_rows),
        "textblock_mapping_gaps": mapping_gap_rows,
        "records_with_no_textblock_observed": no_textblock_rows,
        "strict_prefix_rule": "Only source records with acceptance_datetime strictly earlier than the current event enter its historical prefix; simultaneous timestamps are never ordered by accession.",
        "amendment_rule": "10-K/A records remain observations but never replace the latest prior original 10-K baseline.",
        "textblock_content_rule": "Visible TextBlock contents are normalized and SHA-256 fingerprinted; raw filing text is not copied into the receipt.",
        "structured_fact_rule": "Only the five exact frozen us-gaap QNames are extracted; no fallback or concept substitution is permitted.",
        "source_complete": source_complete,
        "textblock_mapping_complete": textblock_mapping_complete,
        "historical_prefix_order_valid": strict_prefix_valid,
        "status": "Q220_HISTORICAL_REPRESENTATION_PIT_COMPILED" if positive else "Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED",
        "gate_positive": positive,
        "next_gate": "independent PIT reproduction on an independent retrieval/parse path" if positive else "repair source hash mismatches or reconcile TextBlock/presentation mapping gaps before independent reproduction",
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
        "events": events,
    }
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--population", type=Path, default=POPULATION)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--no-network", action="store_true", help="Reserved for tests; compile_receipt is called with an injected fetcher.")
    args = parser.parse_args()
    if args.no_network:
        parser.error("--no-network is only available through the Python API with an injected fetcher")
    population = json.loads(args.population.read_text(encoding="utf-8"))
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    receipt = compile_receipt(population, contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "events"}, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["gate_positive"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
