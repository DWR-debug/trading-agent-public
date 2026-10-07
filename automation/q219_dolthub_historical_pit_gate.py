"""Q219 DoltHub historical-vintage / PIT feasibility gate.

Source/PIT infrastructure only. Never reads returns or authorizes performance.
The gate separates commit-history observability from true point-in-time
availability by requiring a Dolt commit at or before the fixed historical
observation date.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://www.dolthub.com/api/v1alpha1/post-no-preference/options/master"
TARGET_DATE = "2025-08-01"
TARGET_SYMBOLS = ["AAPL", "AMZN", "DIS", "JPM", "MSFT", "NVDA", "WMT", "XOM"]
HEAD_LOG_LIMIT = 50
BOUNDED_HISTORY_SCAN_LIMIT = 200
UA = "TradingAgent-Public-Q219-DoltHub-PIT-Gate/1.0"
QUERY_TIMEOUT_SECONDS = 90
MAX_TRANSIENT_QUERY_ATTEMPTS = 2
TRANSIENT_QUERY_MARKERS = ("deadline exceeded", "timeout", "timed out")


def fetch_sql(query: str) -> dict:
    params = urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(
        f"{API_BASE}?{params}",
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    last_error = None
    for attempt in range(1, MAX_TRANSIENT_QUERY_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=QUERY_TIMEOUT_SECONDS) as response:
                status = int(getattr(response, "status", 200))
                body = response.read()
            payload = json.loads(body.decode("utf-8", errors="replace"))
            if status != 200:
                raise RuntimeError(f"DOLTHUB_HTTP_{status}")
            if payload.get("query_execution_status") == "Success":
                return payload
            message = str(payload.get("query_execution_message") or "unknown")
            error = RuntimeError("DOLTHUB_QUERY_ERROR:" + message)
            if not any(marker in message.lower() for marker in TRANSIENT_QUERY_MARKERS):
                raise error
            last_error = error
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = RuntimeError(f"DOLTHUB_TRANSPORT_ERROR:{type(exc).__name__}:{exc}")
        if attempt < MAX_TRANSIENT_QUERY_ATTEMPTS:
            time.sleep(2)
    raise last_error or RuntimeError("DOLTHUB_QUERY_ERROR:unknown")


def sha256_json(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def run(output: Path) -> dict:
    history_query = f"""
SELECT commit_hash, date, message
FROM dolt_log
WHERE date <= {repr(TARGET_DATE + " 23:59:59")}
  AND message LIKE 'option_chain % update'
ORDER BY date DESC
LIMIT {HEAD_LOG_LIMIT}
""".strip()
    history_payload = fetch_sql(history_query)
    scanned_rows = history_payload.get("rows") or []
    history_rows = [row for row in scanned_rows if row.get("commit_hash")]
    bounded_dates = [str(row.get("date")) for row in scanned_rows if row.get("date")]
    earliest = min(bounded_dates) if bounded_dates else None
    latest = max(bounded_dates) if bounded_dates else None
    commit_count = len(scanned_rows)

    prior_query = (
        "SELECT commit_hash, date, message FROM dolt_log "
        "WHERE date <= " + repr(TARGET_DATE + " 23:59:59") +
        " ORDER BY date DESC LIMIT 1"
    )
    prior_payload = fetch_sql(prior_query)
    prior_rows = prior_payload.get("rows") or []
    prior_commit = prior_rows[0] if prior_rows else None

    snapshots = []
    if history_rows:
        chosen = []
        if prior_commit:
            chosen.append(prior_commit)
        for row in history_rows:
            if len(chosen) >= 2:
                break
            if not prior_commit or str(row.get("commit_hash")) != str(prior_commit.get("commit_hash")):
                chosen.append(row)
        for row in chosen:
            commit = str(row.get("commit_hash"))
            sample_query = (
                "SELECT date, act_symbol, expiration, strike, call_put, bid, ask, vol "
                "FROM option_chain AS OF "
                + repr(commit)
                + " WHERE date = "
                + repr(TARGET_DATE)
                + " AND act_symbol IN ("
                + ",".join(repr(x) for x in TARGET_SYMBOLS)
                + ") ORDER BY act_symbol, expiration, strike, call_put LIMIT 50"
            )
            payload = fetch_sql(sample_query)
            rows = payload.get("rows") or []
            snapshots.append({
                "commit_hash": commit,
                "commit_date": row.get("date"),
                "commit_message": row.get("message"),
                "query": sample_query,
                "row_count": len(rows),
                "symbol_count": len({str(x.get("act_symbol")) for x in rows}),
                "result_sha256": sha256_json(rows),
            })

    pit_before_target = prior_commit is not None
    result = {
        "schema_version": 1,
        "record_type": "q219_dolthub_historical_pit_gate",
        "candidate_id": "Q219",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "api": API_BASE,
            "owner": "post-no-preference",
            "database": "options",
            "branch": "master",
            "public_http": True,
        },
        "frozen_contract": {
            "target_date": TARGET_DATE,
            "target_symbols": TARGET_SYMBOLS,
            "head_log_limit": HEAD_LOG_LIMIT,
        },
        "query_retry_policy": {
            "timeout_seconds": QUERY_TIMEOUT_SECONDS,
            "max_transient_attempts": MAX_TRANSIENT_QUERY_ATTEMPTS,
            "backoff_seconds": 2,
            "transient_markers": TRANSIENT_QUERY_MARKERS,
        },
        "history": {
            "earliest_commit_date": earliest,
            "latest_commit_date": latest,
            "commit_count_bounded_scan": commit_count,
            "option_chain_update_commits_observed": len(history_rows),
            "commit_log_query": history_query,
            "history_query_surface": "dolt_log_system_table_filtered",
            "bounded_scan_limit": HEAD_LOG_LIMIT,
            "prior_commit_query": prior_query,
            "prior_commit_query_surface": "dolt_log_system_table_filtered",
        },
        "historical_pit": {
            "commit_at_or_before_target_date_observed": pit_before_target,
            "prior_commit": prior_commit,
            "pit_ready": pit_before_target and len(snapshots) >= 2,
        },
        "revision_checks": {
            "as_of_query_supported_on_observed_commits": len(snapshots) >= 2,
            "observed_snapshots": snapshots,
            "historical_result_hashes_available": all(x.get("result_sha256") for x in snapshots),
        },
        "status": (
            "Q219_PIT_SNAPSHOT_READY_FOR_INDEPENDENT_REPRODUCTION"
            if pit_before_target and len(snapshots) >= 2
            else "Q219_SOURCE_HISTORY_OBSERVED_BUT_HISTORICAL_PIT_SNAPSHOT_UNPROVEN"
        ),
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {
            "PAPER_ONLY": True,
            "LIVE_TRADING_ENABLED": False,
            "ORDERS_ENABLED": False,
            "AUTOMATIC_PROMOTION": False,
        },
    }
    result["receipt_fingerprint"] = sha256_json(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "earliest_commit_date": earliest,
        "latest_commit_date": latest,
        "commit_at_or_before_target_date_observed": pit_before_target,
        "observed_snapshots": len(snapshots),
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.output)
