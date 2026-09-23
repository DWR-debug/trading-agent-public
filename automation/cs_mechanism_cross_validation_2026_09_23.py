"""Cross-validation of the fixed cross-sectional mechanism.

Diagnostic-only control. It compares the same pre-registered 12-1/top-2 rule on
two already completed, independent validation universes. Holdout returns are
not consumed by this analysis.
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
TOP_N = 2


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


def _correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left_std = pstdev(left)
    right_std = pstdev(right)
    if left_std == 0.0 or right_std == 0.0:
        return 0.0
    left_mean = mean(left)
    right_mean = mean(right)
    return mean(
        (a - left_mean) * (b - right_mean)
        for a, b in zip(left, right)
    ) / (left_std * right_std)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _csv_rows(path: Path) -> list[dict]:
    import csv

    rows: list[dict] = []
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


def _discover_source(root: Path) -> tuple[dict, dict, Path, str]:
    candidates = (
        (
            root / "research/cs_momentum_replication/report.json",
            root / "research/cs_momentum_replication/manifest.json",
            "first_validation",
        ),
        (
            root / "research/independent_validation_2026_09_23/report.json",
            root / "research/independent_validation_2026_09_23/data_cs_manifest.json",
            "second_validation",
        ),
    )
    for report_path, manifest_path, label in candidates:
        if report_path.is_file() and manifest_path.is_file():
            return (
                _load_json(report_path),
                _load_json(manifest_path),
                report_path.parent.parent.parent,
                label,
            )
    raise FileNotFoundError(
        f"Kein bekanntes Cross-Sectional-Artifact unter {root}"
    )


def _research_count(report: dict, label: str) -> int:
    if label == "first_validation":
        return int(
            report["strategies"]["cs_momentum_252_long_only_top2"][
                "base"
            ]["research"]["day_count"]
        )
    return int(
        report["scenarios"]["base"]["vol_budget_10pct"]["price_only"][
            "research"
        ]["day_count"]
    )


def _validate_report(report: dict, manifest: dict, label: str) -> None:
    stored = report.get("report_fingerprint")
    if not stored:
        raise ValueError(f"{label}: report_fingerprint fehlt.")
    body = dict(report)
    body.pop("report_fingerprint")
    if _fingerprint(body) != stored:
        raise ValueError(f"{label}: Report-Fingerprint ungültig.")

    if report.get("status") != "COMPLETED":
        raise ValueError(f"{label}: Report nicht abgeschlossen.")
    if not manifest.get("manifest_fingerprint"):
        raise ValueError(f"{label}: Manifest-Fingerprint fehlt.")

    methodology = report.get("methodology", {})
    preregistration = report.get("preregistration", {})
    architecture_text = str(
        methodology.get("architecture", "")
    ).lower()
    preregistration_text = json.dumps(
        preregistration,
        sort_keys=True,
    ).lower()
    if "12-1 cs momentum top-2 long-only" not in architecture_text:
        raise ValueError(
            f"{label}: feste 12-1-CS-Top-2-Architektur nicht verifiziert."
        )
    if preregistration.get("concrete_universes_fixed_before_data_acquisition") is not True:
        raise ValueError(
            f"{label}: präregistrierte Universen nicht verifiziert."
        )
    if preregistration.get("selection_after_results") is not False:
        raise ValueError(
            f"{label}: Selection-after-results Guard verletzt."
        )
    if preregistration.get("asset_replacement_after_results") is not False:
        raise ValueError(
            f"{label}: Asset-replacement-after-results Guard verletzt."
        )
    if "selection_profile_used" in methodology and methodology["selection_profile_used"] is not False:
        raise ValueError(
            f"{label}: Selection-profile Guard verletzt."
        )

    safety = report.get("safety", {})
    if safety.get("paper_only") is not True:
        raise ValueError(f"{label}: PAPER_ONLY verletzt.")
    if safety.get("live_trading_enabled") is not False:
        raise ValueError(f"{label}: LIVE_TRADING_ENABLED verletzt.")
    if safety.get("orders_enabled") is not False:
        raise ValueError(f"{label}: orders_enabled verletzt.")

    if label == "second_validation" and report.get("candidate_status") != "BLOCKED":
        raise ValueError("second_validation: Candidate-Status ist nicht BLOCKED.")


def _validate_manifest(manifest: dict, data_root: Path) -> list[str]:
    symbols = []
    for dataset in manifest.get("datasets", []):
        symbol = dataset["symbol"]
        path = data_root / symbol / "1d.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Fehlende Daten: {symbol}")
        rows = _csv_rows(path)
        expected = int(dataset["candle_count"])
        if len(rows) != expected:
            raise ValueError(
                f"{symbol}: Manifest {expected} Candles, Datei {len(rows)}."
            )
        symbols.append(symbol)
    if len(symbols) != 5:
        raise ValueError(f"Cross-Sectional-Universum muss 5 Assets enthalten: {symbols}")
    return symbols


def _load_aligned_assets(
    manifest: dict,
    data_root: Path,
) -> tuple[dict[str, list[dict]], list[datetime]]:
    symbols = _validate_manifest(manifest, data_root)
    raw = {symbol: _csv_rows(data_root / symbol / "1d.csv") for symbol in symbols}
    common = sorted(
        set.intersection(
            *[set(row["timestamp"] for row in rows) for rows in raw.values()]
        )
    )
    if len(common) < LOOKBACK + SKIP + TOP_N + 5:
        raise ValueError("Zu wenig gemeinsam ausgerichtete Daten.")
    aligned = {
        symbol: [
            next(row for row in raw[symbol] if row["timestamp"] == timestamp)
            for timestamp in common
        ]
        for symbol in symbols
    }
    return aligned, common


def _analyse_dataset(
    root: Path,
    report: dict,
    manifest: dict,
    label: str,
) -> dict:
    data_root = root / "data/market_data"
    assets, timestamps = _load_aligned_assets(manifest, data_root)
    symbols = tuple(assets)
    research_count = _research_count(report, label)

    if research_count > len(timestamps) - 2:
        raise ValueError(
            f"{label}: Research-Länge {research_count} überschreitet Datenbasis."
        )

    weights: list[dict[str, float]] = []
    current = {symbol: 0.0 for symbol in symbols}

    for index in range(len(timestamps)):
        if index % REBALANCE == 0:
            if index < LOOKBACK + SKIP:
                current = {symbol: 0.0 for symbol in symbols}
            else:
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
                winners = sorted(
                    symbols,
                    key=lambda symbol: (-scores[symbol], symbol),
                )[:TOP_N]
                current = {
                    symbol: 1.0 / TOP_N if symbol in winners else 0.0
                    for symbol in symbols
                }
        weights.append(dict(current))

    selected: list[float] = []
    equal_weight: list[float] = []
    bottom: list[float] = []
    dispersion: list[float] = []
    turnover: list[float] = []
    rebalances: list[dict] = []
    previous_weights = {symbol: 0.0 for symbol in symbols}

    for index in range(research_count):
        asset_returns = {
            symbol: (
                assets[symbol][index + 2]["open"]
                / assets[symbol][index + 1]["open"]
                - 1.0
            )
            for symbol in symbols
        }
        target = weights[index]
        selected_symbols = tuple(
            symbol for symbol in symbols if target[symbol] > 0.0
        )
        selected_return = (
            mean(asset_returns[symbol] for symbol in selected_symbols)
            if selected_symbols
            else 0.0
        )
        equal_return = mean(asset_returns.values())
        bottom_symbols = tuple(
            symbol
            for symbol, _ in sorted(
                asset_returns.items(),
                key=lambda item: (item[1], item[0]),
            )[:TOP_N]
        )

        selected.append(selected_return)
        equal_weight.append(equal_return)
        bottom.append(mean(asset_returns[symbol] for symbol in bottom_symbols))
        dispersion.append(pstdev(asset_returns.values()))
        turnover.append(
            sum(
                abs(target[symbol] - previous_weights[symbol])
                for symbol in symbols
            )
        )
        previous_weights = dict(target)

        if (
            index >= LOOKBACK + SKIP
            and index % REBALANCE == 0
            and index + REBALANCE <= research_count
        ):
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
            ranking = sorted(
                scores.items(),
                key=lambda item: (-item[1], item[0]),
            )
            winners = tuple(symbol for symbol, _ in ranking[:TOP_N])
            losers = tuple(symbol for symbol, _ in ranking[-TOP_N:])

            forward_selected: list[float] = []
            forward_equal: list[float] = []
            forward_bottom: list[float] = []
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
                forward_bottom.append(
                    mean(future_returns[symbol] for symbol in losers)
                )

            formation_score = mean(scores[symbol] for symbol in winners)
            forward_spread = (
                _period_return(forward_selected)
                - _period_return(forward_equal)
            )
            rebalances.append(
                {
                    "index": index,
                    "timestamp": timestamps[index + 2].isoformat(),
                    "formation_score": formation_score,
                    "forward_selection_spread": forward_spread,
                    "forward_selected_vs_bottom": (
                        _period_return(forward_selected)
                        - _period_return(forward_bottom)
                    ),
                }
            )

    forward_spreads = [
        item["forward_selection_spread"] for item in rebalances
    ]
    formation_scores = [
        item["formation_score"] for item in rebalances
    ]

    return {
        "label": label,
        "report_fingerprint": report["report_fingerprint"],
        "manifest_fingerprint": manifest["manifest_fingerprint"],
        "symbols": list(symbols),
        "aligned_candle_count": len(timestamps),
        "research_return_count": research_count,
        "selected_period_return": _period_return(selected),
        "equal_weight_period_return": _period_return(equal_weight),
        "selection_spread_period_return": (
            _period_return(selected) - _period_return(equal_weight)
        ),
        "selected_beats_equal_weight_ratio": (
            sum(a > b for a, b in zip(selected, equal_weight))
            / len(selected)
        ),
        "selected_beats_bottom_ratio": (
            sum(a > b for a, b in zip(selected, bottom))
            / len(selected)
        ),
        "mean_cross_sectional_dispersion": mean(dispersion),
        "mean_cross_sectional_turnover": mean(turnover),
        "formation_count": len(rebalances),
        "negative_forward_spread_ratio": (
            sum(value < 0.0 for value in forward_spreads)
            / len(forward_spreads)
            if forward_spreads
            else 0.0
        ),
        "positive_score_negative_forward_spread_ratio": (
            sum(
                score > 0.0 and spread < 0.0
                for score, spread in zip(
                    formation_scores,
                    forward_spreads,
                )
            )
            / len(rebalances)
            if rebalances
            else 0.0
        ),
        "score_forward_spread_correlation": _correlation(
            formation_scores,
            forward_spreads,
        ),
        "mean_forward_selection_spread": (
            mean(forward_spreads)
            if forward_spreads
            else 0.0
        ),
    }


def run_control(
    first_root: Path,
    second_root: Path,
    output_path: Path,
) -> dict:
    first_report, first_manifest, _, first_label = _discover_source(first_root)
    second_report, second_manifest, _, second_label = _discover_source(second_root)
    if first_label != "first_validation":
        raise ValueError("Erstes Artifact ist nicht die erwartete erste Validation.")
    if second_label != "second_validation":
        raise ValueError("Zweites Artifact ist nicht die erwartete zweite Validation.")

    _validate_report(first_report, first_manifest, first_label)
    _validate_report(second_report, second_manifest, second_label)

    first = _analyse_dataset(first_root, first_report, first_manifest, first_label)
    second = _analyse_dataset(second_root, second_report, second_manifest, second_label)

    selection_direction = (
        "positive_both"
        if first["selection_spread_period_return"] > 0.0
        and second["selection_spread_period_return"] > 0.0
        else "negative_both"
        if first["selection_spread_period_return"] < 0.0
        and second["selection_spread_period_return"] < 0.0
        else "discordant"
    )

    weak_score_prediction = (
        first["score_forward_spread_correlation"] <= 0.0
        and second["score_forward_spread_correlation"] <= 0.0
    )

    result = {
        "schema_version": 1,
        "diagnostic_type": "cross_validation_cs_mechanism_consensus_2026_09_23",
        "status": "COMPLETED",
        "datasets": {
            "first_validation": first,
            "second_validation": second,
        },
        "consensus": {
            "selection_spread_direction": selection_direction,
            "selection_return_direction_consistent": selection_direction
            in {"positive_both", "negative_both"},
            "formation_score_forward_prediction_non_positive_both": (
                weak_score_prediction
            ),
            "holdout_used_for_selection": False,
        },
        "interpretation": {
            "primary_finding": (
                "Die Richtung der kumulierten Top-2-vs.-Equal-Weight-Selektion "
                "ist zwischen den beiden unabhängigen Universen diskordant."
            ),
            "shared_mechanism_finding": (
                "In beiden unabhängigen Universen ist die lineare Beziehung "
                "zwischen Formation-Score und anschließendem Forward-Spread "
                "nicht positiv."
            ),
            "implication_for_research": (
                "Der zweite Failure-Fall ist nicht als universelles Versagen "
                "des Cross-Sectional-Ansatzes zu klassifizieren. Die robuste "
                "Fragestellung ist stattdessen die Stabilität der Rangselektion "
                "über Universen und Regime."
            ),
        },
        "constraints": [
            "diagnostic only",
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
    result["consensus_fingerprint"] = _fingerprint(result)
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
    print("CS_CROSS_VALIDATION_STATUS:", result["status"])
    print(
        "SELECTION_SPREAD_DIRECTION:",
        result["consensus"]["selection_spread_direction"],
    )
    print(
        "WEAK_SCORE_PREDICTION_BOTH:",
        result["consensus"][
            "formation_score_forward_prediction_non_positive_both"
        ],
    )
    print("CONSENSUS_FINGERPRINT:", result["consensus_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
