"""Independent Q104:I22 SEC filing-arrival PIT reproduction.

This module does not import the primary Q104:I22 compiler. It reconstructs the
frozen SEC event population independently and refuses to claim mechanism
non-overlap when the candidate metadata contract is incomplete.
Research-only: no returns, performance, ranking, holdout selection, tuning,
promotion, orders, or live execution.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import exchange_calendars as xcals
from automation.evidence_graph_stage4_stage5 import candidate_inventory, candidate_signature, compare_signatures
from research.asset_universes import list_universes

ROOT = Path(__file__).resolve().parents[1]
SYMBOLS = ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")
FORMS = frozenset({"8-K", "8-K/A", "10-Q", "10-Q/A", "10-K", "10-K/A"})
START = date(2011, 1, 1)
END = date(2025, 9, 24)
WINDOW = 20
UNIVERSE = "validation_2026_10_01_q104_sec_treasury_equities"
RECONCILIATION_PATH = ROOT / "research/evidence/q104_i22_cross_arch_reconciliation_latest.json"
Q107_PATH = ROOT / "research/evidence/q107_coverage_result.json"
Q107_MANIFEST_PATH = ROOT / "research/runs/q107_coverage/T-2026-10-01-107-Q104-COVERAGE/snapshot_manifest.json"
Q108_PATH = ROOT / "research/evidence/q108_pit_integration_2026_10_01.json"
PREREG_PATH = ROOT / "research/preregistrations/q104_i22_filing_arrival_2026_10_01.json"

PINNED = {
    "source_workflow_run_id": 38274043682,
    "source_master_sha": "65c879498e3f5d494e1d6c9749418bc0bf137a31",
    "reconciliation_fingerprint": "058bba7fd9aebb9d30cc5294fc71548ebe9bd9f11d5ee38a558936b29ecfb9a0",
    "q107_coverage_fingerprint": "ea3a3fd1c33c3de984b60bad069ed611729c25faa8272211a81e9ce85e1dd6dd",
    "q107_snapshot_fingerprint": "c5eb39fcd802eb73c6c71d4bdbb0c0ec0f132db77c5c0a2c37b4ba1277edf036",
    "q108_receipt_fingerprint": "07dcc87087f6a762ecbddaab0298625fb1bf50123df48758fa5c9f6d56bdc8c3",
}
FROZEN_CIKS = {
    "SPGI": 64040, "NDAQ": 1120193, "AMP": 820027, "RJF": 720005,
    "WMB": 107263, "VLO": 1035002, "DVN": 1090012, "EMN": 915389,
}
PINNED_SOURCE_FP_X64 = "a9595d33a34615553ee706c95458fff0bb9fec9642a9d61710f3e5dbd45ca23e"
PINNED_SOURCE_FP_ARM64 = "bb1521ff938ce1217343362f335aae521d9978b105229eabef69124ac24bbb1c"
MAX_REQUESTS = 40
MAX_RESPONSE_BYTES = 25 * 1024 * 1024
MAX_TOTAL_BYTES = 250 * 1024 * 1024
TIMEOUT_SECONDS = 45


def validate_reproduction_code_sha(value: str) -> str:
    """Require the full immutable commit SHA of the code being audited."""
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise argparse.ArgumentTypeError(
            "reproduction code SHA must be a full lowercase 40-character Git commit SHA"
        )
    return value


USER_AGENT = "trading-agent-public/Q104-I22-independent-PIT-reproduction"
CAL = xcals.get_calendar("XNYS")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def receipt_fingerprint(payload: dict[str, Any]) -> str:
    unsigned = deepcopy(payload)
    unsigned.pop("receipt_fingerprint", None)
    return sha256_bytes(canonical_json(unsigned).encode("utf-8"))


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"EXPECTED_JSON_OBJECT:{path}")
    return payload


def verify_self_fingerprint(payload: dict[str, Any], expected: str, label: str) -> None:
    if payload.get("receipt_fingerprint") != expected:
        raise RuntimeError(f"{label}_PIN_MISMATCH")
    if receipt_fingerprint(payload) != expected:
        raise RuntimeError(f"{label}_CONTENT_FINGERPRINT_MISMATCH")


def validate_q107_policy_flags(q107: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Validate frozen Q107 policy flags at their actual schema locations.

    The coverage receipt stores policy booleans at top level. The canonical
    snapshot manifest stores policy booleans under governance. A missing flag
    is still a hard failure; a schema mismatch must not skip a research gate.
    """
    receipt_false_flags = (
        "performance_evaluation",
        "oos_evaluation",
        "holdout_evaluation",
        "selection_used",
        "holdout_used_for_selection",
    )
    if any(q107.get(key) is not False for key in receipt_false_flags):
        raise RuntimeError("Q107_GOVERNANCE_GATE_MISMATCH")

    manifest_governance = manifest.get("governance", {})
    manifest_false_flags = (
        "performance_evaluation",
        "oos_evaluation",
        "holdout_evaluation",
        "selection_used",
        "holdout_used_for_selection",
        "performance_trial_authorized",
        "automatic_promotion",
    )
    if any(manifest_governance.get(key) is not False for key in manifest_false_flags):
        raise RuntimeError("Q107_MANIFEST_GOVERNANCE_GATE_MISMATCH")

    for label, safety in (
        ("receipt", q107.get("safety", {})),
        ("manifest", manifest.get("safety", {})),
    ):
        if (
            safety.get("paper_only") is not True
            or safety.get("live_trading_enabled") is not False
            or safety.get("orders_enabled") is not False
            or safety.get("automatic_promotion") is not False
        ):
            raise RuntimeError(f"Q107_{label.upper()}_SAFETY_GATE_MISMATCH")


