"""Pre-registered breadth/concentration diagnostic for the fixed CS mechanism.

Diagnostic-only control. It evaluates the same 12-1 rank formation rule at a
fixed breadth ladder (top-1 through top-5) on two already completed independent
CS validation universes. No breadth is selected for production use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev


LOOKBACK = 252
SKIP = 21
REBALANCE = 21
BREADTHS = (1, 2, 3, 4, 5)


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _period_return(values: list[float]) -> float:
    equity = 1.0
    for value in values:
        equity *= 1.0 + value
    return equity - 1.0


def _max_drawdown(values: list[float]) -> float:
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for value in values:
        equity *= 1.0 + value
        peak = max(peak, equity)
        if peak > 0.0:
            max_dd = max(max_dd, 1.0 - equity / peak)
    return max_dd


def _rolling_stats(values: list[float], count: int = 5) -> list[dict]:
    width = len(values) // count
    windows = []
    for index in range(count):
        start = index * width
        end = len(values) if index == count - 1 else (index + 1) * width
        segment = values[start:end]
        windows.append(
            {
                "window_index": index + 1,
                "start_index": start,
                "end_index": end,
                "period_return": _period_return(segment),
                "max_drawdown_percent": _max_drawdown(segment) * 100.0,
            }
        )
    return windows


def _csv_rows(path: Path) -> list[dict]:
    import csv

    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "timestamp": datetime.fromisoformat(
                        row["timestamp"].replace("Z", "+00:00")
                    ),
                    "open": float(row["open"]),
                    "close": float(row["close"]),
                }
            )
    return rows


def _load_aligned_assets(root: Path, manifest: dict) -> tuple[dict[str, list[dict]], list[datetime]]:
    data_root = root / "data/market_data"
    symbols = [item["symbol"] for item in manifest.get("datasets", [])]
    if len(symbols) != 5:
        raise ValueError(f"Erwartet genau 5 CS-Assets, erhalten: {symbols}")

    raw = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        rows = _csv_rows(data_root / symbol / "1d.csv")
        expected = int(item["candle_count"])
        if len(rows) != expected:
            raise ValueError(
                f"{symbol}: Manifest {expected} Candles, Datei {len(rows)}."
            )
        raw[symbol] = rows

    common = sorted(
        set.intersection(
            *[set(row["timestamp"] for row in rows) for rows in raw.values()]
        )
    )
    if len(common) < LOOKBACK + SKIP + 30:
        raise ValueError("Zu wenig gemeinsam ausgerichtete Candles.")

    aligned = {
        symbol: [
            next(row for row in raw[symbol] if row["timestamp"] == timestamp)
            for timestamp in common
        ]
        for symbol in symbols
    }
    return aligned, common


def _validate_report(report: dict) -> None:
    stored = report.get("report_fingerprint")
    if not stored:
        raise ValueError("report_fingerprint fehlt.")
    body = dict(report)
    body.pop("report_fingerprint")
    if _fingerprint(body) != stored:
        raise ValueError("Report-Fingerprint ungültig.")
    if report.get("status") != "COMPLETED":
        raise ValueError("Report nicht abgeschlossen.")

    methodology = report.get("methodology", {})
    primary_rule = str(methodology.get("primary_rule", "")).lower()
    architecture = str(methodology.get("architecture", "")).lower()
    if (
        "12-1 cross-sectional momentum, top-2 long-only" not in primary_rule
        and "12-1 cs momentum top-2 long-only" not in architecture
    ):
        raise ValueError("Feste 12-1-CS-Top-2-Architektur nicht verifiziert.")

    if "formation_window_sessions" in methodology and int(
        methodology["formation_window_sessions"]
    ) != LOOKBACK:
        raise ValueError("Formation-Länge stimmt nicht.")
    if "skip_sessions" in methodology and int(
        methodology["skip_sessions"]
    ) != SKIP:
        raise ValueError("Skip-Länge stimmt nicht.")
    if "rebalance_sessions" in methodology and int(
        methodology["rebalance_sessions"]
    ) != REBALANCE:
        raise ValueError("Rebalance-Länge stimmt nicht.")
    if methodology.get("selection_profile_used") is not False:
        raise ValueError("Selection-profile Guard verletzt.")

    safety = report.get("safety", {})
    if safety.get("paper_only") is not True:
        raise ValueError("PAPER_ONLY verletzt.")
    if safety.get("live_trading_enabled") is not False:
        raise ValueError("LIVE_TRADING_ENABLED verletzt.")
    if safety.get("orders_enabled") is not False:
        raise ValueError("orders_enabled verletzt.")


def _research_count(report: dict, label: str) -> int:
    if label == "first_validation":
        return int(
            report["strategies"]["cs_momentum_252_long_only_top2"]["base"][
                "research"
            ]["day_count"]
        )
    return int(
        report["scenarios"]["base"]["vol_budget_10pct"]["price_only"]["research"][
            "day_count"
        ]
    )


def _analyse_breadth(
    assets: dict[str, list[dict]],
    timestamps: list[datetime],
    research_count: int,
) -> dict:
    symbols = tuple(assets)
    breadth_results = {}

    # One fixed ranking path per dataset. Only breadth changes across controls.
    ranking_path: list[tuple[str, ...] | None] = [None] * len(timestamps)
    for index in range(len(timestamps)):
        if index < LOOKBACK + SKIP:
            continue
        if index % REBALANCE != 0:
            continue
        anchor = index - SKIP
        origin = anchor - LOOKBACK
        scores = {
            symbol: (
                assets[symbol][anchor]["close"]
                / assets[symbol][origin]["close"]
                - 1.0
            )
            for symbol in symbols
        }
        ranking_path[index] = tuple(
            sorted(symbols, key=lambda symbol: (-scores[symbol], symbol))
        )

    for breadth in BREADTHS:
        current: tuple[str, ...] = ()
        selected_returns: list[float] = []
        equal_returns: list[float] = []
        selected_vs_equal: list[float] = []
        formation_rows: list[dict] = []

        for index in range(research_count):
            ranking = ranking_path[index]
            if ranking is not None:
                current = ranking[:breadth]

            asset_returns = {
                symbol: (
                    assets[symbol][index + 2]["open"]
                    / assets[symbol][index + 1]["open"]
                    - 1.0
                )
                for symbol in symbols
            }

            selected_return = (
                mean(asset_returns[symbol] for symbol in current)
                if current
                else 0.0
            )
            equal_return = mean(asset_returns.values())
            selected_returns.append(selected_return)
            equal_returns.append(equal_return)
            selected_vs_equal.append(selected_return - equal_return)

            if (
                ranking is not None
                and len(ranking) >= breadth
                and index + REBALANCE <= research_count
            ):
                winners = ranking[:breadth]
                forward_selected = []
                forward_equal = []
                for future_index in range(index, index + REBALANCE):
                    future_returns = {
                        symbol: (
                            assets[symbol][future_index + 2]["open"]
                            / assets[symbol][future_index + 1]["open"]
                            - 1.0
                        )
                        for symbol in symbols
                    }
                    forward_selected.append(
                        mean(future_returns[symbol] for symbol in winners)
                    )
                    forward_equal.append(mean(future_returns.values()))

                formation_rows.append(
                    {
                        "index": index,
                        "timestamp": timestamps[index + 2].isoformat(),
                        "forward_selection_spread": (
                            _period_return(forward_selected)
                            - _period_return(forward_equal)
                        ),
                    }
                )

        rolling = _rolling_stats(selected_returns)
        breadth_results[str(breadth)] = {
            "breadth": breadth,
            "selected_period_return": _period_return(selected_returns),
            "equal_weight_period_return": _period_return(equal_returns),
            "selection_spread_period_return": (
                _period_return(selected_returns)
                - _period_return(equal_returns)
            ),
            "max_drawdown_percent": _max_drawdown(selected_returns) * 100.0,
            "positive_day_ratio": (
                sum(value > 0.0 for value in selected_returns)
                / len(selected_returns)
            ),
            "selected_beats_equal_weight_ratio": (
                sum(
                    selected > equal
                    for selected, equal in zip(
                        selected_returns,
                        equal_returns,
                    )
                )
                / len(selected_returns)
            ),
            "mean_daily_selection_spread": mean(selected_vs_equal),
            "mean_cross_sectional_dispersion": mean(
                pstdev(
                    (
                        assets[symbol][index + 2]["open"]
                        / assets[symbol][index + 1]["open"]
                        - 1.0
                    )
                    for symbol in symbols
                )
                for index in range(research_count)
            ),
            "mean_forward_selection_spread": (
                mean(
                    row["forward_selection_spread"]
                    for row in formation_rows
                )
                if formation_rows
                else 0.0
            ),
            "negative_forward_spread_ratio": (
                sum(
                    row["forward_selection_spread"] < 0.0
                    for row in formation_rows
                )
                / len(formation_rows)
                if formation_rows
                else 0.0
            ),
            "formation_count": len(formation_rows),
            "rolling": rolling,
            "rolling_positive_window_count": sum(
                window["period_return"] > 0.0 for window in rolling
            ),
            "rolling_positive_window_ratio": (
                sum(window["period_return"] > 0.0 for window in rolling)
                / len(rolling)
            ),
        }

    return {
        "research_return_count": research_count,
        "breadths": breadth_results,
        "breadth_ladder_fixed_before_results": list(BREADTHS),
        "holdout_used": False,
    }


def _discover(root: Path) -> tuple[dict, dict, str]:
    first = (
        root / "research/cs_momentum_replication/report.json",
        root / "research/cs_momentum_replication/manifest.json",
        "first_validation",
    )
    second = (
        root / "research/independent_validation_2026_09_23/report.json",
        root / "research/independent_validation_2026_09_23/data_cs_manifest.json",
        "second_validation",
    )
    for report_path, manifest_path, label in (first, second):
        if report_path.is_file() and manifest_path.is_file():
            return (
                json.loads(report_path.read_text(encoding="utf-8")),
                json.loads(manifest_path.read_text(encoding="utf-8")),
                label,
            )
    raise FileNotFoundError("Unbekanntes CS-Artifact.")


def run_control(first_root: Path, second_root: Path, output_path: Path) -> dict:
    first_report, first_manifest, first_label = _discover(first_root)
    second_report, second_manifest, second_label = _discover(second_root)
    if first_label != "first_validation" or second_label != "second_validation":
        raise ValueError("Falsche Artifact-Zuordnung.")

    _validate_report(first_report)
    _validate_report(second_report)

    first_assets, first_timestamps = _load_aligned_assets(first_root, first_manifest)
    second_assets, second_timestamps = _load_aligned_assets(
        second_root, second_manifest
    )

    first = _analyse_breadth(
        first_assets,
        first_timestamps,
        _research_count(first_report, first_label),
    )
    second = _analyse_breadth(
        second_assets,
        second_timestamps,
        _research_count(second_report, second_label),
    )

    result = {
        "schema_version": 1,
        "diagnostic_type": "cs_breadth_concentration_control_2026_09_23",
        "status": "COMPLETED",
        "datasets": {
            "first_validation": {
                "report_fingerprint": first_report["report_fingerprint"],
                "manifest_fingerprint": first_manifest["manifest_fingerprint"],
                "symbols": [item["symbol"] for item in first_manifest["datasets"]],
                **first,
            },
            "second_validation": {
                "report_fingerprint": second_report["report_fingerprint"],
                "manifest_fingerprint": second_manifest["manifest_fingerprint"],
                "symbols": [item["symbol"] for item in second_manifest["datasets"]],
                **second,
            },
        },
        "constraints": [
            "diagnostic only",
            "breadth ladder fixed before reading results: 1,2,3,4,5",
            "no breadth selected for production",
            "no parameter optimization",
            "no asset replacement",
            "no signal change",
            "no sleeve-weight change",
            "no gate change",
            "holdout returns not consumed",
            "no production change",
        ],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["breadth_control_fingerprint"] = _fingerprint(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first-root", required=True)
    parser.add_argument("--second-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_control(
        Path(args.first_root),
        Path(args.second_root),
        Path(args.output),
    )
    print("CS_BREADTH_CONTROL_STATUS:", result["status"])
    for label in ("first_validation", "second_validation"):
        print(f"{label}_SPREADS:")
        for breadth, row in result["datasets"][label]["breadths"].items():
            print(
                breadth,
                row["selection_spread_period_return"],
                row["rolling_positive_window_ratio"],
                row["negative_forward_spread_ratio"],
            )
    print("BREADTH_CONTROL_FINGERPRINT:", result["breadth_control_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
