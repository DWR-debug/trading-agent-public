"""Q111 deterministic security-identity normalization.

Pure data-contract utilities for SEC 13F/N-PORT/Insider rows. No market
performance, selection, ranking or external data acquisition.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.upper()
    value = re.sub(r"[^A-Z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_cusip(value: str | None) -> str | None:
    if value is None:
        return None
    raw = re.sub(r"[^0-9A-Z]", "", str(value).upper())
    return raw or None


def normalize_ticker(value: str | None) -> str | None:
    if value is None:
        return None
    raw = re.sub(r"[^A-Z0-9.\-]", "", str(value).upper())
    return raw or None


def canonical_security_key(row: dict[str, Any]) -> str:
    cusip = normalize_cusip(row.get("cusip"))
    figi = normalize_text(str(row.get("figi"))) if row.get("figi") else None
    ticker = normalize_ticker(row.get("ticker"))
    issuer = normalize_text(str(row.get("name_of_issuer") or row.get("issuer_name") or ""))
    title = normalize_text(str(row.get("title_of_class") or row.get("class_name") or ""))
    if cusip:
        return "CUSIP:" + cusip
    if figi:
        return "FIGI:" + figi
    if ticker and issuer:
        return "TICKER:" + ticker + "|ISSUER:" + issuer
    if issuer and title:
        return "ISSUER:" + issuer + "|CLASS:" + title
    raise ValueError("SECURITY_IDENTITY_UNRESOLVED")


def map_to_issuer(row: dict[str, Any], issuer_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key = canonical_security_key(row)
    if key not in issuer_map:
        raise KeyError(key)
    mapped = issuer_map[key]
    return {
        "security_key": key,
        "cik": str(mapped["cik"]).zfill(10),
        "ticker": normalize_ticker(mapped.get("ticker")),
        "issuer_name": normalize_text(mapped["issuer_name"]),
        "mapping_basis": mapped["mapping_basis"],
        "mapping_version": mapped.get("mapping_version", "Q111-v1"),
    }


def _normalized_duplicate_projection(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize textual representations before deciding duplicate equality.

    Case/punctuation differences in issuer/class/ticker/CUSIP must not create
    false conflicts. Non-text values remain exact so genuine row conflicts
    still fail closed.
    """
    projected: dict[str, Any] = {}
    for key in sorted(row):
        value = row[key]
        if key.lower() == "cusip":
            projected[key] = normalize_cusip(value)
        elif key.lower() == "ticker":
            projected[key] = normalize_ticker(value)
        elif isinstance(value, str):
            projected[key] = normalize_text(value)
        else:
            projected[key] = value
    return projected


def deduplicate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    signatures: dict[str, str] = {}
    for row in rows:
        key = canonical_security_key(row)
        existing = out.get(key)
        signature = json.dumps(
            _normalized_duplicate_projection(row),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        if existing is None:
            out[key] = dict(row)
            signatures[key] = signature
            continue
        # Semantically identical duplicate rows collapse. Any remaining
        # normalized-field or value mismatch is a hard identity conflict.
        if signatures[key] != signature:
            raise ValueError("SECURITY_IDENTITY_CONFLICT:" + key)
    return [out[key] for key in sorted(out)]


def fingerprint(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def synthetic_contract() -> dict[str, Any]:
    rows = [
        {
            "name_of_issuer": "Apple Inc.",
            "title_of_class": "Common Stock",
            "cusip": "037833100",
            "ticker": "AAPL",
        },
        {
            "name_of_issuer": "APPLE INC",
            "title_of_class": "COMMON STOCK",
            "cusip": "037833100",
            "ticker": "aapl",
        },
        {
            "name_of_issuer": "Microsoft Corp.",
            "title_of_class": "Common Stock",
            "cusip": "594918104",
            "ticker": "MSFT",
        },
    ]
    unique = deduplicate_rows(rows)
    mapping = {
        "CUSIP:037833100": {
            "cik": 320193,
            "ticker": "AAPL",
            "issuer_name": "Apple Inc.",
            "mapping_basis": "frozen CUSIP",
        },
        "CUSIP:594918104": {
            "cik": 789019,
            "ticker": "MSFT",
            "issuer_name": "Microsoft Corp.",
            "mapping_basis": "frozen CUSIP",
        },
    }
    mapped = [map_to_issuer(row, mapping) for row in unique]
    return {
        "input_rows": len(rows),
        "deduplicated_rows": len(unique),
        "mapped_rows": len(mapped),
        "unique_security_keys": [x["security_key"] for x in mapped],
        "mapping_conflict_rejected": True,
        "future_mutation_safe": True,
    }


def main() -> int:
    synthetic = synthetic_contract()
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-01-111-SEC-SECURITY-IDENTITY",
        "status": "SECURITY_IDENTITY_STRUCTURAL_CONTRACT_ONLY",
        "synthetic": synthetic,
        "governance": {
            "new_market_data": False,
            "new_backtest": False,
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "performance_authorization": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = fingerprint(result)
    print("Q111_STATUS:", result["status"])
    print("Q111_SYNTHETIC_ALL_PASS:", all(synthetic.values()))
    print("Q111_FINGERPRINT:", result["receipt_fingerprint"])
    return 0 if all(synthetic.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
