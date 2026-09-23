""""One-command gated research runner.

Prepares stock data, selects the largest common standard history that all
symbols can provide, then runs the existing resumable research.
No live trading.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from automation.prepare_research_data import prepare
from automation.research_workflow import run_research
from optimization.selection_profiles import (
    available_selection_profile_names,
    get_selection_profile,
)
from research.asset_universes import datasets_for, get_universe


def run_universe(
    universe: str,
    *,
    minimum_count: int = 1000,
    target_count: int | None = None,
    resume: bool = False,
    selection_profile: str = "score_max",
    run_root: str | Path | None = None,
    prepare_data: bool = True,
    prepared_data_manifest: str | Path | None = None,
):
    spec = get_universe(universe)
    profile = get_selection_profile(selection_profile)
    if minimum_count < 500:
        raise ValueError("minimum_count muss mindestens 500 sein.")

    root = (
        Path(run_root)
        if run_root is not None
        else Path("research/runs") / universe
    )
    root.mkdir(parents=True, exist_ok=True)
    data_manifest = (
        Path(prepared_data_manifest)
        if prepared_data_manifest is not None
        else root / "data_manifest.json"
    )
    run_manifest = root / "run_manifest.json"
    checkpoint = root / "checkpoint.json"
    output_dir = root / "reports"

    last_error = None
    selected_count = None
    data = None

    if prepare_data:
        candidates = (
            [target_count]
            if target_count is not None
            else list(dict.fromkeys((spec.target_count, 2000, 1500, 1000)))
        )
        candidates = [count for count in candidates if count >= minimum_count]

        for count in candidates:
            try:
                data, _ = prepare(
                    target_count=count,
                    output_path=data_manifest,
                    universe=universe,
                    minimum_count=minimum_count,
                )
                common_count = min(
                    item["candle_count"] for item in data["datasets"]
                )
                if common_count < count:
                    last_error = ValueError(
                        f"Gemeinsame Historie reicht nur für {common_count} "
                        f"statt {count} Candles."
                    )
                    continue

                selected_count = count
                break
            except ValueError as exc:
                last_error = exc

        if data is None or selected_count is None:
            raise RuntimeError(
                f"Keine gemeinsame Historie für {universe}. "
                f"Mindesthistorie={minimum_count}. Letzter Fehler: {last_error}"
            )
    else:
        if not data_manifest.exists():
            raise RuntimeError(
                f"Vorbereitetes Datenmanifest fehlt: {data_manifest}"
            )
        data = json.loads(data_manifest.read_text(encoding="utf-8"))
        if data.get("universe") != universe:
            raise RuntimeError(
                "Vorbereitetes Datenmanifest gehört zu einem anderen "
                f"Universum: {data.get('universe')!r}"
            )
        counts = [
            int(item["candle_count"])
            for item in data.get("datasets", [])
        ]
        if not counts or min(counts) < minimum_count:
            raise RuntimeError(
                f"Vorbereitetes Datenmanifest erfüllt die Mindesthistorie "
                f"nicht: {min(counts) if counts else 0} < {minimum_count}"
            )
        selected_count = int(data.get("target_count") or min(counts))

    datasets = [
        (symbol, interval)
        for symbol, interval, _ in datasets_for(universe)
    ]
    report, report_path = run_research(
        datasets,
        output_dir=output_dir,
        checkpoint_path=checkpoint,
        manifest_path=run_manifest,
        data_manifest_path=data_manifest,
        resume=resume,
        selection_profile=profile.name,
    )

    result = {
        "status": report.get("status"),
        "universe": universe,
        "selected_target_count": selected_count,
        "minimum_count": minimum_count,
        "selection_profile": profile.name,
        "data_manifest": str(data_manifest),
        "run_manifest": str(run_manifest),
        "run_fingerprint": report.get("run_manifest", {}).get("run_fingerprint"),
        "checkpoint": str(checkpoint),
        "report": str(report_path),
        "datasets": [
            {
                "symbol": item["symbol"],
                "candle_count": item["candle_count"],
                "data_start": item["data_start"],
                "data_end": item["data_end"],
            }
            for item in data["datasets"]
        ],
        "failed_gates": report.get("failed_gates", []),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Datenqualität + Research + Gates in einem Lauf."
    )
    parser.add_argument("--universe", required=True)
    parser.add_argument("--minimum-count", type=int, default=1000)
    parser.add_argument("--target-count", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--selection-profile",
        choices=available_selection_profile_names(),
        default="score_max",
    )
    args = parser.parse_args()

    report = run_universe(
        args.universe,
        minimum_count=args.minimum_count,
        target_count=args.target_count,
        resume=args.resume,
        selection_profile=args.selection_profile,
    )
    # A valid REJECT/BLOCKED result is a research outcome, not a runner error.
    # Technical failures still propagate as exceptions and produce a non-zero exit.
    raise SystemExit(0)


if __name__ == "__main__":
    main()
