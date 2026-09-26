"""Q017 G3 coverage-first preflight.

This runner validates only historical source coverage and point-in-time data access
contracts for the three pre-registered Q017 mechanism families. It never computes
strategy returns, ranks candidates by performance, selects parameters/assets/horizons,
or authorizes a performance trial.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import settings
from data.canonical_snapshot import SnapshotSpec, build_frozen_snapshot
from research.asset_universes import get_universe, list_universes

ROOT = Path(__file__).resolve().parents[1]
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
REQUESTED_YAHOO_CANDLES = 3520
TARGET_COMMON_CANDLES = 3500
MACRO_SERIES = ("CPIAUCSL", "UNRATE")
CFTC_YEARS = tuple(range(2011, 2026))
CFTC_TARGETS = {
    "DBO": ("CRUDE OIL",),
    "UNG": ("NATURAL GAS",),
    "PPLT": ("PLATINUM",),
}
ALFRED_SAMPLE_DATES = ("2011-01-04", "2015-01-05", "2020-01-02", "2025-09-24")
USER_AGENT = "trading-agent-public/q017-g3-coverage-first"


@dataclass(frozen=True)
class HttpSnapshot:
    url: str
    sha256: str
    byte_count: int


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _http_bytes(url: str, timeout: int = 45) -> tuple[bytes, HttpSnapshot]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        content = response.read()
    return content, HttpSnapshot(url=url, sha256=_sha256(content), byte_count=len(content))


def _http_text(url: str, timeout: int = 45) -> tuple[str, HttpSnapshot]:
    content, snapshot = _http_bytes(url, timeout=timeout)
    return content.decode("utf-8-sig", errors="replace"), snapshot


def _canonical_market(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()


def _date_in_window(value: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            parsed = datetime.strptime(value.strip(), fmt).date()
            if STUDY_START <= parsed <= STUDY_END:
                return parsed
        except ValueError:
            continue
    return None


def _parse_alfred_rows(csv_text: str, series: str) -> tuple[dict[date, str], str]:
    rows = list(csv.reader(io.StringIO(csv_text)))
    if not rows or len(rows[0]) < 2 or rows[0][0].strip().lower() != "observation_date":
        raise ValueError(f"{series}: unexpected ALFRED CSV header")
    expected_prefix = f"{series}_"
    if not rows[0][1].startswith(expected_prefix):
        raise ValueError(f"{series}: vintage column mismatch: {rows[0][1]!r}")
    values: dict[date, str] = {}
    for row in rows[1:]:
        if len(row) < 2:
            continue
        try:
            obs_date = date.fromisoformat(row[0].strip())
        except ValueError:
            continue
        if not (STUDY_START <= obs_date <= STUDY_END):
            continue
        value = row[1].strip()
        if value in ("", ".", "#NA", "NA"):
            continue
        values[obs_date] = value
    return values, rows[0][1]


def _alfred_vintage_dates(series: str) -> tuple[list[str], HttpSnapshot]:
    url = "https://alfred.stlouisfed.org/series/downloaddata?" + urlencode({"seid": series})
    html, snapshot = _http_text(url)
    dates = sorted(
        set(
            re.findall(
                r"<option[^>]+value=[\"'](20\d{2}-\d{2}-\d{2})[\"']",
                html,
                flags=re.IGNORECASE,
            )
        )
    )
    usable = [value for value in dates if STUDY_START <= date.fromisoformat(value) <= STUDY_END]
    if len(usable) < 50:
        raise ValueError(f"{series}: too few ALFRED vintage dates discovered ({len(usable)})")
    return usable, snapshot


def _macro_coverage(output_dir: Path) -> dict:
    result = {
        "family": "macro_surprise_state_transition",
        "source": "ALFRED",
        "series": {},
        "status": "COVERAGE_VALIDATED",
        "point_in_time_ready": True,
    }
    source_meta = []
    for series in MACRO_SERIES:
        try:
            vintages, listing_snapshot = _alfred_vintage_dates(series)
        except (OSError, ValueError) as exc:
            result["status"] = "DATA_INSUFFICIENT"
            result["point_in_time_ready"] = False
            result["series"][series] = {"status": "DATA_INSUFFICIENT", "error": str(exc)}
            continue

        source_meta.append({
            "url": listing_snapshot.url,
            "sha256": listing_snapshot.sha256,
            "byte_count": listing_snapshot.byte_count,
            "vintage_count_in_window": len(vintages),
        })

        first_seen: dict[date, str] = {}
        total_snapshots_used = 0
        sample_results = []

        for vintage in vintages:
            url = "https://alfred.stlouisfed.org/graph/alfredgraph.csv?" + urlencode({
                "id": series,
                "vintage_date": vintage,
                "cosd": STUDY_START.isoformat(),
                "coed": STUDY_END.isoformat(),
            })
            try:
                csv_text, snapshot = _http_text(url)
                values, header = _parse_alfred_rows(csv_text, series)
            except (OSError, ValueError) as exc:
                result["status"] = "DATA_INSUFFICIENT"
                result["point_in_time_ready"] = False
                result["series"][series] = {
                    "status": "DATA_INSUFFICIENT",
                    "error": str(exc),
                    "vintage_count_in_window": len(vintages),
                }
                break
            total_snapshots_used += 1
            for obs_date in values:
                first_seen.setdefault(obs_date, vintage)
            if vintage in ALFRED_SAMPLE_DATES:
                sample_results.append({
                    "vintage_date": vintage,
                    "header": header,
                    "observations": len(values),
                    "sha256": snapshot.sha256,
                    "byte_count": snapshot.byte_count,
                })

        status = "COVERAGE_VALIDATED" if len(first_seen) >= 150 else "DATA_INSUFFICIENT"
        if status != "COVERAGE_VALIDATED":
            result["status"] = "DATA_INSUFFICIENT"
            result["point_in_time_ready"] = False

        result["series"][series] = {
            "status": status,
            "vintage_count_in_window": len(vintages),
            "vintages_scanned": total_snapshots_used,
            "observations_with_first_vintage": len(first_seen),
            "first_vintage_by_observation": {
                key.isoformat(): value for key, value in sorted(first_seen.items())
            },
            "sample_vintages": sample_results,
            "selection_used": False,
            "performance_evaluation": False,
        }

    result["source_listing_snapshots"] = source_meta
    return result


def _cftc_parse_zip(raw: bytes) -> tuple[list[dict[str, str]], str]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [
            name for name in archive.namelist()
            if not name.endswith("/")
            and name.lower().endswith((".txt", ".csv"))
            and "readme" not in name.lower()
        ]
        if not names:
            raise ValueError("CFTC archive contains no usable text/CSV data file")
        data_name = names[0]
        payload = archive.read(data_name)

    text = payload.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CFTC data file has no header")
    field_map = {_canonical_market(field): field for field in reader.fieldnames if field}
    market_field = field_map.get(_canonical_market("Market_and_Exchange_Names"))
    date_field = (
        field_map.get(_canonical_market("As_of_Date_In_Form_YYYY-MM-DD"))
        or field_map.get(_canonical_market("As of Date in Form YYYY-MM-DD"))
        or field_map.get(_canonical_market("As_of_Date_In_Form_MM/DD/YYYY"))
        or field_map.get(_canonical_market("As of Date in Form MM/DD/YYYY"))
        or field_map.get(_canonical_market("Report_Date_as_YYYY-MM-DD"))
    )
    if not market_field or not date_field:
        raise ValueError("CFTC disaggregated header missing market/date fields")

    rows = []
    for row in reader:
        market = row.get(market_field, "")
        report_date = row.get(date_field, "")
        if market and report_date:
            rows.append({"market": market, "report_date": report_date})
    return rows, data_name


def _cftc_coverage(output_dir: Path) -> dict:
    family = {
        "family": "cftc_positioning_crowding",
        "source": "CFTC Disaggregated Futures Only",
        "status": "COVERAGE_VALIDATED",
        "point_in_time_ready": False,
        "pit_status": "UNVERIFIED_HISTORICAL_RELEASE_TIMESTAMPS",
        "historical_release_timestamp_policy": {
            "default": "Friday 15:30 America/New_York after Tuesday report data",
            "exception_policy": "Historical exceptions are not represented in annual compressed archives and remain an explicit preflight limitation.",
        },
        "markets": {
            symbol: {
                "required_tokens": list(tokens),
                "matched_report_dates": set(),
                "source_files": [],
            }
            for symbol, tokens in CFTC_TARGETS.items()
        },
    }

    source_dir = output_dir / "source_cache" / "cftc"
    source_dir.mkdir(parents=True, exist_ok=True)
    for year in CFTC_YEARS:
        url = f"https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
        try:
            raw, snapshot = _http_bytes(url, timeout=60)
            (source_dir / f"{year}.zip").write_bytes(raw)
            rows, data_name = _cftc_parse_zip(raw)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            family["status"] = "DATA_INSUFFICIENT"
            family.setdefault("errors", []).append({"year": year, "error": str(exc)})
            continue

        family.setdefault("source_files", []).append({
            "year": year,
            "data_file": data_name,
            "url": snapshot.url,
            "sha256": snapshot.sha256,
            "byte_count": snapshot.byte_count,
        })

        for row in rows:
            report_date = _date_in_window(row["report_date"])
            if report_date is None:
                continue
            market = _canonical_market(row["market"])
            for symbol, tokens in CFTC_TARGETS.items():
                if all(token in market for token in tokens):
                    family["markets"][symbol]["matched_report_dates"].add(report_date)
                    family["markets"][symbol]["source_files"].append(year)

    expected_min = 650
    for symbol, meta in family["markets"].items():
        dates = sorted(meta["matched_report_dates"])
        meta["matched_report_dates"] = [item.isoformat() for item in dates]
        meta["observation_count"] = len(dates)
        meta["min_report_date"] = dates[0].isoformat() if dates else None
        meta["max_report_date"] = dates[-1].isoformat() if dates else None
        meta["source_files"] = sorted(set(meta["source_files"]))
        if len(dates) < expected_min:
            family["status"] = "DATA_INSUFFICIENT"
        meta["expected_min_reports"] = expected_min

    # The public historical archive exposes report dates, but CFTC does not provide
    # a historical release-date list. Without exact historical publication timestamps,
    # the point-in-time contract cannot be certified for a backtest.
    family["point_in_time_ready"] = False
    family["pit_status"] = "UNVERIFIED_HISTORICAL_RELEASE_TIMESTAMPS"
    family["eligibility"] = "DATA_INSUFFICIENT"
    family["status"] = "DATA_INSUFFICIENT"

    return family


def _yahoo_coverage(universe_name: str, output_dir: Path) -> dict:
    universe = get_universe(universe_name)
    snapshot_dir = output_dir / "source_cache" / "yahoo"
    canonical = build_frozen_snapshot(
        SnapshotSpec(
            universe=universe.name,
            symbols=tuple(universe.symbols),
            interval="1d",
            requested_candles=REQUESTED_YAHOO_CANDLES,
            target_common_candles=TARGET_COMMON_CANDLES,
            minimum_in_window_candles=TARGET_COMMON_CANDLES,
            output_dir=snapshot_dir,
            dataset_subdir=".",
            study_start=STUDY_START,
            study_end=STUDY_END,
        )
    )
    coverage = canonical["coverage"]
    per_symbol = {}
    for symbol in universe.symbols:
        item = coverage["per_symbol"].get(symbol, {})
        per_symbol[symbol] = {
            "status": "COVERAGE_VALID" if item.get("status") == "COVERAGE_VALID" else "DATA_INVALID",
            "count_in_window": item.get("in_window_count", 0),
            "start": item.get("start"),
            "end": item.get("end"),
            "fingerprint": item.get("fingerprint"),
            "quality": item.get("quality", {}),
            "error": item.get("error"),
        }

    status = (
        "COVERAGE_VALIDATED"
        if canonical["status"] == "COVERAGE_PASSED"
        else "DATA_INVALID"
    )
    return {
        "family": "abnormal_turnover_liquidity_shock",
        "source": "Yahoo Finance daily OHLCV",
        "universe": universe.name,
        "symbols": list(universe.symbols),
        "requested_candles": REQUESTED_YAHOO_CANDLES,
        "target_common_candles": TARGET_COMMON_CANDLES,
        "status": status,
        "common_calendar_count": coverage["common_calendar_count"],
        "per_symbol": per_symbol,
        "snapshot_fingerprint": canonical["snapshot_fingerprint"],
        "canonical_data_layer": "data/canonical_snapshot.py",
        "performance_evaluation": False,
        "selection_used": False,
    }


# Q017 uses the same fixed fresh universe for turnover coverage; CFTC has its own
# fixed subset mapping declared in CFTC_TARGETS above.

def _disjointness_check(universe_name: str) -> dict:
    universe = get_universe(universe_name)
    target = set(universe.symbols)
    overlaps = {}
    for other in list_universes():
        if other.name == universe.name:
            continue
        overlap = sorted(target.intersection(other.symbols))
        if overlap:
            overlaps[other.name] = overlap
    return {
        "universe": universe_name,
        "symbols": list(universe.symbols),
        "symbol_disjoint": not overlaps,
        "overlaps": overlaps,
    }


def run(
    *,
    output_root: str | Path = "research/runs/q017_g3_coverage_first",
    universe_name: str = "q017_coverage_first",
) -> dict:
    if settings.PAPER_ONLY is not True:
        raise RuntimeError("Q017 G3 requires PAPER_ONLY=True")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Q017 G3 requires LIVE_TRADING_ENABLED=False")
    if settings.ORDERS_ENABLED is not False:
        raise RuntimeError("Q017 G3 requires ORDERS_ENABLED=False")

    output_dir = Path(output_root)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    prereg = ROOT / "research" / "preregistrations" / "q017_g3_coverage_first_2026_09_25.json"
    spec = json.loads(prereg.read_text(encoding="utf-8"))
    if spec["fresh_universe"]["name"] != universe_name:
        raise RuntimeError("Q017 universe mismatch")

    disjointness = _disjointness_check(universe_name)
    if not disjointness["symbol_disjoint"]:
        raise RuntimeError(f"Q017 universe overlap detected: {disjointness['overlaps']}")

    macro = _macro_coverage(output_dir / "macro")
    cftc = _cftc_coverage(output_dir)
    yahoo = _yahoo_coverage(universe_name, output_dir)

    failures = {
        family["family"]: family["status"]
        for family in (macro, cftc, yahoo)
        if family["status"] != "COVERAGE_VALIDATED"
    }
    overall_status = "COVERAGE_SOURCE_VALIDATED"
    if failures:
        overall_status = (
            "DATA_INSUFFICIENT"
            if any(value == "DATA_INSUFFICIENT" for value in failures.values())
            else "DATA_INVALID"
        )

    payload = {
        "schema_version": "1.0",
        "task_id": "Q-017-G3-COVERAGE-FIRST",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "study_window": {
            "start": STUDY_START.isoformat(),
            "end": STUDY_END.isoformat(),
            "target_common_daily_candles": TARGET_COMMON_CANDLES,
            "requested_yahoo_candles": REQUESTED_YAHOO_CANDLES,
        },
        "status": overall_status,
        "universe_disjointness": disjointness,
        "families": {
            "macro_surprise_state_transition": macro,
            "cftc_positioning_crowding": cftc,
            "abnormal_turnover_liquidity_shock": yahoo,
        },
        "governance": {
            "performance_evaluation": False,
            "oos_evaluation": False,
            "holdout_evaluation": False,
            "selection_used": False,
            "holdout_used_for_selection": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "interpretation": {
            "result_type": "coverage_only",
            "return_metrics_computed": False,
            "family_ranking": False,
            "next_gate": "formalize one fixed candidate only after coverage/PIT review; no performance selection is contained in this run",
        },
    }

    payload["coverage_fingerprint"] = _sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    )

    report_path = output_dir / "q017_g3_coverage_first_result.json"
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "task_id": payload["task_id"],
                "report": str(report_path.relative_to(ROOT)),
                "coverage_fingerprint": payload["coverage_fingerprint"],
                "performance_evaluation": False,
                "performance_trial_authorized": False,
                "safety": payload["safety"],
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "task_id": payload["task_id"],
        "status": payload["status"],
        "coverage_fingerprint": payload["coverage_fingerprint"],
        "family_statuses": {key: value["status"] for key, value in payload["families"].items()},
        "performance_trial_authorized": False,
    }, sort_keys=True))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="research/runs/q017_g3_coverage_first")
    parser.add_argument("--universe", default="q017_coverage_first")
    args = parser.parse_args()
    run(output_root=args.output_root, universe_name=args.universe)


if __name__ == "__main__":
    main()