def verify_frozen_contracts() -> dict[str, Any]:
    recon = read_json(RECONCILIATION_PATH)
    verify_self_fingerprint(recon, PINNED["reconciliation_fingerprint"], "I22_RECONCILIATION")
    if recon.get("record_type") != "q104_i22_cross_arch_reconciliation":
        raise RuntimeError("I22_RECONCILIATION_RECORD_TYPE_MISMATCH")
    if recon.get("source_workflow_run_id") != PINNED["source_workflow_run_id"] or recon.get("source_master_sha") != PINNED["source_master_sha"]:
        raise RuntimeError("I22_RECONCILIATION_SOURCE_MISMATCH")
    if recon.get("status") != "I22_PIT_COMPILER_RECONCILED_X64_ARM64_NO_PERFORMANCE" or recon.get("architecture_equality") is not True:
        raise RuntimeError("I22_RECONCILIATION_NOT_POSITIVE")
    if recon.get("mutation_tests") != {"input_order_invariance": True, "future_acceptance_invariance": True, "amendment_accession_separation": True}:
        raise RuntimeError("I22_FROZEN_MUTATION_CONTRACT_MISMATCH")
    if recon.get("safety", {}).get("paper_only") is not True or recon.get("safety", {}).get("live_trading_enabled") is not False:
        raise RuntimeError("I22_SAFETY_CONTRACT_MISMATCH")

    q107 = read_json(Q107_PATH)
    if q107.get("status") != "coverage_passed":
        raise RuntimeError("Q107_FROZEN_COVERAGE_NOT_POSITIVE")
    if q107.get("coverage_fingerprint") != PINNED["q107_coverage_fingerprint"] or q107.get("snapshot_fingerprint") != PINNED["q107_snapshot_fingerprint"]:
        raise RuntimeError("Q107_FINGERPRINT_MISMATCH")
    if q107.get("symbols") != list(SYMBOLS) or q107.get("common_calendar_count") != 3704:
        raise RuntimeError("Q107_FROZEN_UNIVERSE_MISMATCH")
    if q107.get("scientific_outcome") != "COVERAGE_PASSED_NO_PERFORMANCE_EVIDENCE":
        raise RuntimeError("Q107_SCIENTIFIC_BOUNDARY_MISMATCH")
    manifest = read_json(Q107_MANIFEST_PATH)
    if manifest.get("status") != "COVERAGE_PASSED" or manifest.get("snapshot_fingerprint") != PINNED["q107_snapshot_fingerprint"]:
        raise RuntimeError("Q107_MANIFEST_NOT_FROZEN_POSITIVE")
    if manifest.get("symbols") != list(SYMBOLS) or manifest.get("universe") != UNIVERSE:
        raise RuntimeError("Q107_MANIFEST_UNIVERSE_MISMATCH")
    if manifest.get("data_snapshot") != q107.get("data_snapshot"):
        raise RuntimeError("Q107_MANIFEST_RECEIPT_SNAPSHOT_MISMATCH")
    validate_q107_policy_flags(q107, manifest)

    q108 = read_json(Q108_PATH)
    verify_self_fingerprint(q108, PINNED["q108_receipt_fingerprint"], "Q108")
    if q108.get("status") != "PIT_INTEGRATION_AUDIT_ONLY":
        raise RuntimeError("Q108_FROZEN_RECEIPT_STATUS_MISMATCH")
    if q108.get("sec_ticker_mapping", {}).get("status") != "VERIFIABLE" or q108.get("sec_ticker_mapping", {}).get("ciks") != FROZEN_CIKS:
        raise RuntimeError("Q108_CIK_MAPPING_MISMATCH")
    issuers, xbrl = q108.get("issuer_submissions", {}), q108.get("issuer_xbrl", {})
    if set(issuers) != set(SYMBOLS) or any(issuers[s].get("status") != "VERIFIABLE" for s in SYMBOLS):
        raise RuntimeError("Q108_ISSUER_SUBMISSION_GATE_MISMATCH")
    if set(xbrl) != set(SYMBOLS) or any(xbrl[s].get("status") != "VERIFIABLE" for s in SYMBOLS):
        raise RuntimeError("Q108_XBRL_GATE_MISMATCH")
    if q108.get("sec_13f_sample", {}).get("status") != "VERIFIABLE" or q108.get("treasury", {}).get("status") != "VERIFIABLE":
        raise RuntimeError("Q108_AUXILIARY_SOURCE_GATES_MISMATCH")
    if q108.get("q023_treasury_reuse_check", {}).get("verified") is not True:
        raise RuntimeError("Q108_Q023_REUSE_NOT_VERIFIED")
    mutations = q108.get("synthetic_mutation_tests", {})
    if not mutations or not all(value is True for value in mutations.values()):
        raise RuntimeError("Q108_SYNTHETIC_MUTATION_GATE_MISMATCH")
    q108_gov = q108.get("governance", {})
    if any(q108_gov.get(key) is not False for key in ("new_market_data_for_performance", "new_backtest", "performance_evaluation", "holdout_selection", "candidate_selection", "candidate_ranking", "parameter_search", "threshold_search", "horizon_search", "performance_authorization", "automatic_promotion")):
        raise RuntimeError("Q108_GOVERNANCE_GATE_MISMATCH")
    q108_safe = q108.get("safety", {})
    if q108_safe.get("paper_only") is not True or q108_safe.get("live_trading_enabled") is not False or q108_safe.get("orders_enabled") is not False:
        raise RuntimeError("Q108_SAFETY_GATE_MISMATCH")

    prereg = read_json(PREREG_PATH)
    expected = {
        "candidate_id": "Q104:I22",
        "status": "PREREGISTERED_PRE_PERFORMANCE_COMPILER",
        "fixed_forms": sorted(FORMS),
        "study_window": {"start": START.isoformat(), "end": END.isoformat()},
        "public_availability_anchor": "SEC acceptanceDateTime",
        "eligible_session_rule": "first XNYS session whose session_date is strictly after the acceptanceDateTime calendar date",
        "arrival_density_window": WINDOW,
    }
    for key, value in expected.items():
        actual = sorted(prereg.get(key, [])) if key == "fixed_forms" else prereg.get(key)
        if actual != value:
            raise RuntimeError(f"I22_PREREG_CONTRACT_MISMATCH:{key}")
    if any(prereg.get("governance", {}).get(key) is not False for key in ("performance", "holdout", "selection", "ranking", "parameter_search", "asset_search", "threshold_search", "performance_authorized", "automatic_promotion")):
        raise RuntimeError("I22_PREREG_GOVERNANCE_GATE_MISMATCH")
    if prereg.get("safety", {}).get("paper_only") is not True or prereg.get("safety", {}).get("live_trading_enabled") is not False:
        raise RuntimeError("I22_PREREG_SAFETY_GATE_MISMATCH")
    return {"reconciliation": recon, "q107": q107, "manifest": manifest, "q108": q108}


