"""Validation and analysis helpers for the immutable Research trial ledger.

The ledger records what was tested, on which evidence scope, and whether a
selection event occurred. It deliberately distinguishes raw trial count from
declared independent trial count and does not invent missing statistical
inputs.

It also provides a small PBO consumer for precomputed CSCV split results and
adapts trial families to the existing PSR/DSR implementation.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any, Iterable, Sequence

from research.statistical_validation import (
    DeflatedSharpeResult,
    StatisticalValidationError,
    deflated_sharpe_ratio,
)

LEDGER_SCHEMA_VERSION = 1
VALID_STATUSES = {
    "diagnostic_completed",
    "validated_pass",
    "validated_fail",
    "archived_rejected",
    "archived_diagnostic",
    "governance_only",
}


class TrialLedgerError(ValueError):
    """Raised when the trial ledger contract is violated."""


@dataclass(frozen=True)
class PBOResult:
    """Probability of backtest overfitting from precomputed CSCV splits."""

    split_count: int
    overfit_count: int
    probability: float
    logit_median: float
    logit_values: tuple[float, ...]


def _finite(value: float, label: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise TrialLedgerError(f"{label} muss endlich sein.")
    return value


def validate_trial(record: dict[str, Any]) -> None:
    required = {
        "trial_id",
        "recorded_at",
        "status",
        "research_family",
        "hypothesis",
        "data_scope",
        "search_scope",
        "selection",
        "statistical_evidence",
        "safety",
    }
    missing = sorted(required.difference(record))
    if missing:
        raise TrialLedgerError(f"Fehlende Trial-Felder: {', '.join(missing)}")

    if record["status"] not in VALID_STATUSES:
        raise TrialLedgerError(f"Unbekannter Trial-Status: {record['status']}")

    scope = record["data_scope"]
    for key in (
        "research_count",
        "holdout_count",
        "holdout_used_for_selection",
        "artifact_ids",
    ):
        if key not in scope:
            raise TrialLedgerError(f"Fehlendes data_scope-Feld: {key}")

    if not isinstance(scope["holdout_used_for_selection"], bool):
        raise TrialLedgerError("holdout_used_for_selection muss bool sein.")
    if not isinstance(scope["artifact_ids"], list):
        raise TrialLedgerError("artifact_ids muss eine Liste sein.")

    search = record["search_scope"]
    for key in (
        "raw_trial_count",
        "independent_trial_count",
        "parameter_search",
        "threshold_search",
        "variant_search",
    ):
        if key not in search:
            raise TrialLedgerError(f"Fehlendes search_scope-Feld: {key}")

    raw_count = search["raw_trial_count"]
    indep_count = search["independent_trial_count"]
    if raw_count is not None and int(raw_count) < 1:
        raise TrialLedgerError("raw_trial_count muss >= 1 oder null sein.")
    if indep_count is not None and int(indep_count) < 1:
        raise TrialLedgerError(
            "independent_trial_count muss >= 1 oder null sein."
        )
    if (
        raw_count is not None
        and indep_count is not None
        and int(indep_count) > int(raw_count)
    ):
        raise TrialLedgerError(
            "independent_trial_count darf raw_trial_count nicht überschreiten."
        )

    if not all(
        isinstance(search[name], bool)
        for name in ("parameter_search", "threshold_search", "variant_search")
    ):
        raise TrialLedgerError("search_scope boolean fields müssen bool sein.")

    selection = record["selection"]
    for key in (
        "selected",
        "selection_method",
        "selection_family_id",
        "selection_metric",
    ):
        if key not in selection:
            raise TrialLedgerError(f"Fehlendes selection-Feld: {key}")
    if not isinstance(selection["selected"], bool):
        raise TrialLedgerError("selection.selected muss bool sein.")

    statistical = record["statistical_evidence"]
    for key in (
        "psr_probability",
        "dsr_probability",
        "pbo_probability",
        "trial_sharpes",
        "independent_trial_count",
        "ready",
    ):
        if key not in statistical:
            raise TrialLedgerError(
                f"Fehlendes statistical_evidence-Feld: {key}"
            )
    if not isinstance(statistical["ready"], bool):
        raise TrialLedgerError("statistical_evidence.ready muss bool sein.")

    if (
        statistical["dsr_probability"] is not None
        and not 0.0 <= _finite(
            statistical["dsr_probability"], "dsr_probability"
        ) <= 1.0
    ):
        raise TrialLedgerError("dsr_probability muss zwischen 0 und 1 liegen.")

    if (
        statistical["psr_probability"] is not None
        and not 0.0 <= _finite(
            statistical["psr_probability"], "psr_probability"
        ) <= 1.0
    ):
        raise TrialLedgerError("psr_probability muss zwischen 0 und 1 liegen.")

    if (
        statistical["pbo_probability"] is not None
        and not 0.0 <= _finite(
            statistical["pbo_probability"], "pbo_probability"
        ) <= 1.0
    ):
        raise TrialLedgerError("pbo_probability muss zwischen 0 und 1 liegen.")

    if not (
        statistical["ready"]
        or (
            statistical["trial_sharpes"] is None
            and statistical["dsr_probability"] is None
            and statistical["pbo_probability"] is None
        )
    ):
        # A record marked ready must expose at least the actual probability
        # inputs it claims to have computed.
        if statistical["dsr_probability"] is None:
            raise TrialLedgerError(
                "ready=True erfordert dsr_probability oder muss als nicht-ready markiert sein."
            )

    safety = record["safety"]
    if safety != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }:
        raise TrialLedgerError("Safety contract verletzt.")


def validate_ledger(ledger: dict[str, Any]) -> None:
    if ledger.get("schema_version") != LEDGER_SCHEMA_VERSION:
        raise TrialLedgerError("Unbekannte Ledger-Schema-Version.")

    trials = ledger.get("trials")
    if not isinstance(trials, list) or not trials:
        raise TrialLedgerError("Ledger muss mindestens einen Trial enthalten.")

    seen: set[str] = set()
    for record in trials:
        validate_trial(record)
        trial_id = record["trial_id"]
        if trial_id in seen:
            raise TrialLedgerError(f"Doppelter trial_id: {trial_id}")
        seen.add(trial_id)


def load_ledger(path: Path) -> dict[str, Any]:
    ledger = json.loads(path.read_text(encoding="utf-8"))
    validate_ledger(ledger)
    return ledger


def summarize_trial_families(
    ledger: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    validate_ledger(ledger)
    families: dict[str, dict[str, Any]] = {}

    for record in ledger["trials"]:
        family_id = record["selection"]["selection_family_id"]
        family = families.setdefault(
            family_id,
            {
                "trial_ids": [],
                "raw_trial_counts": [],
                "independent_trial_counts": [],
                "selected_trial_ids": [],
                "statuses": [],
            },
        )
        family["trial_ids"].append(record["trial_id"])
        family["statuses"].append(record["status"])

        raw = record["search_scope"]["raw_trial_count"]
        indep = record["search_scope"]["independent_trial_count"]
        if raw is not None:
            family["raw_trial_counts"].append(int(raw))
        if indep is not None:
            family["independent_trial_counts"].append(int(indep))
        if record["selection"]["selected"]:
            family["selected_trial_ids"].append(record["trial_id"])

    for family in families.values():
        family["raw_trial_count_max"] = (
            max(family["raw_trial_counts"])
            if family["raw_trial_counts"]
            else None
        )
        family["independent_trial_count_max"] = (
            max(family["independent_trial_counts"])
            if family["independent_trial_counts"]
            else None
        )

    return families


def compute_dsr_for_trial(
    returns: Iterable[float],
    *,
    trial_sharpes: Sequence[float],
    independent_trial_count: int,
    null_mean_sharpe: float = 0.0,
) -> DeflatedSharpeResult:
    """Explicit bridge to the project's DSR implementation."""
    return deflated_sharpe_ratio(
        returns,
        independent_trial_count=independent_trial_count,
        trial_sharpes=trial_sharpes,
        null_mean_sharpe=null_mean_sharpe,
    )


