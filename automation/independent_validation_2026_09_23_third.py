"""Third independent validation of the fixed 50/50 + 10% vol-budget candidate.

This module reuses the already validated calculation primitives from the existing
candidate-validation control. Only the new pre-registered universes change.

Research-only: no optimization, selection, production mutation or orders.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from automation import candidate_validation_50_50_vol_budget as base
from config import settings
from research.asset_universes import get_universe, list_universes

TREND_UNIVERSE = "validation_2026_09_23_third_trend"
CS_UNIVERSE = "validation_2026_09_23_third_cs"
TARGET_COUNT = base.TARGET_COUNT
RESEARCH_COUNT = base.RESEARCH_COUNT
HOLDOUT_COUNT = base.HOLDOUT_COUNT


def _assert_global_disjoint() -> None:
    new_symbols = set(get_universe(TREND_UNIVERSE).symbols) | set(
        get_universe(CS_UNIVERSE).symbols
    )
    if len(new_symbols) != len(
        get_universe(TREND_UNIVERSE).symbols
    ) + len(get_universe(CS_UNIVERSE).symbols):
        raise ValueError("Neue Validierungsuniversen sind intern nicht disjunkt.")

    prior_symbols: set[str] = set()
    for universe in list_universes():
        if universe.name in {TREND_UNIVERSE, CS_UNIVERSE}:
            continue
        prior_symbols.update(universe.symbols)

    overlap = sorted(new_symbols & prior_symbols)
    if overlap:
        raise ValueError(
            "Neue Validierungsuniversen überschneiden bestehende Research-Universen: "
            + ", ".join(overlap)
        )


def _manifest(path: Path, universe_name: str) -> dict:
    return base._manifest(path, universe_name)


def run_validation(
    trend_data_dir: Path,
    trend_manifest_path: Path,
    cs_data_dir: Path,
    cs_manifest_path: Path,
    output_path: Path,
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only-Sicherheitsvertrag verletzt.")

    _assert_global_disjoint()

    trend_manifest = _manifest(trend_manifest_path, TREND_UNIVERSE)
    cs_manifest = _manifest(cs_manifest_path, CS_UNIVERSE)
    trend = base._assets(trend_data_dir, trend_manifest)
    cs = base._assets(cs_data_dir, cs_manifest)

    if set(trend) & set(cs):
        raise ValueError("Validation-Universen sind nicht disjunkt.")

    trend_weights = base._build_weight_path(
        trend,
        base.TREND_STRATEGY,
    )
    cs_weights = base._cs_weights(cs)
    all_assets = {**trend, **cs}

    adjusted = {
        symbol: base._yahoo_adjclose(
            symbol,
            bars[0].timestamp,
            bars[-1].timestamp,
        )
        for symbol, bars in all_assets.items()
    }
    adjusted_archive = {
        symbol: [
            [bar.timestamp.isoformat(), adjusted[symbol][bar.timestamp]]
            for bar in bars
        ]
        for symbol, bars in all_assets.items()
    }
    adjusted_close_fingerprints = {
        symbol: base._fp(values)
        for symbol, values in adjusted_archive.items()
    }

    rows = base._align(
        trend,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in trend},
        cs,
        cs_weights,
        {symbol: adjusted[symbol] for symbol in cs},
    )
    expected_return_count = RESEARCH_COUNT + HOLDOUT_COUNT
    if len(rows) < expected_return_count:
        raise ValueError(f"Zu wenige Returns: {len(rows)}")

    scenarios = {
        name: base._scenario(rows, multiplier)
        for name, multiplier in base.COST_SCENARIOS
    }

    adjusted_archive_document = {
        "schema_version": 1,
        "source": "yahoo_chart_adjusted_close",
        "datasets": adjusted_archive,
    }
    adjusted_archive_fingerprint = base._fp(adjusted_archive_document)
    adjusted_archive_document["archive_fingerprint"] = adjusted_archive_fingerprint
    archive_path = output_path.with_name("adjusted_close_archive.json")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(
        json.dumps(
            adjusted_archive_document,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    gates = base._gates(scenarios, base.ResearchGateConfig())
    reference = scenarios["base"]["vol_budget_10pct"]

    report = {
        "schema_version": 1,
        "diagnostic_type": "third_independent_candidate_validation_2026_09_23",
        "status": "COMPLETED",
        "candidate_status": (
            "PASS" if gates["all_relevant_checks_passed"] else "BLOCKED"
        ),
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "preregistration": {
            "document": "docs/third_independent_validation_2026_09_23_preregistration.md",
            "concrete_universes_fixed_before_data_acquisition": True,
            "selection_after_results": False,
            "asset_replacement_after_results": False,
        },
        "source": {
            "trend_universe": TREND_UNIVERSE,
            "trend_symbols": list(get_universe(TREND_UNIVERSE).symbols),
            "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
            "trend_source_run_id": trend_manifest.get("provenance", {}).get("run_id"),
            "cs_universe": CS_UNIVERSE,
            "cs_symbols": list(get_universe(CS_UNIVERSE).symbols),
            "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
            "cs_source_run_id": cs_manifest.get("provenance", {}).get("run_id"),
            "raw_candle_count_per_asset": TARGET_COUNT,
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "common_return_count": len(rows),
            "independent_asset_universes": True,
            "fully_disjoint_from_prior_universes": True,
            "out_of_time_validation": False,
            "adjusted_close_fingerprints": adjusted_close_fingerprints,
            "adjusted_close_archive_fingerprint": adjusted_archive_fingerprint,
        },
        "methodology": {
            "architecture": (
                "fixed 50/50 Cross-Asset SMA 50/200 inverse-volatility "
                "+ 12-1 CS momentum top-2 long-only"
            ),
            "vol_budget_target_annualized": base.TARGET_VOL,
            "vol_budget_window_sessions": base.VOL_WINDOW,
            "execution_model": (
                "close(t) decision -> next-session open -> following-open return"
            ),
            "research_holdout_split": f"{RESEARCH_COUNT} / {HOLDOUT_COUNT}",
            "rolling_windows": "5 fixed windows covering the full Research span",
            "cost_scenarios": [name for name, _ in base.COST_SCENARIOS],
            "optimization_used": False,
            "selection_profile_used": False,
            "signal_parameters_changed": False,
            "sleeve_weights_changed": False,
            "production_strategy_changed": False,
            "orders_enabled": False,
            "total_return_sensitivity": (
                "Adjusted-Close dividend/split sensitivity on the same "
                "open-to-open portfolio path; diagnostic only"
            ),
        },
        "reference_unscaled": scenarios["base"]["unscaled_baseline"],
        "scenarios": scenarios,
        "gate_contract": gates,
        "total_return_sensitivity_delta": base._delta(
            reference["price_only"],
            reference["total_return_sensitivity"],
        ),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    report["report_fingerprint"] = base._fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend-data-dir", required=True)
    parser.add_argument("--trend-manifest", required=True)
    parser.add_argument("--cs-data-dir", required=True)
    parser.add_argument("--cs-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_validation(
        Path(args.trend_data_dir),
        Path(args.trend_manifest),
        Path(args.cs_data_dir),
        Path(args.cs_manifest),
        Path(args.output),
    )
    print("INDEPENDENT_VALIDATION_STATUS:", report["status"])
    print("CANDIDATE_STATUS:", report["candidate_status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    print(
        "ALL_RELEVANT_CHECKS_PASSED:",
        report["gate_contract"]["all_relevant_checks_passed"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