def dataset_fingerprint_from_rows(rows: list[dict[str, str]]) -> str:
    canonical = []
    for row in rows:
        stamp = datetime.fromisoformat(row["timestamp"])
        if stamp.tzinfo is None:
            raise RuntimeError("Q107_TIMESTAMP_MISSING_TIMEZONE")
        canonical.append({
            "timestamp": stamp.isoformat(),
            "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"]),
            "volume": float(row["volume"]),
        })
    return sha256_bytes(json.dumps(canonical, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))


def verify_frozen_market_data(q107: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    evidence = {item["symbol"]: item for item in q107["data_snapshot"]["datasets"]}
    frozen = {item["symbol"]: item for item in manifest["data_snapshot"]["datasets"]}
    if set(evidence) != set(SYMBOLS) or set(frozen) != set(SYMBOLS):
        raise RuntimeError("Q107_DATASET_SYMBOL_SET_MISMATCH")
    timestamps_ref = None
    checked = {}
    for symbol in SYMBOLS:
        left, right = evidence[symbol], frozen[symbol]
        for key in ("path", "interval", "candle_count", "fingerprint"):
            if left.get(key) != right.get(key):
                raise RuntimeError(f"Q107_DATASET_MANIFEST_MISMATCH:{symbol}:{key}")
        if right.get("interval") != "1d" or right.get("candle_count") != 3500:
            raise RuntimeError(f"Q107_DATASET_GEOMETRY_MISMATCH:{symbol}")
        path = ROOT / str(right["path"]).replace("\\", "/")
        if not path.is_file():
            raise RuntimeError(f"Q107_FROZEN_CSV_MISSING:{symbol}")
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != ("timestamp", "open", "high", "low", "close", "volume"):
                raise RuntimeError(f"Q107_CSV_HEADER_MISMATCH:{symbol}")
            rows = list(reader)
        if len(rows) != 3500:
            raise RuntimeError(f"Q107_CSV_ROW_COUNT_MISMATCH:{symbol}")
        stamps = [row["timestamp"] for row in rows]
        parsed = [datetime.fromisoformat(value) for value in stamps]
        if any(value.tzinfo is None for value in parsed) or stamps != [value.isoformat() for value in parsed]:
            raise RuntimeError(f"Q107_TIMESTAMP_CANONICALIZATION_MISMATCH:{symbol}")
        if parsed != sorted(parsed) or len(stamps) != len(set(stamps)):
            raise RuntimeError(f"Q107_TIMESTAMP_ORDER_MISMATCH:{symbol}")
        if any(value.date() < START or value.date() > END for value in parsed):
            raise RuntimeError(f"Q107_TIMESTAMP_OUTSIDE_FIXED_WINDOW:{symbol}")
        actual = dataset_fingerprint_from_rows(rows)
        if actual != right.get("fingerprint"):
            raise RuntimeError(f"Q107_DATASET_FINGERPRINT_MISMATCH:{symbol}")
        if timestamps_ref is None:
            timestamps_ref = stamps
        elif stamps != timestamps_ref:
            raise RuntimeError(f"Q107_COMMON_CALENDAR_MISMATCH:{symbol}")
        checked[symbol] = {
            "candle_count": len(rows), "dataset_fingerprint": actual,
            "first_timestamp": stamps[0], "last_timestamp": stamps[-1],
        }
    if timestamps_ref is None:
        raise RuntimeError("Q107_EMPTY_FROZEN_SNAPSHOT")
    if timestamps_ref[0] != manifest.get("selected_common_calendar_start") or timestamps_ref[-1] != manifest.get("selected_common_calendar_end"):
        raise RuntimeError("Q107_COMMON_CALENDAR_BOUNDARY_MISMATCH")
    return {
        "status": "Q107_FROZEN_CSVS_VERIFIED",
        "symbol_count": len(checked), "common_timestamp_count": len(timestamps_ref),
        "selected_start": timestamps_ref[0], "selected_end": timestamps_ref[-1],
        "datasets": checked,
    }


def audit_registered_universe() -> dict[str, Any]:
    universes = list_universes()
    exact = [row for row in universes if row.name == UNIVERSE]
    if len(exact) != 1 or tuple(exact[0].symbols) != SYMBOLS:
        raise RuntimeError("Q107_REGISTERED_UNIVERSE_CONTRACT_MISMATCH")
    overlaps = []
    for row in universes:
        if row.name == UNIVERSE:
            continue
        shared = sorted(set(row.symbols).intersection(SYMBOLS))
        if shared:
            overlaps.append({"universe": row.name, "symbols": shared})
    return {
        "status": "Q107_REGISTERED_UNIVERSE_SYMBOL_DISJOINT" if not overlaps else "Q107_REGISTERED_UNIVERSE_OVERLAP_FOUND",
        "registered_universe_count": len(universes),
        "peer_universe_count": len(universes) - 1,
        "overlaps": overlaps,
        "non_overlap_proven": not overlaps,
    }


def audit_candidate_mechanism_overlap() -> dict[str, Any]:
    inventory = candidate_inventory()
    if "Q104:I22" not in inventory:
        raise RuntimeError("I22_CANDIDATE_MISSING_FROM_OVERLAP_INVENTORY")
    relation_contract = read_json(ROOT / "research/governance/knowledge_relation_graph_contract_2026_10_06.json")
    links: dict[str, set[str]] = {}
    for item in relation_contract.get("candidate_component_links", []):
        if isinstance(item, dict) and item.get("candidate") and item.get("component"):
            links.setdefault(str(item["candidate"]), set()).add(str(item["component"]))
    signatures = {
        candidate_id: candidate_signature(spec, {candidate_id: links.get(candidate_id, set())})
        for candidate_id, spec in inventory.items()
    }
    base = signatures["Q104:I22"]
    comparisons = []
    for peer_id, peer_sig in signatures.items():
        if peer_id == "Q104:I22":
            continue
        result = compare_signatures(base, peer_sig)
        similarities = result["similarities"]
        comparisons.append({
            "peer": peer_id,
            "signature_coverage_complete": result["signature_coverage_complete"],
            "observed_dimensions": result["observed_dimensions"],
            "missing_dimensions": [key for key, value in similarities.items() if value is None],
            "complete_score": round(result["score"], 6) if result["signature_coverage_complete"] and result["score"] is not None else None,
            "token_jaccard": round(similarities["tokens"], 6) if similarities["tokens"] is not None else None,
            "component_jaccard": round(similarities["components"], 6) if similarities["components"] is not None else None,
            "domain_jaccard": round(similarities["source_domains"], 6) if similarities["source_domains"] is not None else None,
        })
    complete = sum(row["signature_coverage_complete"] for row in comparisons)
    incomplete = len(comparisons) - complete
    comparisons.sort(key=lambda row: row["peer"])
    non_overlap_proven = bool(
        comparisons and incomplete == 0
        and all(row["complete_score"] is not None and row["complete_score"] < 0.45 for row in comparisons)
    )
    return {
        "status": "I22_MECHANISM_SIGNATURE_NON_OVERLAP_REVIEW_REQUIRED" if not non_overlap_proven else "I22_SIGNATURE_AUDIT_COMPLETE_REVIEW_ONLY",
        "candidate_count": len(inventory),
        "peer_comparison_count": len(comparisons),
        "complete_comparison_count": complete,
        "incomplete_comparison_count": incomplete,
        "dimensions": ["mechanism_tokens", "source_components", "source_domains"],
        "candidate_metadata": {
            "mechanism_token_count": len(base["tokens"]),
            "source_component_count": len(base["components"]),
            "source_domain_count": len(base["source_domains"]),
        },
        "non_overlap_proven": non_overlap_proven,
        "comparisons": comparisons,
        "note": "Partial signatures cannot establish orthogonality. Review only; no performance authority.",
    }


def values(container: Any, field: str) -> list[Any]:
    value = container.get(field, []) if isinstance(container, dict) else []
    return value if isinstance(value, list) else []


def columnar_rows(container: dict[str, Any], filter_window: bool) -> list[dict[str, Any]]:
    forms = container.get("form", [])
    if not isinstance(forms, list):
        raise RuntimeError("SEC_FORM_ARRAY_INVALID")
    rows = []
    for index in range(len(forms)):
        filing_date = str(container.get("filingDate", [])[index] or "") if index < len(container.get("filingDate", [])) else ""
        if filter_window and not (START.isoformat() <= filing_date <= END.isoformat()):
            continue
        acceptance_rows = container.get("acceptanceDateTime", [])
        accession_rows = container.get("accessionNumber", [])
        rows.append({
            "form": forms[index],
            "filingDate": filing_date,
            "acceptanceDateTime": acceptance_rows[index] if isinstance(acceptance_rows, list) and index < len(acceptance_rows) else None,
            "accessionNumber": str(accession_rows[index] or "") if isinstance(accession_rows, list) and index < len(accession_rows) else "",
        })
    return rows


def fetch_sec_json(url: str, budget: dict[str, Any]) -> dict[str, Any]:
    if budget["request_count"] >= MAX_REQUESTS:
        raise RuntimeError("SEC_REQUEST_BUDGET_EXCEEDED")
    remaining = MAX_TOTAL_BYTES - budget["total_bytes"]
    if remaining <= 0:
        raise RuntimeError("SEC_TOTAL_DOWNLOAD_BUDGET_EXCEEDED")
    byte_limit = min(MAX_RESPONSE_BYTES, remaining)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            if int(response.status) != 200:
                raise RuntimeError(f"SEC_HTTP_STATUS:{response.status}:{url}")
            body = response.read(byte_limit + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"SEC_HTTP_STATUS:{exc.code}:{url}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"SEC_REQUEST_FAILED:{url}:{type(exc).__name__}") from exc
    if len(body) > byte_limit:
        reason = "SEC_TOTAL_DOWNLOAD_BUDGET_EXCEEDED" if remaining < MAX_RESPONSE_BYTES else "SEC_RESPONSE_LIMIT_EXCEEDED"
        raise RuntimeError(f"{reason}:{url}")
    budget["request_count"] += 1
    budget["total_bytes"] += len(body)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"SEC_RESPONSE_NOT_JSON:{url}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"SEC_RESPONSE_NOT_OBJECT:{url}")
    budget["responses"].append({"url": url, "http_status": 200, "bytes": len(body), "sha256": sha256_bytes(body)})
    return payload


def fetch_issuer_rows(symbol: str, cik: int, budget: dict[str, Any]) -> list[dict[str, Any]]:
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    payload = fetch_sec_json(url, budget)
    filings = payload.get("filings", {})
    if not isinstance(filings, dict):
        raise RuntimeError(f"SEC_FILINGS_INVALID:{symbol}")
    rows = columnar_rows(filings.get("recent", {}), filter_window=False)
    archives = values(filings, "files")
    for extension in archives:
        if not isinstance(extension, dict):
            continue
        name = extension.get("name")
        if not name:
            continue
        filing_from = str(extension.get("filingFrom") or "")
        filing_to = str(extension.get("filingTo") or "")
        if filing_to and filing_to < START.isoformat():
            continue
        if filing_from and filing_from > END.isoformat():
            continue
        archive_url = "https://data.sec.gov/submissions/" + str(name)
        archive = fetch_sec_json(archive_url, budget)
        rows.extend(columnar_rows(archive, filter_window=True))

    # Prefer the complete, earliest public timestamp when an accession appears
    # in both the recent and historical arrays; keep amendments as own accessions.
    by_accession: dict[str, dict[str, Any]] = {}
    for row in rows:
        accession = str(row.get("accessionNumber") or "")
        if not accession:
            continue
        old = by_accession.get(accession)
        new_time = str(row.get("acceptanceDateTime") or "")
        old_time = str(old.get("acceptanceDateTime") or "") if old else ""
        if old is None or (new_time and not old_time) or (new_time and old_time and new_time < old_time):
            by_accession[accession] = row
    return list(by_accession.values())


def parse_utc(value: str) -> datetime:
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise RuntimeError("SEC_ACCEPTANCE_TIMESTAMP_IS_NAIVE")
    return stamp.astimezone(timezone.utc)


def next_xnys_session(after_date: date) -> date:
    sessions = CAL.sessions_in_range((after_date + timedelta(days=1)).isoformat(), (after_date + timedelta(days=10)).isoformat())
    if len(sessions) == 0:
        raise RuntimeError(f"XNYS_NEXT_SESSION_NOT_FOUND:{after_date.isoformat()}")
    return sessions[0].date()


def compile_population(rows: list[dict[str, Any]], cutoff: date = END) -> dict[str, Any]:
    events = []
    for row in rows:
        if row.get("form") not in FORMS or not row.get("acceptanceDateTime") or not row.get("accessionNumber"):
            continue
        accepted = parse_utc(str(row["acceptanceDateTime"]))
        if accepted.date() < START or accepted.date() > cutoff:
            continue
        eligible = next_xnys_session(accepted.date())
        if eligible > cutoff:
            continue
        events.append({
            "form": row["form"], "accession": str(row["accessionNumber"]),
            "filing_date": str(row.get("filingDate", "")),
            "acceptance_datetime": accepted.isoformat(), "eligible_session": eligible.isoformat(),
        })
    events.sort(key=lambda item: (item["acceptance_datetime"], item["accession"], item["form"]))
    event_sessions = sorted({date.fromisoformat(item["eligible_session"]) for item in events})
    per_session = {session: [] for session in event_sessions}
    for event in events:
        per_session[date.fromisoformat(event["eligible_session"])].append(event)
    sessions = [stamp.date() for stamp in CAL.sessions_in_range(START.isoformat(), cutoff.isoformat())]
    density = []
    for index, session in enumerate(sessions):
        window_sessions = sessions[max(0, index - WINDOW + 1):index + 1]
        density.append({
            "decision_session": session.isoformat(),
            "arrival_count_20": sum(len(per_session.get(day, [])) for day in window_sessions),
            "window_session_count": len(window_sessions),
        })
    return {
        "filing_count": len(events),
        "eligible_session_count": len(event_sessions),
        "decision_session_count": len(sessions),
        "first_acceptance": events[0]["acceptance_datetime"] if events else None,
        "last_acceptance": events[-1]["acceptance_datetime"] if events else None,
        "events": events,
        "arrival_density_20": density,
    }


def reference_prefix(reference: dict[str, Any], cutoff: date) -> dict[str, Any]:
    events = [
        event for event in reference["events"]
        if date.fromisoformat(event["acceptance_datetime"][:10]) <= cutoff
        and date.fromisoformat(event["eligible_session"]) <= cutoff
    ]
    events.sort(key=lambda item: (item["acceptance_datetime"], item["accession"], item["form"]))
    event_sessions = sorted({item["eligible_session"] for item in events})
    density = [row for row in reference["arrival_density_20"] if date.fromisoformat(row["decision_session"]) <= cutoff]
    return {
        "filing_count": len(events),
        "eligible_session_count": len(event_sessions),
        "decision_session_count": len(density),
        "first_acceptance": events[0]["acceptance_datetime"] if events else None,
        "last_acceptance": events[-1]["acceptance_datetime"] if events else None,
        "events": events,
        "arrival_density_20": density,
    }


def verify_compiler_artifact(payload: dict[str, Any], expected_fp: str, label: str) -> None:
    verify_self_fingerprint(payload, expected_fp, label)
    if payload.get("task_id") != "Q-2026-10-01-104-I22-FILING-ARRIVAL" or payload.get("status") != "I22_PIT_COMPILER_COMPLETED":
        raise RuntimeError(f"{label}_TASK_OR_STATUS_MISMATCH")
    if payload.get("symbols") != list(SYMBOLS) or payload.get("study_window") != {"start": START.isoformat(), "end": END.isoformat()}:
        raise RuntimeError(f"{label}_UNIVERSE_OR_WINDOW_MISMATCH")
    if payload.get("arrival_density_window") != WINDOW or payload.get("fixed_forms") != sorted(FORMS):
        raise RuntimeError(f"{label}_CONTRACT_MISMATCH")
    expected_ciks = {symbol: f"{FROZEN_CIKS[symbol]:010d}" for symbol in SYMBOLS}
    if payload.get("issuer_ciks") != expected_ciks or set(payload.get("issuer_results", {})) != set(SYMBOLS):
        raise RuntimeError(f"{label}_CIK_OR_ISSUER_SET_MISMATCH")
    if not payload.get("mutation_tests") or not all(value is True for value in payload["mutation_tests"].values()):
        raise RuntimeError(f"{label}_MUTATION_TESTS_NOT_POSITIVE")
    gov, safe = payload.get("governance", {}), payload.get("safety", {})
    if any(gov.get(key) is not False for key in ("performance", "holdout", "selection", "ranking", "parameter_search", "asset_search", "threshold_search", "performance_authorized", "automatic_promotion")):
        raise RuntimeError(f"{label}_GOVERNANCE_GATE_MISMATCH")
    if safe.get("paper_only") is not True or safe.get("live_trading_enabled") is not False or safe.get("orders_enabled") is not False:
        raise RuntimeError(f"{label}_SAFETY_GATE_MISMATCH")


def compare_architectures(x64: dict[str, Any], arm64: dict[str, Any]) -> None:
    excluded = {"source_response_fingerprint", "receipt_fingerprint"}
    if {k: v for k, v in x64.items() if k not in excluded} != {k: v for k, v in arm64.items() if k not in excluded}:
        raise RuntimeError("I22_X64_ARM64_SUBSTANTIVE_RESULT_MISMATCH")
    if x64.get("source_response_fingerprint") != PINNED_SOURCE_FP_X64:
        raise RuntimeError("I22_X64_SOURCE_FP_MISMATCH")
    if arm64.get("source_response_fingerprint") != PINNED_SOURCE_FP_ARM64:
        raise RuntimeError("I22_ARM64_SOURCE_FP_MISMATCH")


def run_reproduction(
    x64_path: Path,
    arm64_path: Path,
    budget: dict[str, Any],
    reproduction_code_sha: str,
) -> dict[str, Any]:
    frozen = verify_frozen_contracts()
    market_data = verify_frozen_market_data(frozen["q107"], frozen["manifest"])
    registered = audit_registered_universe()
    if registered["status"] != "Q107_REGISTERED_UNIVERSE_SYMBOL_DISJOINT":
        raise RuntimeError("Q107_REGISTERED_UNIVERSE_NON_OVERLAP_FAILED")
    x64, arm64 = read_json(x64_path), read_json(arm64_path)
    verify_compiler_artifact(x64, frozen["reconciliation"]["x64_receipt_fingerprint"], "I22_X64_ARTIFACT")
    verify_compiler_artifact(arm64, frozen["reconciliation"]["arm64_receipt_fingerprint"], "I22_ARM64_ARTIFACT")
    compare_architectures(x64, arm64)

    independent, prefixes, order_checks, future_checks = {}, {}, {}, {}
    for symbol in SYMBOLS:
        raw_rows = fetch_issuer_rows(symbol, FROZEN_CIKS[symbol], budget)
        rebuilt = compile_population(raw_rows, END)
        expected = x64["issuer_results"][symbol]
        if rebuilt != expected:
            raise RuntimeError(f"I22_INDEPENDENT_SOURCE_RESULT_MISMATCH:{symbol}")
        independent[symbol] = rebuilt

        for cutoff in (date(2015, 12, 31), date(2020, 12, 31), END):
            prefix = compile_population(raw_rows, cutoff)
            if prefix != reference_prefix(expected, cutoff):
                raise RuntimeError(f"I22_PREFIX_REPRODUCTION_MISMATCH:{symbol}:{cutoff.isoformat()}")
            prefixes[f"{symbol}:{cutoff.isoformat()}"] = {
                "status": "PASS", "filing_count": prefix["filing_count"],
                "eligible_session_count": prefix["eligible_session_count"],
                "decision_session_count": prefix["decision_session_count"],
            }

        if compile_population(list(reversed(raw_rows)), END) != rebuilt:
            raise RuntimeError(f"I22_INPUT_ORDER_INVARIANCE_FAILED:{symbol}")
        order_checks[symbol] = True

        cutoff = date(2020, 12, 31)
        baseline = compile_population(raw_rows, cutoff)
        future = {
            "form": "8-K", "filingDate": "2021-01-04",
            "acceptanceDateTime": "2021-01-04T12:00:00Z",
            "accessionNumber": f"FUTURE-MUTATION-{symbol}",
        }
        if compile_population(raw_rows + [future], cutoff) != baseline:
            raise RuntimeError(f"I22_FUTURE_ACCEPTANCE_INVARIANCE_FAILED:{symbol}")
        future_checks[symbol] = True
        accession_ids = [event["accession"] for event in rebuilt["events"]]
        if len(accession_ids) != len(set(accession_ids)):
            raise RuntimeError(f"I22_DUPLICATE_ACCESSION:{symbol}")

    total_filings = sum(row["filing_count"] for row in independent.values())
    if total_filings != 2209 or total_filings != sum(row["filing_count"] for row in x64["issuer_results"].values()):
        raise RuntimeError("I22_TOTAL_FILING_COUNT_MISMATCH")
    amendments = sum(
        event["form"].endswith("/A")
        for result in independent.values() for event in result["events"]
    )
    if amendments < 1:
        raise RuntimeError("I22_AMENDMENT_LINEAGE_NOT_OBSERVED")

    mechanism_overlap = audit_candidate_mechanism_overlap()
    if budget["request_count"] > MAX_REQUESTS or budget["total_bytes"] > MAX_TOTAL_BYTES:
        raise RuntimeError("SEC_REQUEST_BUDGET_POSTCONDITION_FAILED")
    return {
        "schema_version": "1.0",
        "record_type": "q104_i22_independent_pit_reproduction",
        "task_id": "Q-2026-10-12-104-I22-INDEPENDENT-PIT",
        "candidate_id": "Q104:I22",
        "reproduction_code_sha": reproduction_code_sha,
        "status": "Q104_I22_INDEPENDENT_PIT_REPRODUCED_NON_OVERLAP_REVIEW_REQUIRED" if not mechanism_overlap["non_overlap_proven"] else "Q104_I22_INDEPENDENT_PIT_REPRODUCED_REVIEW_ONLY",
        "validation_outcome": "INDEPENDENT_PIT_REPRODUCED",
        "upstream_inputs": {
            "source_workflow_run_id": PINNED["source_workflow_run_id"],
            "source_master_sha": PINNED["source_master_sha"],
            "reconciliation_receipt_fingerprint": PINNED["reconciliation_fingerprint"],
            "q107_coverage_fingerprint": PINNED["q107_coverage_fingerprint"],
            "q107_snapshot_fingerprint": PINNED["q107_snapshot_fingerprint"],
            "q108_receipt_fingerprint": PINNED["q108_receipt_fingerprint"],
            "preregistration": PREREG_PATH.relative_to(ROOT).as_posix(),
        },
        "frozen_market_data": market_data,
        "registered_universe_non_overlap": registered,
        "compiler_reproduction": {
            "x64_receipt_fingerprint": x64["receipt_fingerprint"],
            "arm64_receipt_fingerprint": arm64["receipt_fingerprint"],
            "x64_arm64_semantic_equality": True,
            "independent_source_refetch_semantic_equality": True,
            "independent_filing_count": total_filings,
            "eligible_issuer_session_sum": sum(row["eligible_session_count"] for row in independent.values()),
            "per_symbol_filing_counts": {symbol: independent[symbol]["filing_count"] for symbol in SYMBOLS},
            "per_symbol_eligible_sessions": {symbol: independent[symbol]["eligible_session_count"] for symbol in SYMBOLS},
            "amendment_accession_events": amendments,
            "accessions_unique_within_symbol": True,
            "raw_source_response_hashes": budget["responses"],
            "request_count": budget["request_count"],
            "downloaded_bytes": budget["total_bytes"],
            "resource_limits": {
                "max_requests": MAX_REQUESTS, "max_response_bytes": MAX_RESPONSE_BYTES,
                "max_total_bytes": MAX_TOTAL_BYTES, "timeout_seconds": TIMEOUT_SECONDS,
            },
        },
        "pit_invariance_checks": {
            "prefix_reproductions": prefixes, "input_order_invariance": order_checks,
            "future_acceptance_invariance": future_checks, "all_passed": True,
        },
        "mechanism_non_overlap": mechanism_overlap,
        "next_gate": "review candidate-specific mechanism signature completeness; do not authorize performance",
        "governance": {
            "new_market_data_for_performance": False, "backtest": False,
            "performance_evaluation": False, "holdout_selection": False,
            "candidate_selection": False, "candidate_ranking": False,
            "parameter_search": False, "threshold_search": False,
            "horizon_search": False, "performance_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True, "live_trading_enabled": False,
            "orders_enabled": False, "automatic_promotion": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--x64-result", type=Path, required=True)
    parser.add_argument("--arm64-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--reproduction-code-sha",
        type=validate_reproduction_code_sha,
        required=True,
        help="Full commit SHA of the exact checked-out reproduction code.",
    )
    args = parser.parse_args()
    budget: dict[str, Any] = {"request_count": 0, "total_bytes": 0, "responses": []}
    try:
        result, code = run_reproduction(
            args.x64_result, args.arm64_result, budget, args.reproduction_code_sha
        ), 0
    except Exception as exc:
        result, code = {
            "schema_version": "1.0",
            "record_type": "q104_i22_independent_pit_reproduction",
            "task_id": "Q-2026-10-12-104-I22-INDEPENDENT-PIT",
            "candidate_id": "Q104:I22",
            "reproduction_code_sha": args.reproduction_code_sha,
            "status": "Q104_I22_INDEPENDENT_PIT_BLOCKED",
            "validation_outcome": "BLOCKED_FAIL_CLOSED",
            "block_reason": f"{type(exc).__name__}:{str(exc)[:1200]}",
            "upstream_inputs": PINNED,
            "partial_source_probes": {
                "request_count": budget["request_count"],
                "downloaded_bytes": budget["total_bytes"],
                "responses": budget["responses"],
            },
            "governance": {
                "new_market_data_for_performance": False, "backtest": False,
                "performance_evaluation": False, "holdout_selection": False,
                "candidate_selection": False, "candidate_ranking": False,
                "parameter_search": False, "threshold_search": False,
                "horizon_search": False, "performance_authorized": False,
                "automatic_promotion": False,
            },
            "safety": {
                "paper_only": True, "live_trading_enabled": False,
                "orders_enabled": False, "automatic_promotion": False,
            },
        }, 1
    result["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["receipt_fingerprint"] = receipt_fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "validation_outcome": result["validation_outcome"],
        "receipt_fingerprint": result["receipt_fingerprint"],
        "request_count": budget["request_count"], "downloaded_bytes": budget["total_bytes"],
        "block_reason": result.get("block_reason"),
    }, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
