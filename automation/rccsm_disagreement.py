"""Mechanism-disagreement topology derived from the frozen Q069 candidate bank.

Design/feasibility only. No performance labels or selection are consumed.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from typing import Any

from automation.q069_candidate_bank import CANDIDATES, candidate_targets_at
from automation.rccsm_state import fingerprint


def disagreement_at(
    assets: Mapping[str, Sequence[Any]],
    index: int,
    *,
    symbols: Sequence[str],
) -> dict[str, Any]:
    targets = candidate_targets_at(assets, index, symbols=symbols)
    selected: dict[str, set[str]] = {
        name: {symbol for symbol, weight in weights.items() if float(weight) > 0}
        for name, weights in targets.items()
        if sum(float(weight) for weight in weights.values()) > 0
    }
    pairs = list(itertools.combinations(sorted(selected), 2))
    overlaps = []
    for left, right in pairs:
        union = selected[left] | selected[right]
        intersection = selected[left] & selected[right]
        overlaps.append(len(intersection) / len(union) if union else 1.0)
    mean_overlap = sum(overlaps) / len(overlaps) if overlaps else 1.0
    payload = {
        "schema_version": 1,
        "index": index,
        "symbols": list(symbols),
        "candidate_ids": list(CANDIDATES),
        "active_candidate_ids": sorted(selected),
        "pair_count": len(pairs),
        "mean_pairwise_jaccard_overlap": mean_overlap,
        "mechanism_disagreement": 1.0 - mean_overlap,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "performance_evaluation": False,
        "uses_future_data": False,
    }
    payload["provenance_fingerprint"] = fingerprint(payload)
    return payload
