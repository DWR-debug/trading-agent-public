"""Independent, source-retrieving Q220 PIT reproduction.

This implementation deliberately uses Python's HTMLParser tree, not the primary
compiler's regular-expression parser. It verifies the frozen population, independently
fetches and hashes every primary filing, recomputes exact TextBlock/numeric states and
strict historical prefixes, then compares those states with the compiler receipt.
It is source/PIT structure only: it does not read outcomes or authorize performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "research/evidence/q220_as_filed_xbrl_population_latest.json"
CONTRACT = ROOT / "research/preregistrations/q220_as_filed_xbrl_population_contract_2026_10_06.json"
COMPILER_RECEIPT = ROOT / "research/evidence/q220_historical_representation_pit_latest.json"
OUTPUT_DEFAULT = ROOT / "research/evidence/q220_independent_pit_reproduction_latest.json"

EXPECTED_POPULATION_FINGERPRINT = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
EXPECTED_RECORD_COUNT = 55
SEC_ROOT = "https://www.sec.gov/Archives/edgar/data"
USER_AGENT = "DWR-debug/trading-agent-public Q220 independent PIT reproduction/1.0 research@example.invalid"
MAX_DOCUMENT_BYTES = 35_000_000
MAX_ATTEMPTS = 3
REQUEST_GAP_SECONDS = 0.25
NUMERIC_QNAMES = (
    "us-gaap:Assets",
    "us-gaap:OperatingIncomeLoss",
    "us-gaap:NetIncomeLoss",
    "us-gaap:NetCashProvidedByUsedInOperatingActivities",
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
)
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
SCRIPTS_AND_STYLES = {"script", "style"}
_CLOCK_LOCK = threading.Lock()
_NEXT_ALLOWED = 0.0


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Any] = field(default_factory=list)
    self_closing: bool = False


class FilingTreeParser(HTMLParser):
    """A tolerant element tree built through stdlib HTML tokenization."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.stack = [self.root]

    def _new_node(self, tag: str, attrs: list[tuple[str, str | None]], closed: bool = False) -> Node:
        return Node(
            tag=tag.lower(),
            attrs={str(k).lower(): ("" if v is None else str(v).strip()) for k, v in attrs},
            self_closing=closed,
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = self._new_node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag.lower() not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].children.append(self._new_node(tag, attrs, closed=True))

    def handle_endtag(self, tag: str) -> None:
        target = tag.lower()
        for idx in range(len(self.stack) - 1, 0, -1):
            if self.stack[idx].tag == target:
                del self.stack[idx:]
                return

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(data)

    def handle_comment(self, data: str) -> None:
        self.stack[-1].children.append(Node("#comment"))

    def handle_decl(self, decl: str) -> None:
        self.stack[-1].children.append(Node("#declaration"))

    def handle_pi(self, data: str) -> None:
        self.stack[-1].children.append(Node("#pi"))

    def handle_entityref(self, name: str) -> None:
        self.stack[-1].children.append("&" + name + ";")

    def handle_charref(self, name: str) -> None:
        self.stack[-1].children.append("&#" + name + ";")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_fingerprint(value: dict[str, Any], field_name: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field_name, None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded)


