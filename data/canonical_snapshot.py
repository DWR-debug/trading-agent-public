"""Canonical, fail-closed OHLCV snapshot builder for research coverage.

This module is the single reusable path for market-data coverage snapshots:
acquisition -> study-window filtering -> cross-symbol calendar intersection ->
exact common-calendar selection -> frozen aligned snapshot -> deterministic
dataset fingerprints.

It never computes returns, P&L, performance metrics, or candidate selection.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from backtesting.models import Candle
from data.yahoo_loader import load_yahoo_history
from research.protocol import dataset_fingerprint

ROOT = Path(__file__).resolve().parents[1]
Loader = Callable[..., list[Candle]]
CSV_HEADER = ("timestamp", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class SnapshotSpec:
    """Immutable data-acquisition and common-calendar contract."""

    universe: str
    symbols: tuple[str, ...]
    interval: str
    requested_candles: int
    target_common_candles: int
    output_dir: Path
    study_start: date | None = None
    study_end: date | None = None
    source: str = "yahoo_chart"
    minimum_in_window_candles: int | None = None

    def __post_init__(self) -> None:
        if not self.universe:
            raise ValueError("universe must not be empty")
        if not self.symbols:
            raise ValueError("symbols must not be empty")
        if len(self.symbols) != len(set(self.symbols)):
            raise ValueError("symbols must be unique")
        if self.requested_candles < 1:
            raise ValueError("requested_candles must be positive")
        if self.target_common_candles < 1:
            raise ValueError("target_common_candles must be positive")
        if self.target_common_candles > self.requested_candles:
            raise ValueError("target_common_candles cannot exceed requested_candles")
        minimum = self.target_common_candles if self.minimum_in_window_candles is None else self.minimum_in_window_candles
        if minimum < self.target_common_candles or minimum > self.requested_candles:
            raise ValueError("minimum_in_window_candles must be between target and requested candles")
        if self.study_start and self.study_end and self.study_start > self.study_end:
            raise ValueError("study_start cannot be after study_end")


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _write_csv(path: Path, candles: Iterable[Candle]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        for candle in candles:
            writer.writerow(
                (
                    candle.timestamp.isoformat(),
                    candle.open,
                    candle.high,
                    candle.low,
                    candle.close,
                    candle.volume,
                )
            )


def _filter_study_window(
    candles: Iterable[Candle],
    study_start: date | None,
    study_end: date | None,
) -> list[Candle]:
    result = []
    for candle in candles:
        day = candle.timestamp.date()
        if study_start is not None and day < study_start:
            continue
        if study_end is not None and day > study_end:
            continue
        result.append(candle)
    result.sort(key=lambda item: item.timestamp)
    return result


def build_frozen_snapshot(
    spec: SnapshotSpec,
    *,
    loader: Loader = load_yahoo_history,
) -> dict:
    """Build one aligned, frozen common-calendar snapshot."""

    output_dir = spec.output_dir
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir

    per_symbol: dict[str, dict] = {}
    bars_by_symbol: dict[str, tuple[Candle, ...]] = {}
    errors: dict[str, str] = {}

    for symbol in spec.symbols:
        quality: dict[str, int] = {}
        try:
            raw = loader(
                symbol,
                spec.interval,
                spec.requested_candles,
                allow_partial=True,
                skip_invalid_ohlc=True,
                quality_report=quality,
            )
            bars = _filter_study_window(raw, spec.study_start, spec.study_end)
        except Exception as exc:
            errors[symbol] = str(exc)
            per_symbol[symbol] = {
                "status": "DATA_INVALID",
                "acquired_count": 0,
                "in_window_count": 0,
                "quality": quality,
                "error": str(exc),
            }
            continue

        bars_tuple = tuple(bars)
        bars_by_symbol[symbol] = bars_tuple
        per_symbol[symbol] = {
            "status": "COVERAGE_VALID"
            if len(bars_tuple) >= (spec.minimum_in_window_candles or spec.target_common_candles)
            else "DATA_INVALID",
            "acquired_count": len(raw),
            "in_window_count": len(bars_tuple),
            "start": bars_tuple[0].timestamp.isoformat() if bars_tuple else None,
            "end": bars_tuple[-1].timestamp.isoformat() if bars_tuple else None,
            "fingerprint": (
                dataset_fingerprint(bars_tuple)
                if len(bars_tuple) >= (spec.minimum_in_window_candles or spec.target_common_candles)
                and bars_tuple
                else None
            ),
            "quality": quality,
        }
        if len(bars_tuple) < (spec.minimum_in_window_candles or spec.target_common_candles):
            errors[symbol] = (
                f"{symbol}: {len(bars_tuple)} candles in fixed study window; "
                f"need at least {(spec.minimum_in_window_candles or spec.target_common_candles)}"
            )

    if len(bars_by_symbol) != len(spec.symbols):
        status = "DATA_INVALID"
        reason = "missing_or_unloadable_symbols"
        common_timestamps: set[datetime] = set()
    else:
        common_timestamps = set.intersection(
            *(
                {bar.timestamp for bar in bars_by_symbol[symbol]}
                for symbol in spec.symbols
            )
        )
        status = (
            "COVERAGE_PASSED"
            if len(common_timestamps) >= spec.target_common_candles and not errors
            else "DATA_INVALID"
        )
        reason = (
            None
            if status == "COVERAGE_PASSED"
            else "insufficient_common_calendar"
            if len(common_timestamps) < spec.target_common_candles
            else "per_symbol_coverage_failure"
        )

    selected_timestamps = (
        sorted(common_timestamps)[-spec.target_common_candles:]
        if status == "COVERAGE_PASSED"
        else []
    )

    snapshot_datasets: list[dict] = []
    selected_start = selected_timestamps[0].isoformat() if selected_timestamps else None
    selected_end = selected_timestamps[-1].isoformat() if selected_timestamps else None

    if status == "COVERAGE_PASSED":
        lookup_by_symbol = {
            symbol: {bar.timestamp: bar for bar in bars_by_symbol[symbol]}
            for symbol in spec.symbols
        }
        for symbol in spec.symbols:
            aligned = tuple(
                lookup_by_symbol[symbol][timestamp]
                for timestamp in selected_timestamps
            )
            if len(aligned) != spec.target_common_candles:
                raise RuntimeError(f"{symbol}: aligned snapshot count mismatch")
            if tuple(bar.timestamp for bar in aligned) != tuple(selected_timestamps):
                raise RuntimeError(f"{symbol}: aligned timestamps mismatch")

            csv_path = output_dir / "datasets" / symbol / f"{spec.interval}.csv"
            _write_csv(csv_path, aligned)
            snapshot_datasets.append(
                {
                    "symbol": symbol,
                    "interval": spec.interval,
                    "path": str(csv_path.relative_to(ROOT))
                    if csv_path.is_relative_to(ROOT)
                    else str(csv_path),
                    "candle_count": len(aligned),
                    "fingerprint": dataset_fingerprint(aligned),
                }
            )

    immutable_identity = {
        "schema_version": "1.0",
        "universe": spec.universe,
        "source": spec.source,
        "interval": spec.interval,
        "symbols": list(spec.symbols),
        "requested_candles": spec.requested_candles,
        "target_common_candles": spec.target_common_candles,
        "minimum_in_window_candles": spec.minimum_in_window_candles or spec.target_common_candles,
        "study_start": spec.study_start.isoformat() if spec.study_start else None,
        "study_end": spec.study_end.isoformat() if spec.study_end else None,
        "selected_common_calendar_start": selected_start,
        "selected_common_calendar_end": selected_end,
        "selection_rule": "last_target_common_timestamps_from_full_fixed_window_intersection",
        "datasets": snapshot_datasets,
    }

    payload = {
        **immutable_identity,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "coverage": {
            "common_calendar_count": len(common_timestamps),
            "per_symbol": per_symbol,
            "errors": errors,
            "failure_reason": reason,
        },
        "data_snapshot": (
            {
                "format": "csv_ohlcv_common_calendar",
                "selection_rule": immutable_identity["selection_rule"],
                "datasets": snapshot_datasets,
            }
            if status == "COVERAGE_PASSED"
            else None
        ),
        "governance": {
            "coverage_only": True,
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
        "snapshot_fingerprint": _sha256(immutable_identity),
    }

    if status == "COVERAGE_PASSED":
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "snapshot_manifest.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    return payload


def snapshot_from_preregistration(
    spec: dict,
    *,
    output_root: str | Path,
    loader: Loader = load_yahoo_history,
) -> dict:
    """Construct a canonical snapshot directly from a preregistration mapping."""

    study = spec.get("study_window", {})
    data_contract = spec.get("data_contract", {})
    requested_value = spec.get("requested_candles")
    if requested_value is None:
        requested_value = data_contract.get("requested_raw_candles_per_symbol")
    target_value = spec.get("target_candles")
    if target_value is None:
        target_value = data_contract.get("target_common_calendar")
    if requested_value is None or target_value is None:
        raise ValueError("Preregistration lacks requested/target coverage geometry")

    study_start = study.get("start") or data_contract.get("study_start")
    study_end = study.get("end") or data_contract.get("study_end")

    return build_frozen_snapshot(
        SnapshotSpec(
            universe=str(spec["universe"]),
            symbols=tuple(spec["symbols"]),
            interval=str(spec["interval"]),
            requested_candles=int(requested_value),
            target_common_candles=int(target_value),
            output_dir=Path(output_root) / str(spec["trial_id"]),
            study_start=date.fromisoformat(study_start) if study_start else None,
            study_end=date.fromisoformat(study_end) if study_end else None,
        ),
        loader=loader,
    )
