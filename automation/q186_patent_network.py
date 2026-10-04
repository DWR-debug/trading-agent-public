"""Deterministic Q186 technology-network construction.

Pre-formal only. The functions here construct a directed five-year citation
network using only citation observations available by a supplied cutoff and
exclude self-citations. No returns, ranking, optimization or candidate
selection are used.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Iterable, Mapping

def five_year_start(cutoff: date) -> date:
    try:
        return cutoff.replace(year=cutoff.year - 5)
    except ValueError:
        return cutoff.replace(month=2, day=28, year=cutoff.year - 5)

def build_edge_weights(
    citations: Iterable[Mapping[str, object]],
    cutoff: date,
) -> dict[tuple[str, str], float]:
    start = five_year_start(cutoff)
    counts: Counter[tuple[str, str]] = Counter()
    denominator: Counter[str] = Counter()

    for row in citations:
        cited = str(row["cited_firm"])
        citing = str(row["citing_firm"])
        public_date = row["citation_public_date"]
        if not isinstance(public_date, date):
            raise TypeError("citation_public_date must be a datetime.date")
        if cited == citing:
            continue
        if not (start < public_date <= cutoff):
            continue
        edge = (cited, citing)
        counts[edge] += 1
        denominator[citing] += 1

    return {
        edge: count / denominator[citing]
        for edge, count in counts.items()
        if denominator[citing] > 0
    }

def compute_grant_shock(
    grants: Iterable[Mapping[str, object]],
    edge_weights: Mapping[tuple[str, str], float],
    event_date: date,
) -> dict[str, float]:
    grants_by_upstream: Counter[str] = Counter()
    for row in grants:
        grant_date = row["grant_date"]
        if not isinstance(grant_date, date):
            raise TypeError("grant_date must be a datetime.date")
        if grant_date == event_date:
            grants_by_upstream[str(row["upstream_firm"])] += 1

    shock: dict[str, float] = {}
    for (upstream, downstream), weight in edge_weights.items():
        n_grants = grants_by_upstream.get(upstream, 0)
        if n_grants:
            shock[downstream] = shock.get(downstream, 0.0) + weight * n_grants
    return shock

def validate_edge_direction(
    edge_weights: Mapping[tuple[str, str], float],
) -> None:
    if any(src == dst for src, dst in edge_weights):
        raise ValueError("SELF_CITATION_EDGE_PRESENT")
    for (upstream, downstream), weight in edge_weights.items():
        if not upstream or not downstream:
            raise ValueError("EMPTY_FIRM_ID")
        if weight <= 0:
            raise ValueError("NON_POSITIVE_EDGE_WEIGHT")
