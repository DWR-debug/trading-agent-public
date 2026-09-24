"""Paper-only 30-day experiment harness with checkpoint/resume.

The harness evaluates one already evidence-eligible fixed strategy return stream.
It never selects among strategies and never places orders.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from automation.checkpoint import ResearchCheckpointStore, checkpoint_fingerprint
from research.evidence_contract import (
    EvidenceContractError,
    EvidenceSnapshot,
    GateResult,
    evaluate_evidence,
)

HORIZON_DAYS = 30


class Paper30DayExperimentError(ValueError):
    """Raised when the 30-day paper experiment contract is violated."""


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _finite_return(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise Paper30DayExperimentError("Daily returns must be numeric.") from exc
    if result <= -1.0:
        raise Paper30DayExperimentError("Daily returns must be greater than -100%.")
    return result


def load_return_stream(path: Path) -> tuple[str, tuple[float, ...], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Paper30DayExperimentError("Return stream must be a JSON object.")

    strategy_id = payload.get("strategy_id")
    if not isinstance(strategy_id, str) or not strategy_id.strip():
        raise Paper30DayExperimentError("Return stream requires strategy_id.")

    returns = payload.get("daily_returns")
    if not isinstance(returns, list):
        raise Paper30DayExperimentError("Return stream requires daily_returns as a list.")
    if len(returns) != HORIZON_DAYS:
        raise Paper30DayExperimentError(
            f"Exactly {HORIZON_DAYS} daily returns are required."
        )

    net_of_costs = payload.get("net_of_costs")
    if net_of_costs is not True:
        raise Paper30DayExperimentError(
            "The 30-day harness requires returns already net of the declared execution-cost contract."
        )

    values = tuple(_finite_return(value) for value in returns)
    metadata = {
        "strategy_id": strategy_id,
        "net_of_costs": True,
        "source": payload.get("source", "UNSPECIFIED"),
        "cost_contract": payload.get("cost_contract"),
    }
    return strategy_id, values, metadata


def load_evidence(path: Path) -> EvidenceSnapshot:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Paper30DayExperimentError("Evidence snapshot must be a JSON object.")

    try:
        gates = tuple(
            GateResult(
                name=str(item["name"]),
                passed=bool(item["passed"]),
                observed=item.get("observed"),
                threshold=item.get("threshold"),
            )
            for item in payload["gates"]
        )
        return EvidenceSnapshot(
            trial_id=str(payload["trial_id"]),
            strategy_id=str(payload["strategy_id"]),
            status=str(payload["status"]),
            artifact_id=int(payload["artifact_id"]),
            artifact_digest_sha256=str(payload["artifact_digest_sha256"]),
            report_fingerprint_sha256=str(payload["report_fingerprint_sha256"]),
            manifest_fingerprint_sha256=str(payload["manifest_fingerprint_sha256"]),
            code_commit_sha=str(payload["code_commit_sha"]),
            research_count=int(payload["research_count"]),
            holdout_count=int(payload["holdout_count"]),
            holdout_used_for_selection=bool(payload["holdout_used_for_selection"]),
            gates=gates,
            paper_only=bool(payload.get("paper_only", True)),
            live_trading_enabled=bool(payload.get("live_trading_enabled", False)),
            orders_enabled=bool(payload.get("orders_enabled", False)),
        )
    except (KeyError, TypeError, ValueError, EvidenceContractError) as exc:
        raise Paper30DayExperimentError(
            f"Evidence snapshot violates the project contract: {exc}"
        ) from exc


def _validate_pair(
    strategy_id: str,
    evidence: EvidenceSnapshot,
    daily_returns: Sequence[float],
    initial_capital_eur: float,
) -> None:
    if strategy_id != evidence.strategy_id:
        raise Paper30DayExperimentError(
            "strategy_id must match the evidence-eligible strategy."
        )
    decision = evaluate_evidence(evidence)
    if not decision.eligible:
        raise Paper30DayExperimentError(
            "Evidence gate rejected the experiment: "
            f"{decision.reason}; failed_gates={list(decision.failed_gates)}"
        )
    if len(daily_returns) != HORIZON_DAYS:
        raise Paper30DayExperimentError(
            f"Exactly {HORIZON_DAYS} daily returns are required."
        )
    if initial_capital_eur <= 0.0:
        raise Paper30DayExperimentError("Initial capital must be > 0.")
    if evidence.paper_only is not True or evidence.live_trading_enabled is not False:
        raise Paper30DayExperimentError("Paper-only evidence contract violated.")
    if evidence.orders_enabled is not False:
        raise Paper30DayExperimentError("Orders must remain disabled.")


def _input_fingerprint(
    strategy_id: str,
    evidence: EvidenceSnapshot,
    daily_returns: Sequence[float],
    initial_capital_eur: float,
) -> str:
    return fingerprint(
        {
            "strategy_id": strategy_id,
            "trial_id": evidence.trial_id,
            "evidence": asdict(evidence),
            "daily_returns": list(daily_returns),
            "initial_capital_eur": initial_capital_eur,
            "horizon_days": HORIZON_DAYS,
        }
    )


def _resume_state(
    checkpoint: ResearchCheckpointStore,
    input_fp: str,
) -> dict[str, Any] | None:
    state = checkpoint.load()
    if state is None:
        return None
    if state.get("input_fingerprint") != input_fp:
        raise Paper30DayExperimentError(
            "Checkpoint gehört nicht exakt zu diesem Evidence-/Return-Stream."
        )
    return state


def run(
    *,
    evidence_path: str | Path,
    returns_path: str | Path,
    output_path: str | Path,
    checkpoint_path: str | Path,
    initial_capital_eur: float = 10.0,
    resume: bool = False,
    max_days: int | None = None,
) -> dict[str, Any]:
    evidence = load_evidence(Path(evidence_path))
    strategy_id, daily_returns, return_metadata = load_return_stream(Path(returns_path))
    _validate_pair(strategy_id, evidence, daily_returns, initial_capital_eur)

    input_fp = _input_fingerprint(
        strategy_id,
        evidence,
        daily_returns,
        initial_capital_eur,
    )
    checkpoint = ResearchCheckpointStore(checkpoint_path)
    state = _resume_state(checkpoint, input_fp) if resume else None

    if state is None:
        processed = 0
        equity = float(initial_capital_eur)
        peak = equity
        max_drawdown = 0.0
        observations: list[dict[str, Any]] = []
    else:
        processed = int(state["processed_days"])
        equity = float(state["equity_eur"])
        peak = float(state["peak_equity_eur"])
        max_drawdown = float(state["maximum_drawdown_percent"])
        observations = list(state.get("observations", []))

    target_days = HORIZON_DAYS if max_days is None else min(HORIZON_DAYS, max(0, int(max_days)))
    if processed > target_days:
        raise Paper30DayExperimentError(
            "Checkpoint already progressed beyond the requested target_days."
        )

    for index in range(processed, target_days):
        period_return = daily_returns[index]
        equity_before = equity
        pnl = equity_before * period_return
        equity += pnl
        peak = max(peak, equity)
        max_drawdown = max(
            max_drawdown,
            (1.0 - equity / peak) * 100.0,
        )
        observations.append(
            {
                "day": index + 1,
                "return": period_return,
                "equity_before_eur": equity_before,
                "pnl_eur": pnl,
                "equity_after_eur": equity,
                "peak_equity_eur": peak,
                "drawdown_percent": (1.0 - equity / peak) * 100.0,
            }
        )
        checkpoint.save(
            {
                "experiment": "paper_30_day",
                "status": "RUNNING" if index + 1 < HORIZON_DAYS else "COMPLETED",
                "strategy_id": strategy_id,
                "trial_id": evidence.trial_id,
                "processed_days": index + 1,
                "equity_eur": equity,
                "peak_equity_eur": peak,
                "maximum_drawdown_percent": max_drawdown,
                "observations": observations,
                "input_fingerprint": input_fp,
            }
        )

    result = {
        "schema_version": 1,
        "experiment": "paper_30_day",
        "status": "COMPLETED" if target_days == HORIZON_DAYS else "CHECKPOINTED",
        "strategy_id": strategy_id,
        "trial_id": evidence.trial_id,
        "horizon_days": HORIZON_DAYS,
        "processed_days": target_days,
        "initial_capital_eur": initial_capital_eur,
        "final_equity_eur": equity,
        "total_return_percent": (equity / initial_capital_eur - 1.0) * 100.0,
        "maximum_drawdown_percent": max_drawdown,
        "minimum_equity_eur": min(
            [initial_capital_eur] + [float(item["equity_after_eur"]) for item in observations]
        ),
        "return_stream_fingerprint": fingerprint(
            {"strategy_id": strategy_id, "daily_returns": list(daily_returns)}
        ),
        "input_fingerprint": input_fp,
        "evidence_eligibility": {
            "status": evidence.status,
            "holdout_used_for_selection": evidence.holdout_used_for_selection,
            "paper_only": evidence.paper_only,
            "live_trading_enabled": evidence.live_trading_enabled,
            "orders_enabled": evidence.orders_enabled,
        },
        "return_metadata": return_metadata,
        "observations": observations,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    if target_days == HORIZON_DAYS:
        result["report_fingerprint"] = fingerprint(result)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Paper-only 30-day experiment harness.")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--returns", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--initial-capital-eur", type=float, default=10.0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    report = run(
        evidence_path=args.evidence,
        returns_path=args.returns,
        output_path=args.output,
        checkpoint_path=args.checkpoint,
        initial_capital_eur=args.initial_capital_eur,
        resume=args.resume,
    )
    print("PAPER_30_DAY_STATUS:", report["status"])
    print("PAPER_30_DAY_FINAL_EQUITY_EUR:", report["final_equity_eur"])
    print("PAPER_30_DAY_MAX_DD_PERCENT:", report["maximum_drawdown_percent"])
    if "report_fingerprint" in report:
        print("PAPER_30_DAY_REPORT_FINGERPRINT:", report["report_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
