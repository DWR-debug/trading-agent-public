"""Controlled entry point for immutable, resumable Research runs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from automation.backtest_runner import run_all
from automation.checkpoint import ResearchCheckpointStore, checkpoint_key
from automation.research_run import build_run_identity, same_run_identity
from config.parameter_space import ParameterSpace
from data.market_store import MarketDataStore
from research.protocol import ResearchProtocol
from research.asset_universes import datasets_for
from validation.research_gates import evaluate_research_gates


DEFAULT_RESEARCH_RUN_OPTIONS = {
    "optimizer_top_n": 5,
    "selection_profile": "score_max",
    "train_ratio": 0.7,
    "rolling_train_ratio": 0.5,
    "rolling_test_ratio": 0.1,
    "rolling_step_ratio": 0.1,
    "minimum_trades_required": 30,
}

def _canonical_json(value) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def result_fingerprint(report: dict) -> str:
    payload = dict(report)
    payload.pop("result_fingerprint", None)
    payload.pop("generated_at", None)
    payload.pop("updated_at", None)
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def verify_result_fingerprint(report: dict) -> None:
    stored = report.get("result_fingerprint")
    if not isinstance(stored, str) or stored != result_fingerprint(report):
        raise ValueError(
            "Research-Ergebnis besitzt keinen gültigen Fingerprint."
        )

def _write_manifest(path: Path, identity: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                **identity,
            },
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    temp.replace(path)


def load_or_create_run_manifest(
    datasets,
    *,
    store,
    protocol,
    parameter_space,
    path,
    data_manifest_path=None,
    execution_config=None,
):
    manifest_path = Path(path)
    identity = build_run_identity(
        list(datasets),
        store,
        protocol,
        parameter_space,
        data_manifest_path=data_manifest_path,
        execution_config=execution_config,
    )

    if manifest_path.exists():
        existing = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        if not same_run_identity(existing, identity):
            raise RuntimeError(
                "Research-Manifest passt nicht zum aktuellen "
                "Dataset/Code/Protokoll/Parameterraum. "
                "Resume wurde aus Sicherheitsgründen verweigert."
            )
        return existing

    _write_manifest(manifest_path, identity)
    return json.loads(
        manifest_path.read_text(encoding="utf-8")
    )


def run_research(
    datasets,
    *,
    store=None,
    parameter_space=None,
    protocol=None,
    output_dir="reports",
    checkpoint_path="research/checkpoints/latest.json",
    manifest_path="research/run_manifest.json",
    data_manifest_path="research/data_manifest.json",
    resume=False,
    **run_options,
):
    store = store or MarketDataStore()
    parameter_space = parameter_space or ParameterSpace()
    protocol = protocol or ResearchProtocol()

    execution_config = {
        **DEFAULT_RESEARCH_RUN_OPTIONS,
        **run_options,
    }

    manifest = load_or_create_run_manifest(
        datasets,
        store=store,
        protocol=protocol,
        parameter_space=parameter_space,
        path=manifest_path,
        data_manifest_path=data_manifest_path,
        execution_config=execution_config,
    )

    report, report_path = run_all(
        datasets,
        store=store,
        parameter_space=parameter_space,
        protocol=protocol,
        output_dir=output_dir,
        checkpoint_path=checkpoint_path,
        resume=resume,
        run_fingerprint=manifest["run_fingerprint"],
        **execution_config,
    )

    gate_failures = []

    for result in report["datasets"]:
        candles = tuple(
            store.load(result["symbol"], result["interval"])
        )
        gate_report = evaluate_research_gates(
            result,
            candles,
        )
        result["research_gates"] = gate_report
        result["statistical_diagnostics"] = {
            "multiple_testing": {
                "parameter_space_candidate_count": result.get(
                    "optimization_candidate_count"
                ),
                "reported_top_n": result.get(
                    "optimization_reported_top_n"
                ),
                "selection_profile": result.get(
                    "walk_forward", {}
                ).get("selection_profile"),
                "holdout_was_used_for_candidate_selection": False,
                "interpretation": (
                    "Die Kandidatenauswahl erfolgt ausschließlich auf "
                    "dem Research-Abschnitt; der finale Holdout bleibt "
                    "bis zur Auswahl unberührt. Die Suchraumgröße wird "
                    "zur Dokumentation des Multiple-Testing-Exposures "
                    "gespeichert."
                ),
            },
            "permutation": {
                "positive_tail_probability": result.get(
                    "holdout", {}
                ).get("permutation_positive_tail_probability"),
                "trials": result.get(
                    "protocol", {}
                ).get("permutation_trials"),
                "seed": result.get("protocol", {}).get("permutation_seed"),
                "diagnostic_only": True,
                "unadjusted": True,
                "interpretation": (
                    "Sign-Permutationsdiagnostik des Holdout-Trade-PnL; "
                    "kein eigenständiges Profitabilitäts-Gate und keine "
                    "multiple-testing-korrigierte Signifikanzbehauptung."
                ),
            },
        }
        if not gate_report["passed"]:
            gate_failures.extend(
                f"{result['symbol']} {result['interval']}: {name}"
                for name in gate_report["failed_gates"]
            )

    report["status"] = "PASSED" if not gate_failures else "BLOCKED"
    report["failed_gates"] = gate_failures
    report["evaluation_summary"] = {
        "dataset_count": len(report["datasets"]),
        "passed_dataset_count": sum(
            1
            for item in report["datasets"]
            if item["research_gates"]["passed"]
        ),
        "blocked_dataset_count": sum(
            1
            for item in report["datasets"]
            if not item["research_gates"]["passed"]
        ),
        "evidence_scope": (
            "multi_dataset"
            if len(report["datasets"]) > 1
            else "single_dataset"
        ),
        "single_backtest_decision": False,
        "interpretation": (
            "Der Report dient als reproduzierbarer Research-Nachweis. "
            "Eine einzelne Backtest-Beobachtung gilt nicht als ausreichende "
            "Entscheidungsgrundlage; Ergebnisse sind im Kontext der "
            "gesamten Gate- und Evidenzkette zu bewerten."
        ),
    }
    report["run_manifest"] = manifest
    report["result_fingerprint"] = result_fingerprint(report)

    report_path = Path(report_path)
    report_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    checkpoint = ResearchCheckpointStore(checkpoint_path)
    checkpoint_state = checkpoint.load()
    if checkpoint_state is not None:
        checkpoint_state["run_fingerprint"] = manifest["run_fingerprint"]
        checkpoint_state["research_status"] = report["status"]
        checkpoint_state["failed_gates"] = list(report["failed_gates"])
        checkpoint_state["research_gates"] = {
            checkpoint_key(result["symbol"], result["interval"]): result["research_gates"]
            for result in report["datasets"]
        }
        checkpoint.save(checkpoint_state)

    return report, report_path


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--universe", default=None)
    parser.add_argument("--data-manifest", default="research/data_manifest.json")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument(
        "--checkpoint",
        default="research/checkpoints/latest.json",
    )
    parser.add_argument(
        "--manifest",
        default="research/run_manifest.json",
    )
    args = parser.parse_args()

    datasets = (
        [
            ("BTCUSDT", "1h"),
            ("BTCUSDT", "15m"),
            ("ETHUSDT", "1h"),
            ("ETHUSDT", "15m"),
        ]
        if args.universe is None
        else [
            (symbol, interval)
            for symbol, interval, _target in datasets_for(args.universe)
        ]
    )

    report, path = run_research(
        datasets,
        output_dir=args.output_dir,
        checkpoint_path=args.checkpoint,
        manifest_path=args.manifest,
        data_manifest_path=args.data_manifest,
        resume=args.resume,
    )

    print(f"RESEARCH_REPORT: {path}")
    print(
        "RUN_FINGERPRINT: "
        + report["run_manifest"]["run_fingerprint"]
    )


if __name__ == "__main__":
    main()