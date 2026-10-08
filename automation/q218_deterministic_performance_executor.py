"""Deterministic, network-free Q218 performance executor.

The executor consumes only a frozen Q218 input bundle. It performs no
selection, ranking, tuning, holdout choice, parameter search or live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRIAL_ID = "T-2026-10-08-Q218-PERFORMANCE-01"
BUCKETS = 64
TOKEN_RE = re.compile(r"[a-z0-9]+")


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self.skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self.skip:
            self.skip -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fp(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_child(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if root.resolve() not in candidate.parents:
        raise RuntimeError("Q218 bundle path escapes bundle root")
    return candidate


def normalize_text(raw: bytes) -> str:
    decoded = html.unescape(raw.decode("utf-8", errors="replace"))
    parser = _TextParser()
    parser.feed(decoded)
    text = " ".join(parser.parts)
    return re.sub(r"\s+", " ", text).strip().lower()


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def _bucket(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % BUCKETS


def frequencies(values: list[str]) -> list[float]:
    counts = [0] * BUCKETS
    for value in values:
        counts[_bucket(value)] += 1
    total = sum(counts)
    return [count / total for count in counts] if total else [0.0] * BUCKETS


def presence(values: list[str]) -> set[int]:
    return {_bucket(value) for value in values}


def cosine_distance(a: list[float], b: list[float]) -> float:
    aa = math.sqrt(sum(x * x for x in a))
    bb = math.sqrt(sum(x * x for x in b))
    if aa == 0.0 or bb == 0.0:
        return 1.0 if any(a) or any(b) else 0.0
    return 1.0 - sum(x * y for x, y in zip(a, b)) / (aa * bb)


def construct_features(mandatory_raw: bytes, voluntary_raw: bytes) -> dict[str, float]:
    mandatory = tokens(normalize_text(mandatory_raw))
    voluntary = tokens(normalize_text(voluntary_raw))
    mp = presence(mandatory)
    vp = presence(voluntary)
    union = len(mp | vp)
    coverage_gap = 1.0 - (len(mp & vp) / union if union else 1.0)
    mf = frequencies(mandatory)
    vf = frequencies(voluntary)
    omission_asymmetry = sum(abs(x - y) for x, y in zip(mf, vf)) / BUCKETS
    mb = [" ".join(pair) for pair in zip(mandatory, mandatory[1:])]
    vb = [" ".join(pair) for pair in zip(voluntary, voluntary[1:])]
    framing_gap = cosine_distance(frequencies(mb), frequencies(vb))
    return {
        "topic_coverage_gap_mandatory_vs_voluntary": coverage_gap,
        "omission_asymmetry_by_topic": omission_asymmetry,
        "secondary_framing_gap": framing_gap,
    }


def _verify_bundle(bundle_path: Path) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    if bundle.get("trial_id") != TRIAL_ID:
        raise RuntimeError("Q218 bundle trial identity mismatch")
    expected = bundle.get("bundle_fingerprint")
    if not expected:
        raise RuntimeError("Q218 bundle fingerprint missing")
    unsigned = dict(bundle)
    unsigned.pop("bundle_fingerprint", None)
    if fp(unsigned) != expected:
        raise RuntimeError("Q218 bundle self-fingerprint mismatch")
    if bundle.get("executor_network_access") is not False:
        raise RuntimeError("Q218 executor must be network-free")
    if bundle.get("selection_used") is not False or bundle.get("parameter_search") is not False:
        raise RuntimeError("Q218 bundle crosses selection boundary")
    contract_sha = str(bundle.get("contract_sha256") or "")
    if not contract_sha:
        raise RuntimeError("Q218 bundle contract fingerprint missing")
    contract_path = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"
    if not contract_path.is_file() or file_sha256(contract_path) != contract_sha:
        raise RuntimeError("Q218 frozen performance contract fingerprint mismatch")
    events = bundle.get("events")
    if not isinstance(events, list) or not events:
        raise RuntimeError("Q218 bundle event population missing")
    docs = bundle.get("documents")
    bars = bundle.get("market_bars")
    if not isinstance(docs, list) or not isinstance(bars, list):
        raise RuntimeError("Q218 bundle inputs incomplete")
    return bundle


def validate_bundle_sources(bundle: dict[str, Any], bundle_root: Path) -> None:
    """Validate all frozen source/identity boundaries before evaluation."""
    cutoff = str(bundle.get("future_cutoff_session") or "")
    seen_accessions: set[str] = set()
    for document in bundle.get("documents", []):
        accession = str(document.get("accession") or "")
        form = str(document.get("form") or "")
        if not accession or accession in seen_accessions:
            raise RuntimeError("Q218 duplicate or missing document accession")
        seen_accessions.add(accession)
        if form not in {"10-K", "8-K"}:
            raise RuntimeError(f"Q218 amended or unsupported SEC form in bundle: {accession}")
        if not document.get("sha256") or not document.get("header_sha256"):
            raise RuntimeError(f"Q218 source fingerprints incomplete: {accession}")
        doc_path = _safe_child(bundle_root, str(document.get("path") or ""))
        header_path = _safe_child(bundle_root, str(document.get("header_path") or ""))
        if not doc_path.is_file() or file_sha256(doc_path) != str(document["sha256"]):
            raise RuntimeError(f"Q218 SEC source fingerprint mismatch: {accession}")
        if not header_path.is_file() or file_sha256(header_path) != str(document["header_sha256"]):
            raise RuntimeError(f"Q218 SEC header fingerprint mismatch: {accession}")

    seen_events: set[tuple[str, str, str]] = set()
    for event in bundle.get("events", []):
        issuer = str(event.get("issuer") or "")
        ten_k = str(event.get("ten_k_accession") or "")
        eight_k = str(event.get("item_2_02_8k_accession") or "")
        key = (issuer, ten_k, eight_k)
        if not all(key) or key in seen_events:
            raise RuntimeError("Q218 duplicate or incomplete event identity")
        seen_events.add(key)
        closure = str(event.get("pair_closure_clock") or "")
        action = str(event.get("action_session") or "")
        if not closure or not action:
            raise RuntimeError("Q218 event timing incomplete")
        if cutoff and action > cutoff:
            raise RuntimeError(f"Q218 action session exceeds cutoff: {action}")
        docs_for_event = {
            str(d.get("accession") or ""): d
            for d in bundle.get("documents", [])
            if str(d.get("accession") or "") in {ten_k, eight_k}
        }
        if ten_k not in docs_for_event or eight_k not in docs_for_event:
            raise RuntimeError("Q218 event references unknown SEC accession")
        if docs_for_event[ten_k].get("form") != "10-K":
            raise RuntimeError("Q218 mandatory document is not an unamended 10-K")
        if docs_for_event[eight_k].get("form") != "8-K":
            raise RuntimeError("Q218 voluntary document is amended or unsupported")

    seen_market: set[tuple[str, str]] = set()
    for bar in bundle.get("market_bars", []):
        key = (str(bar.get("symbol") or ""), str(bar.get("session") or ""))
        if not all(key) or key in seen_market:
            raise RuntimeError("Q218 duplicate or incomplete market bar identity")
        seen_market.add(key)
        raw_path = _safe_child(bundle_root, str(bar.get("raw_response_path") or ""))
        if not raw_path.is_file() or file_sha256(raw_path) != str(bar.get("raw_response_sha256") or ""):
            raise RuntimeError(f"Q218 market source fingerprint mismatch: {key[0]} {key[1]}")
        if cutoff and key[1] > cutoff:
            raise RuntimeError(f"Q218 market bar exceeds cutoff: {key[1]}")
        for field in ("open", "close"):
            value = bar.get(field)
            if value is None or not math.isfinite(float(value)) or float(value) <= 0:
                raise RuntimeError(f"Q218 invalid market bar: {key[0]} {key[1]}")

def execute(bundle_path: Path, output_path: Path) -> dict[str, Any]:
    bundle = _verify_bundle(bundle_path)
    bundle_root = bundle_path.parent
    validate_bundle_sources(bundle, bundle_root)
    doc_by_accession = {str(d["accession"]): d for d in bundle["documents"]}
    bar_by_symbol_date = {(str(b["symbol"]), str(b["session"])): b for b in bundle["market_bars"]}
    rows: list[dict[str, Any]] = []
    for event in bundle["events"]:
        mandatory = doc_by_accession.get(str(event["ten_k_accession"]))
        voluntary = doc_by_accession.get(str(event["item_2_02_8k_accession"]))
        if not mandatory or not voluntary:
            raise RuntimeError("Q218 bundle missing paired SEC documents")
        action = str(event["action_session"])
        bar = bar_by_symbol_date.get((str(event["issuer"]), action))
        if not bar:
            raise RuntimeError(f"Q218 market bar missing: {event['issuer']} {action}")
        if float(bar["open"]) <= 0.0 or float(bar["close"]) <= 0.0:
            raise RuntimeError("Q218 invalid market price")
        features = construct_features(
            _safe_child(bundle_root, str(mandatory["path"])).read_bytes(),
            _safe_child(bundle_root, str(voluntary["path"])).read_bytes(),
        )
        outcome = float(bar["close"]) / float(bar["open"]) - 1.0
        rows.append({
            "issuer": event["issuer"],
            "ten_k_accession": event["ten_k_accession"],
            "item_2_02_8k_accession": event["item_2_02_8k_accession"],
            "pair_closure_clock": event["pair_closure_clock"],
            "action_session": action,
            "features": features,
            "outcome": outcome,
        })
    result = {
        "schema_version": "1.0",
        "record_type": "q218_deterministic_performance_result",
        "candidate_id": "Q218",
        "trial_id": TRIAL_ID,
        "bundle_fingerprint": bundle["bundle_fingerprint"],
        "event_count": len(rows),
        "events": rows,
        "performance_evaluation": True,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "parameter_search": False,
        "threshold_search": False,
        "horizon_search": False,
        "asset_search": False,
        "variant_search": False,
        "family_ranking": False,
        "promotion_decision": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["report_fingerprint"] = fp(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = execute(args.bundle, args.output)
    print(json.dumps({"trial_id": result["trial_id"], "event_count": result["event_count"], "report_fingerprint": result["report_fingerprint"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
