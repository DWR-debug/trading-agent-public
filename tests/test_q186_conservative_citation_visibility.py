"""Synthetic contract tests for Q186 conservative citation visibility.

This module tests only the deterministic inclusion rule. It does not fetch data
and does not create scientific performance evidence.
"""
from __future__ import annotations

from datetime import date


def conservative_public_date(
    *,
    citing_patent_grant_date: date,
    upstream_patent_grant_date: date,
    citation_present_in_citing_grant_document: bool,
) -> date | None:
    """Return the conservative public boundary for a citation edge.

    The citation is accepted only when the citation is present in the public
    citing-grant document and that grant predates the upstream grant strictly.
    Same-day ties are excluded because intraday ordering is not proven.
    """
    if not isinstance(citing_patent_grant_date, date):
        raise TypeError("citing_patent_grant_date must be datetime.date")
    if not isinstance(upstream_patent_grant_date, date):
        raise TypeError("upstream_patent_grant_date must be datetime.date")

    if not citation_present_in_citing_grant_document:
        return None
    if citing_patent_grant_date >= upstream_patent_grant_date:
        return None
    return citing_patent_grant_date


def test_prior_citing_grant_is_eligible() -> None:
    assert conservative_public_date(
        citing_patent_grant_date=date(2024, 1, 2),
        upstream_patent_grant_date=date(2024, 3, 5),
        citation_present_in_citing_grant_document=True,
    ) == date(2024, 1, 2)


def test_same_day_grants_are_excluded() -> None:
    assert conservative_public_date(
        citing_patent_grant_date=date(2024, 3, 5),
        upstream_patent_grant_date=date(2024, 3, 5),
        citation_present_in_citing_grant_document=True,
    ) is None


def test_later_citing_grant_is_excluded() -> None:
    assert conservative_public_date(
        citing_patent_grant_date=date(2024, 4, 1),
        upstream_patent_grant_date=date(2024, 3, 5),
        citation_present_in_citing_grant_document=True,
    ) is None


def test_missing_document_evidence_is_excluded() -> None:
    assert conservative_public_date(
        citing_patent_grant_date=date(2024, 1, 2),
        upstream_patent_grant_date=date(2024, 3, 5),
        citation_present_in_citing_grant_document=False,
    ) is None


def test_invalid_dates_fail_closed() -> None:
    try:
        conservative_public_date(
            citing_patent_grant_date="2024-01-02",  # type: ignore[arg-type]
            upstream_patent_grant_date=date(2024, 3, 5),
            citation_present_in_citing_grant_document=True,
        )
    except TypeError:
        pass
    else:
        raise AssertionError("invalid citing date must fail closed")
