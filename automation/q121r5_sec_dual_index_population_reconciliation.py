"""Q121-R5: dual SEC quarterly-index population reconciliation.

Source/PIT only. No prices, returns, holdout selection, ranking, tuning,
promotion or live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from automation.q121r3_sec_form_index_reverse_issuer import (
    FORM_SET as R3_FORM_SET,
    QUARTERS as R3_QUARTERS,
    accession_from_filename as r3_accession_from_filename,
    fetch_logical_form_index,
    parse_index,
    within_window,
)
from automation.q121r4_sec_master_index_reverse_issuer import (
    QUARTERS as R4_QUARTERS,
    accession_from_filename as r4_accession_from_filename,
    fetch_master,
    parse_master,
)

START = "2024-02-05"
END = "2025-09-24"
FORM_SET = {"SC 13D", "SC 13G", "SC 13D/A", "SC 13G/A"}
KEY_FIELDS = ("cik", "form", "filed_date", "accession_number")


def canonical_keys(rows, accession_fn):
    out = Counter()
    for row in rows:
        out[(row["cik"], row["form"], row["filed_date"], accession_fn(row["filename"]))] += 1
    return out


def counter_fingerprint(counter):
    payload = [[list(key), count] for key, count in sorted(counter.items())]
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def run(output: Path):
    if R3_QUARTERS != R4_QUARTERS:
        raise RuntimeError("Q121R5_QUARTER_DEFINITION_DRIFT")
    if R3_FORM_SET != FORM_SET:
        raise RuntimeError("Q121R5_FORM_DEFINITION_DRIFT")

    form_rows, master_rows = [], []
    form_receipts, master_receipts = [], []

    for year, quarter in R3_QUARTERS:
        body, transport = fetch_logical_form_index(year, quarter)
        parsed = [r for r in parse_index(body) if r["form"] in FORM_SET and within_window(r["filed_date"])]
        form_rows.extend(parsed)
        form_receipts.append({"year": year, "quarter": quarter, **transport, "matching_rows": len(parsed)})

    for year, quarter in R4_QUARTERS:
        body, transport = fetch_master(year, quarter)
        parsed = [r for r in parse_master(body) if r["form"] in FORM_SET and within_window(r["filed_date"])]
        master_rows.extend(parsed)
        master_receipts.append({"year": year, "quarter": quarter, **transport, "matching_rows": len(parsed)})

    left = canonical_keys(form_rows, r3_accession_from_filename)
    right = canonical_keys(master_rows, r4_accession_from_filename)
    left_only, right_only = left - right, right - left
    exact_equal = left == right

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-121R5-SEC-DUAL-INDEX-POPULATION-RECONCILIATION",
        "status": "Q121R5_DUAL_INDEX_POPULATION_RECONCILIATION_COMPLETED" if exact_equal else "Q121R5_DUAL_INDEX_POPULATION_MISMATCH",
        "window": {"start": START, "end": END},
        "forms": sorted(FORM_SET),
        "canonical_key_fields": list(KEY_FIELDS),
        "routes": {
            "form_index": {"route": "SEC_QUARTERLY_FORM_INDEX", "quarters_checked": len(form_receipts),
                           "raw_filtered_rows": len(form_rows), "unique_canonical_keys": len(left),
                           "row_multiset_fingerprint": counter_fingerprint(left), "quarter_receipts": form_receipts},
            "master_index": {"route": "SEC_QUARTERLY_MASTER_INDEX", "quarters_checked": len(master_receipts),
                             "raw_filtered_rows": len(master_rows), "unique_canonical_keys": len(right),
                             "row_multiset_fingerprint": counter_fingerprint(right), "quarter_receipts": master_receipts},
        },
        "comparison": {
            "exact_row_multiset_equal": exact_equal,
            "left_only_key_count": len(left_only), "right_only_key_count": len(right_only),
            "left_only_row_count": sum(left_only.values()), "right_only_row_count": sum(right_only.values()),
            "sample_left_only": [[list(k), v] for k, v in sorted(left_only.items())[:10]],
            "sample_right_only": [[list(k), v] for k, v in sorted(right_only.items())[:10]],
        },
        "interpretation": {
            "dual_index_population_equivalence": exact_equal,
            "full_subject_issuer_population_compiled": False,
            "acceptance_timestamps_compiled": False,
            "same_day_pit_safe": False,
            "revision_lineage_established": False,
        },
        "governance": {k: False for k in (
            "performance", "holdout", "selection", "ranking", "parameter_search",
            "threshold_search", "horizon_search", "asset_search", "variant_search",
            "performance_authorized", "automatic_promotion")},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    result = run(p.parse_args().output)
    print(json.dumps({
        "status": result["status"],
        "form_rows": result["routes"]["form_index"]["raw_filtered_rows"],
        "master_rows": result["routes"]["master_index"]["raw_filtered_rows"],
        "equal": result["comparison"]["exact_row_multiset_equal"],
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