def _percentile_rank(values: Sequence[float], observed: float) -> float:
    ordered = sorted(float(value) for value in values)
    n = len(ordered)
    less = sum(value < observed for value in ordered)
    equal = sum(value == observed for value in ordered)
    mid_rank = less + (equal + 1) / 2.0
    return mid_rank / (n + 1.0)


def compute_pbo_from_cscv(
    split_results: Sequence[dict[str, Sequence[float]]],
) -> PBOResult:
    """Compute PBO from precomputed CSCV IS/OOS Sharpe vectors.

    Each split must contain equal-length 'is_sharpes' and 'oos_sharpes'.
    The IS winner's OOS rank is converted to the CSCV logit statistic
    log(omega / (1 - omega)); PBO is the fraction of negative logits.
    """

    if not split_results:
        raise TrialLedgerError("Mindestens ein CSCV-Split wird benötigt.")

    logits: list[float] = []
    for split in split_results:
        if set(split) != {"is_sharpes", "oos_sharpes"}:
            raise TrialLedgerError(
                "Jeder CSCV-Split benötigt exakt is_sharpes und oos_sharpes."
            )

        is_values = tuple(_finite(v, "is_sharpe") for v in split["is_sharpes"])
        oos_values = tuple(_finite(v, "oos_sharpe") for v in split["oos_sharpes"])
        if len(is_values) < 2 or len(is_values) != len(oos_values):
            raise TrialLedgerError(
                "IS/OOS-Sharpe-Vektoren müssen gleiche Länge >= 2 besitzen."
            )

        winner_index = max(range(len(is_values)), key=is_values.__getitem__)
        omega = _percentile_rank(oos_values, oos_values[winner_index])
        omega = min(max(omega, 1e-12), 1.0 - 1e-12)
        logits.append(math.log(omega / (1.0 - omega)))

    return PBOResult(
        split_count=len(logits),
        overfit_count=sum(value < 0.0 for value in logits),
        probability=sum(value < 0.0 for value in logits) / len(logits),
        logit_median=median(logits),
        logit_values=tuple(logits),
    )


def statistical_readiness(
    *,
    trial_sharpes: Sequence[float] | None,
    independent_trial_count: int | None,
    pbo_probability: float | None,
) -> dict[str, Any]:
    """Describe whether the ledger has enough inputs for selection-aware stats."""

    if trial_sharpes is None or independent_trial_count is None:
        dsr_ready = False
    else:
        dsr_ready = (
            len(tuple(trial_sharpes)) >= 2
            and 1 <= int(independent_trial_count) <= len(tuple(trial_sharpes))
        )

    pbo_ready = pbo_probability is not None
    return {
        "dsr_ready": dsr_ready,
        "pbo_ready": pbo_ready,
        "ready": dsr_ready or pbo_ready,
    }
