"""Independent Q129 structural/PIT reproduction for the pinned public options release.

This is a data-contract reproduction only. It intentionally does not compute returns,
select assets, tune parameters, or authorize performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

EXPECTED = {
    "SPY_options.parquet": (
        "https://github.com/lambdaclass/options_portfolio_backtester/releases/download/data-v1/SPY_options.parquet",
        631738559,
        "a7152991b45b81f090f970e945bf88def8093b8ecb9b250e9891cb6d88041f0a",
    ),
    "QQQ_options.parquet": (
        "https://github.com/lambdaclass/options_portfolio_backtester/releases/download/data-v1/QQQ_options.parquet",
        387476183,
        "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734",
    ),
    "IWM_options.parquet": (
        "https://github.com/lambdaclass/options_portfolio_backtester/releases/download/data-v1/IWM_options.parquet",
        308766441,
        "d16a728116f8095c97c39ed66e75000bf66a0ab422b678002eb9f6086fd10ee5",
    ),
}

REQUIRED = {
    "contract_id", "symbol", "expiration", "strike", "type",
    "bid", "ask", "volume", "open_interest", "date",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path) -> None:
    request = Request(url, headers={"User-Agent": "trading-agent-public/Q129-independent-pit/1"})
    with urlopen(request, timeout=120) as response, path.open("wb") as out:
        while chunk := response.read(4 * 1024 * 1024):
            out.write(chunk)


def inspect(path: Path, dataset_name: str) -> dict[str, object]:
    import duckdb
    import exchange_calendars as xcals

    con = duckdb.connect(database=":memory:")
    con.execute("PRAGMA threads=2")
    parquet = str(path).replace("'", "''")
    schema = con.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{parquet}')"
    ).fetchall()
    columns = {row[0] for row in schema}
    missing_columns = sorted(REQUIRED - columns)
    if missing_columns:
        return {
            "status": "STRUCTURAL_INVALID",
            "missing_columns": missing_columns,
        }

    summary = con.execute(
        f"""
        SELECT
          COUNT(*) AS rows,
          COUNT(*) FILTER (WHERE contract_id IS NULL) AS null_contract_id,
          COUNT(*) FILTER (WHERE symbol IS NULL) AS null_symbol,
          COUNT(*) FILTER (WHERE date IS NULL) AS null_date,
          COUNT(*) FILTER (WHERE expiration IS NULL) AS null_expiration,
          COUNT(*) FILTER (WHERE bid IS NULL) AS null_bid,
          COUNT(*) FILTER (WHERE ask IS NULL) AS null_ask,
          COUNT(*) FILTER (WHERE volume IS NULL) AS null_volume,
          COUNT(*) FILTER (WHERE open_interest IS NULL) AS null_open_interest,
          COUNT(*) FILTER (WHERE volume < 0) AS negative_volume,
          COUNT(*) FILTER (WHERE open_interest < 0) AS negative_open_interest,
          COUNT(*) FILTER (WHERE bid < 0 OR ask < 0) AS negative_quote_rows,
          COUNT(*) FILTER (WHERE bid > 0 AND ask > 0 AND bid > ask) AS crossed_quotes,
          COUNT(*) FILTER (WHERE expiration < date) AS expiration_before_observation,
          COUNT(*) FILTER (WHERE UPPER(CAST(type AS VARCHAR)) NOT IN ('C','P','CALL','PUT')) AS invalid_option_type,
          COUNT(*) - COUNT(DISTINCT concat(CAST(contract_id AS VARCHAR), '|', CAST(date AS VARCHAR))) AS duplicate_contract_date_rows,
          MIN(CAST(date AS DATE)) AS first_observation_date,
          MAX(CAST(date AS DATE)) AS last_observation_date
        FROM read_parquet('{parquet}')
        """
    ).fetchone()
    keys = [
        "rows", "null_contract_id", "null_symbol", "null_date", "null_expiration",
        "null_bid", "null_ask", "null_volume", "null_open_interest",
        "negative_volume", "negative_open_interest", "negative_quote_rows", "crossed_quotes",
        "expiration_before_observation", "invalid_option_type",
        "duplicate_contract_date_rows", "first_observation_date", "last_observation_date",
    ]
    values = dict(zip(keys, summary))
    type_rows = con.execute(
        f"SELECT UPPER(CAST(type AS VARCHAR)) AS type, COUNT(*) AS rows "
        f"FROM read_parquet('{parquet}') GROUP BY 1 ORDER BY 1"
    ).fetchall()
    distinct_dates = [
        row[0] for row in con.execute(
            f"SELECT DISTINCT CAST(date AS DATE) FROM read_parquet('{parquet}') ORDER BY 1"
        ).fetchall()
    ]
    first_date = values["first_observation_date"]
    last_date = values["last_observation_date"]
    cal = xcals.get_calendar("XNYS")
    sessions = set()
    if first_date is not None and last_date is not None:
        for ts in cal.sessions_in_range(str(first_date), str(last_date)):
            sessions.add(ts.date())
    non_session_dates = sorted(str(x) for x in distinct_dates if x not in sessions)

    next_session_after_latest = None
    if last_date is not None:
        next_session_after_latest = cal.next_session(last_date).date().isoformat()

    non_session_row_count = 0
    for bad_date in non_session_dates:
        row_count = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{parquet}') WHERE CAST(date AS DATE) = DATE '{bad_date}'"
        ).fetchone()[0]
        non_session_row_count += int(row_count)

    eligible_where = [
        "volume >= 0",
        "open_interest >= 0",
        "bid >= 0",
        "ask >= 0",
        "NOT (bid > 0 AND ask > 0 AND bid > ask)",
        "expiration >= date",
        "UPPER(CAST(type AS VARCHAR)) IN ('C','P','CALL','PUT')",
    ]
    if non_session_dates:
        quoted = ",".join(f"DATE '{x}'" for x in non_session_dates)
        eligible_where.append(f"CAST(date AS DATE) NOT IN ({quoted})")
    eligible_rows = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{parquet}') WHERE {' AND '.join(eligible_where)}"
    ).fetchone()[0]

    structural_ok = (
        values["rows"] > 0
        and all(values[k] == 0 for k in (
            "null_contract_id", "null_symbol", "null_date", "null_expiration",
            "null_volume", "null_open_interest", "negative_volume",
            "negative_open_interest", "negative_quote_rows", "expiration_before_observation",
            "invalid_option_type", "duplicate_contract_date_rows"
        ))
        and REQUIRED.issubset(columns)
        and int(eligible_rows) > 0
    )

    return {
        "dataset": dataset_name,
        "status": "PIT_STRUCTURAL_CHECK_PASSED" if structural_ok else "PIT_STRUCTURAL_CHECK_FAILED",
        "columns": sorted(columns),
        "rows": int(values["rows"]),
        "first_observation_date": str(first_date),
        "last_observation_date": str(last_date),
        "type_counts": {str(k): int(v) for k, v in type_rows},
        "null_counts": {k: int(values[k]) for k in (
            "null_contract_id", "null_symbol", "null_date", "null_expiration",
            "null_bid", "null_ask", "null_volume", "null_open_interest"
        )},
        "negative_volume": int(values["negative_volume"]),
        "negative_open_interest": int(values["negative_open_interest"]),
        "negative_quote_rows": int(values["negative_quote_rows"]),
        "crossed_quotes_positive_only": int(values["crossed_quotes"]),
        "expiration_before_observation": int(values["expiration_before_observation"]),
        "invalid_option_type": int(values["invalid_option_type"]),
        "duplicate_contract_date_rows": int(values["duplicate_contract_date_rows"]),
        "non_xnys_observation_dates": non_session_dates[:20],
        "non_xnys_observation_date_count": len(non_session_dates),
        "non_xnys_observation_row_count": non_session_row_count,
        "eligible_rows_after_fixed_quarantine": int(eligible_rows),
        "deterministic_quarantine": {
            "raw_source_rows_modified": False,
            "option_type_map": {"CALL":"C","PUT":"P","C":"C","P":"P"},
            "exclude_positive_crossed_quotes": True,
            "exclude_negative_quotes": True,
            "exclude_non_xnys_observation_dates": True,
            "no_return_based_filtering": True,
        },
        "next_eligible_xnys_session_after_latest": next_session_after_latest,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)

    assets = {}
    for name, (url, expected_size, expected_hash) in EXPECTED.items():
        target = args.workdir / name
        download(url, target)
        observed_hash = sha256_file(target)
        assets[name] = {
            "url": url,
            "expected_size": expected_size,
            "observed_size": target.stat().st_size,
            "size_match": target.stat().st_size == expected_size,
            "expected_sha256": expected_hash,
            "observed_sha256": observed_hash,
            "sha256_match": observed_hash == expected_hash,
        }
        assets[name]["inspection"] = inspect(target, name)
        assets[name]["overall_ok"] = (
            assets[name]["size_match"]
            and assets[name]["sha256_match"]
            and assets[name]["inspection"].get("status") == "PIT_STRUCTURAL_CHECK_PASSED"
        )

    ok = all(asset["overall_ok"] for asset in assets.values())
    receipt = {
        "schema_version": "1.0",
        "receipt_type": "q129_independent_options_pit_reproduction",
        "candidate_id": "Q129",
        "status": "Q129_INDEPENDENT_PIT_REPRODUCED" if ok else "Q129_INDEPENDENT_PIT_REPRODUCTION_FAILED",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_release": {
            "repository": "lambdaclass/options_portfolio_backtester",
            "release_tag": "data-v1",
            "release_id": 289029018,
            "published_at": "2026-02-21T19:07:56Z",
        },
        "information_boundary": {
            "same_day_decision_use_allowed": False,
            "decision_boundary": "next eligible XNYS session after EOD observation unless a tighter dissemination timestamp is independently proven",
        },
        "assets": assets,
        "independent_method": {
            "engine": "duckdb",
            "calendar": "exchange_calendars/XNYS",
            "logic_is_distinct_from_source_feasibility_verifier": True,
            "return_evaluation": False,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    receipt["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "receipt_fingerprint": receipt["receipt_fingerprint"],
        "assets_ok": sum(1 for x in assets.values() if x["overall_ok"]),
    }, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