def normalized_scalar(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _render(child: Any) -> str:
    if isinstance(child, str):
        return child
    if child.tag in SCRIPTS_AND_STYLES:
        return ""
    # HTML tags and comments are boundaries, matching their visible-text role.
    return " " + "".join(_render(grandchild) for grandchild in child.children) + " "


def visible_text(node: Node) -> str:
    return normalized_scalar("".join(_render(child) for child in node.children))


def parse_tree(document: str) -> Node:
    parser = FilingTreeParser()
    parser.feed(document)
    parser.close()
    return parser.root


def walk_nodes(root: Node):
    stack = list(reversed(root.children))
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            continue
        yield item
        stack.extend(reversed(item.children))


def local_tag(node: Node) -> str:
    return node.tag.rsplit(":", 1)[-1].lower()


def parse_textblock_states(document: str) -> dict[str, list[dict[str, Any]]]:
    root = parse_tree(document)
    nodes = list(walk_nodes(root))
    continuations = {
        node.attrs["id"]: node
        for node in nodes
        if local_tag(node) == "continuation" and node.attrs.get("id")
    }
    output: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        attrs = node.attrs
        qname = attrs.get("name", "")
        if local_tag(node) != "nonnumeric" or not qname.rsplit(":", 1)[-1].lower().endswith("textblock"):
            continue

        fragments = [visible_text(node)]
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
            continuation = continuations.get(next_id)
            if continuation is None:
                chain_complete = False
                break
            fragments.append(visible_text(continuation))
            next_id = continuation.attrs.get("continuedat")

        text = normalized_scalar(" ".join(fragments))
        row = {
            "context_ref": attrs.get("contextref"),
            "fact_id": attrs.get("id"),
            "continued_chain_length": len(chain_ids),
            "continued_chain_complete": chain_complete,
            "normalized_character_count": len(text),
            "content_sha256": sha256(text.encode("utf-8")) if text else None,
        }
        output.setdefault(qname, []).append(row)

    for qname, rows in output.items():
        rows.sort(key=lambda x: (
            str(x.get("context_ref") or ""),
            str(x.get("fact_id") or ""),
            str(x.get("content_sha256") or ""),
        ))
    return output


def parse_numeric(text: str, attrs: dict[str, str]) -> tuple[str | None, str]:
    value_text = normalized_scalar(text).replace("\u2212", "-")
    if attrs.get("xsi:nil", "").lower() == "true" or attrs.get("nil", "").lower() == "true":
        return None, "NIL"
    negative_parentheses = value_text.startswith("(") and value_text.endswith(")")
    value_text = value_text.strip("()").replace(",", "")
    value_text = re.sub(r"[^0-9.+\-]", "", value_text)
    if not value_text or value_text in {".", "+", "-", "+.", "-."}:
        return None, "UNPARSEABLE_NUMERIC_TEXT"
    try:
        value = Decimal(value_text)
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


def parse_structured_states(document: str) -> dict[str, list[dict[str, Any]]]:
    root = parse_tree(document)
    output: dict[str, list[dict[str, Any]]] = {}
    wanted = set(NUMERIC_QNAMES)
    for node in walk_nodes(root):
        attrs = node.attrs
        qname = attrs.get("name", "")
        if local_tag(node) != "nonfraction" or node.self_closing or qname not in wanted:
            continue
        raw_text = visible_text(node)
        parsed_value, parse_status = parse_numeric(raw_text, attrs)
        output.setdefault(qname, []).append({
            "context_ref": attrs.get("contextref"),
            "unit_ref": attrs.get("unitref"),
            "decimals": attrs.get("decimals"),
            "scale": attrs.get("scale", "0"),
            "sign": attrs.get("sign", "+"),
            "nil": attrs.get("xsi:nil", attrs.get("nil", "false")).lower() == "true",
            "normalized_value": parsed_value,
            "parse_status": parse_status,
            "raw_value_sha256": sha256(raw_text.encode("utf-8")),
        })
    for qname, rows in output.items():
        rows.sort(key=lambda x: (
            str(x.get("context_ref") or ""),
            str(x.get("unit_ref") or ""),
            str(x.get("normalized_value") or ""),
            str(x.get("raw_value_sha256") or ""),
        ))
    return output


def record_key(record: dict[str, Any]) -> str:
    key = record["canonical_key"]
    return "|".join(str(key[name]) for name in ("cik", "accession", "form", "filed_date"))


def acceptance_time(record: dict[str, Any]) -> datetime:
    raw = str(record.get("acceptance_datetime") or "")
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("Q220_INDEPENDENT_ACCEPTANCE_TIME_WITHOUT_ZONE:" + record_key(record))
    return value.astimezone(timezone.utc)


def prefix_summaries(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Compute prefixes from timestamps alone; equal clocks are never ordered."""
    indexed = []
    keys: set[str] = set()
    for record in records:
        key = record_key(record)
        if key in keys:
            raise ValueError("Q220_INDEPENDENT_DUPLICATE_RECORD_KEY:" + key)
        keys.add(key)
        canonical = record["canonical_key"]
        indexed.append({
            "key": key,
            "cik": str(canonical["cik"]).zfill(10),
            "form": str(canonical.get("form") or ""),
            "accepted": acceptance_time(record),
        })

    summaries: dict[str, dict[str, Any]] = {}
    for current in indexed:
        prior = [
            row for row in indexed
            if row["cik"] == current["cik"] and row["accepted"] < current["accepted"]
        ]
        originals = [row for row in prior if row["form"] == "10-K"]
        latest = max(originals, key=lambda row: (row["accepted"], row["key"])) if originals else None
        summaries[current["key"]] = {
            "prior_same_issuer_filing_count": len(prior),
            "prior_same_issuer_original_10k_count": len(originals),
            "latest_prior_original_10k": latest["key"] if latest else None,
        }
    return summaries


def change_states(
    current_textblocks: dict[str, list[dict[str, Any]]],
    previous_textblocks: dict[str, list[dict[str, Any]]],
    current_structured: dict[str, list[dict[str, Any]]],
    previous_structured: dict[str, list[dict[str, Any]]],
) -> tuple[list[str], list[str]]:
    current_text_hashes = {q: [row["content_sha256"] for row in rows] for q, rows in current_textblocks.items()}
    previous_text_hashes = {q: [row["content_sha256"] for row in rows] for q, rows in previous_textblocks.items()}
    text_names = set(current_text_hashes) | set(previous_text_hashes)
    narrative_changed = sorted(
        q for q in text_names if current_text_hashes.get(q, []) != previous_text_hashes.get(q, [])
    )

    current_values = {
        q: [(x["context_ref"], x["unit_ref"], x["normalized_value"], x["parse_status"], x["raw_value_sha256"]) for x in rows]
        for q, rows in current_structured.items()
    }
    previous_values = {
        q: [(x["context_ref"], x["unit_ref"], x["normalized_value"], x["parse_status"], x["raw_value_sha256"]) for x in rows]
        for q, rows in previous_structured.items()
    }
    names = set(current_values) | set(previous_values)
    structured_changed = sorted(
        q for q in names if current_values.get(q, []) != previous_values.get(q, [])
    )
    return narrative_changed, structured_changed


def _rate_wait() -> None:
    global _NEXT_ALLOWED
    with _CLOCK_LOCK:
        now = time.monotonic()
        if now < _NEXT_ALLOWED:
            time.sleep(_NEXT_ALLOWED - now)
        _NEXT_ALLOWED = time.monotonic() + REQUEST_GAP_SECONDS


def fetch_primary(cik: str, accession: str, filename: str) -> tuple[bytes, int]:
    """Independently retrieve one immutable filing primary document from SEC."""
    if (
        not filename or "/" in filename or "\\" in filename or filename in {".", ".."}
        or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession)
    ):
        raise ValueError("Q220_INDEPENDENT_UNSAFE_DOCUMENT_IDENTITY")
    compact = accession.replace("-", "")
    url = f"{SEC_ROOT}/{int(cik)}/{compact}/{quote(filename, safe='-._')}"
    last_error = "unknown"
    for attempt in range(MAX_ATTEMPTS):
        _rate_wait()
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,*/*",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read(MAX_DOCUMENT_BYTES + 1)
                if len(body) > MAX_DOCUMENT_BYTES:
                    raise ValueError("Q220_INDEPENDENT_DOCUMENT_EXCEEDS_BYTE_LIMIT")
                return body, int(getattr(response, "status", 200))
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP_{exc.code}"
            if exc.code not in {408, 425, 429, 500, 502, 503, 504} or attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(f"Q220_INDEPENDENT_SEC_FETCH_{last_error}:{accession}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = type(exc).__name__
            if attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(f"Q220_INDEPENDENT_SEC_FETCH_FAILED:{accession}:{last_error}") from exc
        time.sleep(min(8.0, 2.0 ** (attempt + 1)))
    raise RuntimeError(f"Q220_INDEPENDENT_SEC_FETCH_FAILED:{accession}:{last_error}")


def _json_equal(left: Any, right: Any) -> bool:
    return json.dumps(left, sort_keys=True, separators=(",", ":"), ensure_ascii=False) == json.dumps(
        right, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def _new_blocked_receipt(error: str) -> dict[str, Any]:
    result = {
        "schema_version": 1,
        "record_type": "q220_independent_pit_reproduction",
        "candidate_id": "Q220",
        "status": "Q220_INDEPENDENT_PIT_REPRODUCTION_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_positive": False,
        "fatal_error": error[:1000],
        "records_checked": 0,
        "independently_retrieved_documents": 0,
        "scientific_evidence": False,
        "performance_authorization": False,
        "performance_authorized": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = canonical_fingerprint(result)
    return result


def reproduce(
    population: dict[str, Any],
    contract: dict[str, Any],
    compiler_receipt: dict[str, Any],
    *,
    contract_bytes: bytes,
    fetcher: Callable[[str, str, str], tuple[bytes, int]] = fetch_primary,
    expected_population_fingerprint: str = EXPECTED_POPULATION_FINGERPRINT,
    expected_record_count: int = EXPECTED_RECORD_COUNT,
) -> dict[str, Any]:
    """Recompute Q220's frozen PIT states through an independent parser/fetch path."""
    errors: list[dict[str, str]] = []
    textblock_mismatches: list[str] = []
    structured_mismatches: list[str] = []
    prefix_mismatches: list[str] = []
    change_mismatches: list[str] = []
    identity_mismatches: list[str] = []
    source_hash_failures: list[dict[str, str]] = []

    population_fp = str(population.get("receipt_fingerprint") or "")
    population_self_valid = len(population_fp) == 64 and canonical_fingerprint(population) == population_fp
    population_version_valid = population_fp == expected_population_fingerprint
    contract_valid = (
        contract.get("candidate_id") == "Q220"
        and population.get("candidate_id") == "Q220"
        and population.get("mode") == "population"
        and population.get("status") == "Q220_AS_FILED_XBRL_POPULATION_COMPLETED"
        and int(population.get("failure_count", -1)) == 0
        and int(population.get("record_count", -1)) == expected_record_count
        and population.get("contract_sha256") == sha256(contract_bytes)
    )
    compiler_fp = str(compiler_receipt.get("receipt_fingerprint") or "")
    compiler_self_valid = len(compiler_fp) == 64 and canonical_fingerprint(compiler_receipt) == compiler_fp
    compiler_positive = (
        compiler_receipt.get("candidate_id") == "Q220"
        and compiler_receipt.get("status") == "Q220_HISTORICAL_REPRESENTATION_PIT_COMPILED"
        and compiler_receipt.get("gate_positive") is True
        and int(compiler_receipt.get("record_count", -1)) == expected_record_count
        and int(compiler_receipt.get("compiled_event_count", -1)) == expected_record_count
        and int(compiler_receipt.get("verified_primary_document_count", -1)) == expected_record_count
        and int(compiler_receipt.get("source_hash_failure_count", -1)) == 0
        and compiler_receipt.get("source_population_receipt_fingerprint") == population_fp
    )

    records = population.get("records")
    records = records if isinstance(records, list) else []
    events = compiler_receipt.get("events")
    events = events if isinstance(events, list) else []
    population_keys = [record_key(record) for record in records]
    event_keys = [str(event.get("record_key") or "") for event in events]
    key_join_valid = (
        len(records) == expected_record_count
        and len(set(population_keys)) == len(population_keys)
        and len(events) == expected_record_count
        and len(set(event_keys)) == len(event_keys)
        and set(population_keys) == set(event_keys)
    )
    event_by_key = {str(event.get("record_key")): event for event in events}
    record_by_key = {record_key(record): record for record in records}

    contract_ciks = set(str(value).zfill(10) for value in (
        (contract.get("fixed_universe") or {}).get("ciks", {}) or {}
    ).values())
    universe_valid = bool(contract_ciks) and all(
        str(record.get("canonical_key", {}).get("cik", "")).zfill(10) in contract_ciks
        for record in records
    )
    timestamp_valid = True
    for record in records:
        try:
            acceptance_time(record)
        except (ValueError, TypeError, KeyError):
            timestamp_valid = False
            break

    parsed_textblocks: dict[str, dict[str, list[dict[str, Any]]]] = {}
    parsed_structured: dict[str, dict[str, list[dict[str, Any]]]] = {}
    independently_retrieved = 0
    no_textblock_records: list[dict[str, str]] = []
    mapping_complete = True

    if not (population_self_valid and population_version_valid and contract_valid and compiler_self_valid and compiler_positive and key_join_valid and universe_valid and timestamp_valid):
        errors.append({"error": "FROZEN_POPULATION_COMPILER_LINEAGE_OR_IDENTITY_CHECK_FAILED"})

    # Continue the bounded source inspection when the record list is structurally usable,
    # but an invalid upstream fingerprint can never be turned into a positive receipt.
    for record in records:
        key = record_key(record)
        canonical = record["canonical_key"]
        event = event_by_key.get(key)
        cik = str(canonical.get("cik", "")).zfill(10)
        accession = str(canonical.get("accession") or "")
        form = str(canonical.get("form") or "")
        filed_date = str(canonical.get("filed_date") or "")
        filename = str(record.get("primary_document") or "")
        if event is None:
            identity_mismatches.append(key)
            continue
        expected_primary_sha = str(record.get("primary_document_sha256") or "")
        if (
            event.get("cik") != cik
            or event.get("accession") != accession
            or event.get("form") != form
            or event.get("filed_date") != filed_date
            or event.get("primary_document") != filename
            or event.get("acceptance_datetime_utc") != acceptance_time(record).isoformat()
            or event.get("primary_document_sha256") != expected_primary_sha
            or event.get("source_hash_verified") is not True
        ):
            identity_mismatches.append(key)
            continue
        try:
            body, http_status = fetcher(cik, accession, filename)
            actual_sha = sha256(body)
            if http_status != 200 or actual_sha != expected_primary_sha:
                source_hash_failures.append({
                    "record_key": key,
                    "error": "INDEPENDENT_PRIMARY_DOCUMENT_HASH_MISMATCH",
                    "expected_sha256": expected_primary_sha,
                    "actual_sha256": actual_sha,
                    "http_status": str(http_status),
                })
                continue
            document = body.decode("utf-8", errors="replace")
            textblocks = parse_textblock_states(document)
            structured = parse_structured_states(document)
            independently_retrieved += 1
            parsed_textblocks[key] = textblocks
            parsed_structured[key] = structured

            compiler_textblocks = event.get("textblock_content_states")
            compiler_structured = event.get("structured_facts_by_qname")
            if not _json_equal(textblocks, compiler_textblocks):
                textblock_mismatches.append(key)
            if not _json_equal(structured, compiler_structured):
                structured_mismatches.append(key)

            population_text_qnames = set(str(x) for x in record.get("textblock_concepts", []))
            independently_parsed_qnames = set(textblocks)
            mapped_text_qnames = set(str(x) for x in record.get("presentation_mapped_textblock_concepts", []))
            if population_text_qnames != independently_parsed_qnames:
                textblock_mismatches.append(key + ":POPULATION_QNAME_SET")
            if independently_parsed_qnames - mapped_text_qnames:
                mapping_complete = False
            if independently_parsed_qnames and record.get("presentation_mapping_complete_for_observed_textblocks") is not True:
                mapping_complete = False
            if (
                event.get("textblock_fact_count") != sum(len(rows) for rows in textblocks.values())
                or event.get("distinct_textblock_qname_count") != len(textblocks)
                or event.get("structured_fact_counts_by_exact_qname") != {
                    qname: len(structured.get(qname, [])) for qname in NUMERIC_QNAMES
                }
                or event.get("presentation_mapping_complete_in_population_receipt")
                != bool(record.get("presentation_mapping_complete_for_observed_textblocks"))
            ):
                identity_mismatches.append(key + ":SUMMARY_FIELDS")
            if not textblocks:
                no_textblock_records.append({
                    "record_key": key,
                    "form": form,
                    "filed_date": filed_date,
                })
        except Exception as exc:
            errors.append({"record_key": key, "error": f"{type(exc).__name__}:{str(exc)[:400]}"})

    # Independently reconstruct all strict prefixes and their baselines from frozen
    # acceptance clocks, then compare counts and original/amendment lineage.
    independent_prefixes: dict[str, dict[str, Any]] = {}
    if timestamp_valid and len(records) == expected_record_count and len(set(population_keys)) == len(population_keys):
        try:
            independent_prefixes = prefix_summaries(records)
            reverse_prefixes = prefix_summaries(list(reversed(records)))
            input_order_invariant = _json_equal(independent_prefixes, reverse_prefixes)

            future_record = dict(records[0])
            future_record["canonical_key"] = dict(records[0]["canonical_key"])
            future_record["canonical_key"]["accession"] = str(future_record["canonical_key"]["accession"]) + "-FUTURE-SENTINEL"
            latest_time = max(acceptance_time(record) for record in records)
            future_record["acceptance_datetime"] = (latest_time + timedelta(days=365)).isoformat()
            with_future = prefix_summaries(records + [future_record])
            future_row_invariant = all(
                with_future.get(key) == summary for key, summary in independent_prefixes.items()
            )
            for key, summary in independent_prefixes.items():
                event = event_by_key.get(key, {})
                if any(event.get(name) != value for name, value in summary.items()):
                    prefix_mismatches.append(key)
                current_textblocks = parsed_textblocks.get(key)
                current_structured = parsed_structured.get(key)
                if current_textblocks is None or current_structured is None:
                    continue
                prior_key = summary["latest_prior_original_10k"]
                prior_textblocks = parsed_textblocks.get(prior_key, {}) if prior_key else {}
                prior_structured = parsed_structured.get(prior_key, {}) if prior_key else {}
                expected_narrative, expected_structured = change_states(
                    current_textblocks, prior_textblocks, current_structured, prior_structured
                )
                if prior_key is None:
                    if event.get("narrative_changed_qnames_vs_latest_prior_original") is not None:
                        change_mismatches.append(key + ":NARRATIVE_BASELINE")
                    if event.get("structured_changed_qnames_vs_latest_prior_original") is not None:
                        change_mismatches.append(key + ":STRUCTURED_BASELINE")
                elif (
                    event.get("narrative_changed_qnames_vs_latest_prior_original") != expected_narrative
                    or event.get("narrative_changed_qname_count_vs_latest_prior_original") != len(expected_narrative)
                    or event.get("structured_changed_qnames_vs_latest_prior_original") != expected_structured
                    or event.get("structured_changed_qname_count_vs_latest_prior_original") != len(expected_structured)
                ):
                    change_mismatches.append(key)
        except Exception as exc:
            input_order_invariant = False
            future_row_invariant = False
            errors.append({"error": f"PREFIX_RECONCILIATION:{type(exc).__name__}:{str(exc)[:400]}"})
    else:
        input_order_invariant = False
        future_row_invariant = False

    compiler_no_textblock = compiler_receipt.get("records_with_no_textblock_observed")
    compiler_no_textblock = compiler_no_textblock if isinstance(compiler_no_textblock, list) else []
    no_textblock_consistent = _json_equal(
        sorted(no_textblock_records, key=lambda item: item["record_key"]),
        sorted(
            [
                {
                    "record_key": str(row.get("record_key") or ""),
                    "form": str(row.get("form") or ""),
                    "filed_date": str(row.get("filed_date") or ""),
                }
                for row in compiler_no_textblock
            ],
            key=lambda item: item["record_key"],
        ),
    )

    checks = {
        "population_fingerprint_valid": population_self_valid,
        "population_version_pinned": population_version_valid,
        "population_contract_hash_valid": contract_valid,
        "compiler_fingerprint_valid": compiler_self_valid,
        "compiler_upstream_gate_positive": compiler_positive,
        "fixed_universe_and_record_identity_valid": universe_valid and timestamp_valid and key_join_valid and not identity_mismatches,
        "all_primary_sources_independently_retrieved_and_hash_verified": independently_retrieved == expected_record_count and not source_hash_failures and not errors,
        "independent_textblock_parser_matches_compiler": len(parsed_textblocks) == expected_record_count and not textblock_mismatches,
        "independent_structured_parser_matches_compiler": len(parsed_structured) == expected_record_count and not structured_mismatches,
        "presentation_map_covers_all_observed_textblocks": mapping_complete,
        "strict_acceptance_time_prefixes_match": bool(independent_prefixes) and not prefix_mismatches,
        "narrative_and_structured_change_states_match": len(parsed_textblocks) == expected_record_count and not change_mismatches,
        "input_order_permutation_invariant": input_order_invariant,
        "future_row_mutation_invariant": future_row_invariant,
        "no_textblock_states_are_explicit_and_reconciled": no_textblock_consistent,
        "compiled_receipt_contains_no_mapping_gaps": compiler_receipt.get("textblock_mapping_complete") is True and not compiler_receipt.get("textblock_mapping_gaps"),
        "scientific_performance_and_promotion_authority_remains_closed": (
            compiler_receipt.get("scientific_evidence") is False
            and compiler_receipt.get("performance_authorization") is False
            and compiler_receipt.get("holdout_selection") is False
            and compiler_receipt.get("ranking") is False
            and compiler_receipt.get("tuning") is False
            and compiler_receipt.get("promotion") is False
            and compiler_receipt.get("live_execution") is False
        ),
    }
    gate_positive = all(checks.values()) and not errors and not source_hash_failures
    result = {
        "schema_version": 1,
        "record_type": "q220_independent_pit_reproduction",
        "candidate_id": "Q220",
        "trial_id": "Q-2026-10-06-Q220-AS-FILED-XBRL-REPAIR",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Q220_INDEPENDENT_PIT_REPRODUCED" if gate_positive else "Q220_INDEPENDENT_PIT_REPRODUCTION_BLOCKED",
        "gate_positive": gate_positive,
        "method": {
            "retrieval": "independent HTTPS retrieval of each frozen SEC primary document",
            "parser": "stdlib html.parser.HTMLParser element tree; no import from primary compiler",
            "scope": "source hashes, Inline XBRL TextBlock/numeric states and strict acceptance-time prefixes",
        },
        "upstream": {
            "population_receipt_fingerprint": population_fp,
            "compiler_receipt_fingerprint": compiler_fp,
            "population_contract_sha256": population.get("contract_sha256"),
            "population_gate_code_sha256": population.get("gate_code_sha256"),
        },
        "fixed_universe": population.get("fixed_universe"),
        "window": population.get("window"),
        "record_count": len(records),
        "compiler_event_count": len(events),
        "independently_retrieved_documents": independently_retrieved,
        "source_hash_failure_count": len(source_hash_failures),
        "source_hash_failures": source_hash_failures,
        "textblock_mismatch_count": len(textblock_mismatches),
        "textblock_mismatches": textblock_mismatches[:100],
        "structured_mismatch_count": len(structured_mismatches),
        "structured_mismatches": structured_mismatches[:100],
        "prefix_mismatch_count": len(prefix_mismatches),
        "prefix_mismatches": prefix_mismatches[:100],
        "change_state_mismatch_count": len(change_mismatches),
        "change_state_mismatches": change_mismatches[:100],
        "identity_mismatch_count": len(identity_mismatches),
        "identity_mismatches": identity_mismatches[:100],
        "no_textblock_observed_count": len(no_textblock_records),
        "no_textblock_observed_record_keys": sorted(row["record_key"] for row in no_textblock_records),
        "checks": checks,
        "errors": errors[:100],
        "next_gate": (
            "bounded adversarial robustness review and formal trial-governance reconciliation; no performance authorization"
            if gate_positive else "repair the exact independent-reproduction mismatches; keep PIT and performance gates closed"
        ),
        "scientific_evidence": False,
        "performance_authorization": False,
        "performance_authorized": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = canonical_fingerprint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--population", type=Path, default=POPULATION)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--compiler-receipt", type=Path, default=COMPILER_RECEIPT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    try:
        contract_bytes = args.contract.read_bytes()
        population = json.loads(args.population.read_text(encoding="utf-8"))
        contract = json.loads(contract_bytes.decode("utf-8"))
        compiler_receipt = json.loads(args.compiler_receipt.read_text(encoding="utf-8"))
        result = reproduce(
            population,
            contract,
            compiler_receipt,
            contract_bytes=contract_bytes,
        )
    except Exception as exc:
        result = _new_blocked_receipt(f"{type(exc).__name__}:{str(exc)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"textblock_mismatches", "structured_mismatches", "prefix_mismatches", "change_state_mismatches", "identity_mismatches", "source_hash_failures", "errors"}}, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("gate_positive") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
