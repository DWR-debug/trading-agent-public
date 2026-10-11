"""Bounded differential diagnostic for Q220's verified TextBlock parser mismatch.

This is not a PIT/performance gate. It re-fetches only three already-failing,
frozen SEC primary documents and contrasts the canonical compiler parser with
the independent tree parser. The receipt includes bounded visible-text snippets,
first-difference positions and field-level state differences so repairs can target
a proven cause rather than widening the acceptance criteria.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation import q220_historical_representation_pit as primary
from automation import q220_independent_pit_reproduction as independent

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "research/evidence/q220_as_filed_xbrl_population_latest.json"
COMPILER = ROOT / "research/evidence/q220_historical_representation_pit_latest.json"
FAILED_REPRODUCTION = ROOT / "research/evidence/q220_independent_pit_reproduction_latest.json"
OUTPUT_DEFAULT = ROOT / "research/evidence/q220_textblock_mismatch_diagnostic_latest.json"

EXPECTED_POPULATION_FP = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
EXPECTED_COMPILER_FP = "2706261882cb334e5c9f1e2f2cd89ff9922366775bec736c88d80b9d63675806"
EXPECTED_FAILED_REPRODUCTION_FP = "a4670b39165457446fe96471cd9b94e708c3a13024b56266f30b09c98d04adeb"
TARGET_SAMPLE_SIZE = 3
MAX_MISMATCH_QNAMES_PER_RECORD = 35
MAX_FACT_DETAILS_PER_QNAME = 3
MAX_PREVIEW_CHARS = 180


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fingerprint(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("receipt_fingerprint", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded)


def record_key(record: dict[str, Any]) -> str:
    key = record["canonical_key"]
    return "|".join(str(key[name]) for name in ("cik", "accession", "form", "filed_date"))


def primary_texts(document: str) -> dict[str, dict[tuple[str | None, str | None], list[str]]]:
    """Return the exact normalized text used by the production TextBlock parser."""
    continuations = primary.continuation_map(document)
    output: dict[str, dict[tuple[str | None, str | None], list[str]]] = {}
    for match in re.finditer(r"(?is)<ix:nonNumeric\b([^>]*)>", document):
        attrs = primary.attributes(match.group(1))
        qname = attrs.get("name", "")
        if not qname or not qname.rsplit(":", 1)[-1].lower().endswith("textblock"):
            continue
        if match.group(0).rstrip().endswith("/>"):
            fragment = ""
        else:
            fragment = primary.matching_element_content(document, match.end(), "nonNumeric")
            if fragment is None:
                continue
        next_id = attrs.get("continuedat")
        visited: set[str] = set()
        chain_steps = 0
        while next_id:
            if next_id in visited or chain_steps >= 30:
                break
            visited.add(next_id)
            chain_steps += 1
            item = continuations.get(next_id)
            if item is None:
                break
            continuation_attrs, continuation_fragment = item
            fragment += " " + continuation_fragment
            next_id = continuation_attrs.get("continuedat")
        text = primary.normalized_text(fragment)
        identity = (attrs.get("contextref"), attrs.get("id"))
        output.setdefault(qname, {}).setdefault(identity, []).append(text)
    return output


def independent_texts(document: str) -> dict[str, dict[tuple[str | None, str | None], list[str]]]:
    """Return independently rendered visible text from the HTMLParser element tree."""
    root = independent.parse_tree(document)
    nodes = list(independent.walk_nodes(root))
    continuations = {
        node.attrs["id"]: node
        for node in nodes
        if independent.local_tag(node) == "continuation" and node.attrs.get("id")
    }
    output: dict[str, dict[tuple[str | None, str | None], list[str]]] = {}
    for node in nodes:
        attrs = node.attrs
        qname = attrs.get("name", "")
        if independent.local_tag(node) != "nonnumeric" or not qname.rsplit(":", 1)[-1].lower().endswith("textblock"):
            continue
        fragments = [independent.visible_text(node)]
        next_id = attrs.get("continuedat")
        visited: set[str] = set()
        chain_steps = 0
        while next_id:
            if next_id in visited or chain_steps >= 30:
                break
            visited.add(next_id)
            chain_steps += 1
            continuation = continuations.get(next_id)
            if continuation is None:
                break
            fragments.append(independent.visible_text(continuation))
            next_id = continuation.attrs.get("continuedat")
        text = independent.normalized_scalar(" ".join(fragments))
        identity = (attrs.get("contextref"), attrs.get("id"))
        output.setdefault(qname, {}).setdefault(identity, []).append(text)
    return output


def first_difference(left: str, right: str) -> dict[str, Any] | None:
    if left == right:
        return None
    limit = min(len(left), len(right))
    index = 0
    while index < limit and left[index] == right[index]:
        index += 1
    start = max(0, index - 70)
    left_end = min(len(left), index + 110)
    right_end = min(len(right), index + 110)
    return {
        "index": index,
        "left_codepoint": None if index >= len(left) else f"U+{ord(left[index]):04X}",
        "right_codepoint": None if index >= len(right) else f"U+{ord(right[index]):04X}",
        "primary_context": left[start:left_end],
        "independent_context": right[start:right_end],
        "primary_context_repr": repr(left[start:left_end]),
        "independent_context_repr": repr(right[start:right_end]),
    }


def _states_by_identity(states: dict[str, list[dict[str, Any]]]) -> dict[str, dict[tuple[str | None, str | None], list[dict[str, Any]]]]:
    out: dict[str, dict[tuple[str | None, str | None], list[dict[str, Any]]]] = {}
    for qname, rows in states.items():
        for row in rows:
            identity = (row.get("context_ref"), row.get("fact_id"))
            out.setdefault(qname, {}).setdefault(identity, []).append(row)
    return out


def state_differences(
    primary_states: dict[str, list[dict[str, Any]]],
    independent_states: dict[str, list[dict[str, Any]]],
) -> dict[str, int]:
    primary_idx = _states_by_identity(primary_states)
    independent_idx = _states_by_identity(independent_states)
    counts: Counter[str] = Counter()
    for qname in sorted(set(primary_idx) | set(independent_idx)):
        p_rows = primary_idx.get(qname, {})
        i_rows = independent_idx.get(qname, {})
        for identity in sorted(set(p_rows) | set(i_rows), key=lambda item: (str(item[0]), str(item[1]))):
            p_group = sorted(p_rows.get(identity, []), key=lambda row: (row.get("content_sha256") or "", row.get("normalized_character_count", -1)))
            i_group = sorted(i_rows.get(identity, []), key=lambda row: (row.get("content_sha256") or "", row.get("normalized_character_count", -1)))
            if len(p_group) != len(i_group):
                counts["state_count"] += abs(len(p_group) - len(i_group))
            for index in range(min(len(p_group), len(i_group))):
                p_row, i_row = p_group[index], i_group[index]
                for field in (
                    "continued_chain_length",
                    "continued_chain_complete",
                    "normalized_character_count",
                    "content_sha256",
                ):
                    if p_row.get(field) != i_row.get(field):
                        counts[field] += 1
    return dict(sorted(counts.items()))


def _text_digest(text: str) -> str | None:
    return sha256(text.encode("utf-8")) if text else None


def diagnose_document(record: dict[str, Any], event: dict[str, Any], body: bytes) -> dict[str, Any]:
    canonical = record["canonical_key"]
    key = record_key(record)
    expected_sha = str(record.get("primary_document_sha256") or "")
    actual_sha = sha256(body)
    http_ok = actual_sha == expected_sha and event.get("primary_document_sha256") == expected_sha
    if not http_ok:
        raise ValueError("Q220_DIAGNOSTIC_PRIMARY_SOURCE_HASH_MISMATCH:" + key)

    document = body.decode("utf-8", errors="replace")
    primary_states = primary.textblock_states(document)
    independent_states = independent.parse_textblock_states(document)
    p_texts = primary_texts(document)
    i_texts = independent_texts(document)

    mismatching_qnames = [
        qname for qname in sorted(set(primary_states) | set(independent_states))
        if primary_states.get(qname) != independent_states.get(qname)
    ]
    details: list[dict[str, Any]] = []
    for qname in mismatching_qnames[:MAX_MISMATCH_QNAMES_PER_RECORD]:
        p_group = p_texts.get(qname, {})
        i_group = i_texts.get(qname, {})
        p_state_groups = _states_by_identity({qname: primary_states.get(qname, [])}).get(qname, {})
        i_state_groups = _states_by_identity({qname: independent_states.get(qname, [])}).get(qname, {})
        fact_details: list[dict[str, Any]] = []
        for identity in sorted(set(p_group) | set(i_group), key=lambda item: (str(item[0]), str(item[1]))):
            p_values = sorted(p_group.get(identity, []), key=lambda value: (len(value), value))
            i_values = sorted(i_group.get(identity, []), key=lambda value: (len(value), value))
            p_rows = p_state_groups.get(identity, [])
            i_rows = i_state_groups.get(identity, [])
            group_diff = (
                len(p_values) != len(i_values)
                or p_values != i_values
                or p_rows != i_rows
            )
            if not group_diff:
                continue
            for index in range(max(len(p_values), len(i_values))):
                if len(fact_details) >= MAX_FACT_DETAILS_PER_QNAME:
                    break
                p = p_values[index] if index < len(p_values) else None
                i = i_values[index] if index < len(i_values) else None
                pr = p_rows[index] if index < len(p_rows) else {}
                ir = i_rows[index] if index < len(i_rows) else {}
                fact_details.append({
                    "context_ref": identity[0],
                    "fact_id": identity[1],
                    "primary": {
                        "normalized_character_count": len(p) if p is not None else None,
                        "content_sha256": _text_digest(p) if p is not None else None,
                        "continued_chain_length": pr.get("continued_chain_length"),
                        "continued_chain_complete": pr.get("continued_chain_complete"),
                        "preview": p[:MAX_PREVIEW_CHARS] if p is not None else None,
                    },
                    "independent": {
                        "normalized_character_count": len(i) if i is not None else None,
                        "content_sha256": _text_digest(i) if i is not None else None,
                        "continued_chain_length": ir.get("continued_chain_length"),
                        "continued_chain_complete": ir.get("continued_chain_complete"),
                        "preview": i[:MAX_PREVIEW_CHARS] if i is not None else None,
                    },
                    "first_difference": first_difference(p, i) if p is not None and i is not None else None,
                })
        details.append({
            "qname": qname,
            "primary_fact_count": sum(len(values) for values in p_group.values()),
            "independent_fact_count": sum(len(values) for values in i_group.values()),
            "fact_details": fact_details,
        })

    return {
        "record_key": key,
        "cik": str(canonical.get("cik") or "").zfill(10),
        "accession": str(canonical.get("accession") or ""),
        "form": str(canonical.get("form") or ""),
        "filed_date": str(canonical.get("filed_date") or ""),
        "primary_document": str(record.get("primary_document") or ""),
        "http_status": 200,
        "expected_primary_document_sha256": expected_sha,
        "actual_primary_document_sha256": actual_sha,
        "source_hash_verified": True,
        "compiler_textblock_fact_count": sum(len(rows) for rows in primary_states.values()),
        "independent_textblock_fact_count": sum(len(rows) for rows in independent_states.values()),
        "compiler_distinct_qname_count": len(primary_states),
        "independent_distinct_qname_count": len(independent_states),
        "mismatch_qname_count": len(mismatching_qnames),
        "mismatching_qnames": mismatching_qnames,
        "field_difference_counts": state_differences(primary_states, independent_states),
        "mismatch_details_truncated": len(mismatching_qnames) > MAX_MISMATCH_QNAMES_PER_RECORD,
        "mismatch_details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q220_textblock_mismatch_diagnostic",
        "candidate_id": "Q220",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Q220_TEXTBLOCK_DIAGNOSTIC_BLOCKED",
        "diagnostic_only": True,
        "gate_positive": False,
        "records_checked": 0,
        "records": [],
        "errors": [],
        "scientific_evidence": False,
        "performance_authorization": False,
        "performance_authorized": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    try:
        population = json.loads(POPULATION.read_text(encoding="utf-8"))
        compiler = json.loads(COMPILER.read_text(encoding="utf-8"))
        failed = json.loads(FAILED_REPRODUCTION.read_text(encoding="utf-8"))
        current_compiler_sha = sha256((ROOT / "automation/q220_historical_representation_pit.py").read_bytes())
        if population.get("receipt_fingerprint") != EXPECTED_POPULATION_FP or primary.canonical_fingerprint(population) != EXPECTED_POPULATION_FP:
            raise ValueError("Q220_DIAGNOSTIC_POPULATION_RECEIPT_CHANGED")
        if compiler.get("receipt_fingerprint") != EXPECTED_COMPILER_FP or primary.canonical_fingerprint(compiler) != EXPECTED_COMPILER_FP:
            raise ValueError("Q220_DIAGNOSTIC_COMPILER_RECEIPT_CHANGED")
        if compiler.get("compiler_code_sha256") != current_compiler_sha:
            raise ValueError("Q220_DIAGNOSTIC_COMPILER_CODE_VERSION_CHANGED")
        if failed.get("receipt_fingerprint") != EXPECTED_FAILED_REPRODUCTION_FP or independent.canonical_fingerprint(failed) != EXPECTED_FAILED_REPRODUCTION_FP:
            raise ValueError("Q220_DIAGNOSTIC_FAILED_RECEIPT_CHANGED")
        if failed.get("upstream", {}).get("compiler_receipt_fingerprint") != compiler.get("receipt_fingerprint"):
            raise ValueError("Q220_DIAGNOSTIC_COMPILER_LINEAGE_CHANGED")
        if failed.get("gate_positive") is not False or not failed.get("textblock_mismatches"):
            raise ValueError("Q220_DIAGNOSTIC_MISMATCH_BASELINE_NOT_NEGATIVE")

        record_by_key = {record_key(row): row for row in population.get("records", [])}
        event_by_key = {str(row.get("record_key") or ""): row for row in compiler.get("events", [])}
        keys = list(failed["textblock_mismatches"][:TARGET_SAMPLE_SIZE])
        for key in keys:
            record = record_by_key.get(key)
            event = event_by_key.get(key)
            if record is None or event is None:
                raise ValueError("Q220_DIAGNOSTIC_BASELINE_KEY_NOT_JOINED:" + key)
            cik = str(record["canonical_key"]["cik"]).zfill(10)
            accession = str(record["canonical_key"]["accession"])
            filename = str(record["primary_document"])
            body, http_status = independent.fetch_primary(cik, accession, filename)
            if http_status != 200:
                raise ValueError(f"Q220_DIAGNOSTIC_FETCH_STATUS_{http_status}:{key}")
            result["records"].append(diagnose_document(record, event, body))
        result["records_checked"] = len(result["records"])
        result["status"] = "Q220_TEXTBLOCK_DIAGNOSTIC_CAPTURED"
        result["baseline"] = {
            "population_receipt_fingerprint": population["receipt_fingerprint"],
            "compiler_receipt_fingerprint": compiler["receipt_fingerprint"],
            "independent_failure_receipt_fingerprint": failed["receipt_fingerprint"],
            "compiler_code_sha256": compiler["compiler_code_sha256"],
            "source_fetch_scope": "first three records from the pinned failure receipt only",
        }
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}:{str(exc)[:800]}")
    result["receipt_fingerprint"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {key: value for key, value in result.items() if key not in {"records", "errors"}}
    summary["error_count"] = len(result["errors"])
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    # A captured mismatch is a successful diagnostic run; only stale inputs,
    # bad source hashes or failed retrieval are an execution failure.
    return 0 if result["status"] == "Q220_TEXTBLOCK_DIAGNOSTIC_CAPTURED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
