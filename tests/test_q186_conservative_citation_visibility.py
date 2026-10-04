"""Tests for the Q186 conservative citation-visibility contract."""
from __future__ import annotations

from datetime import date

import pytest

from automation.q186_citation_visibility import conservative_public_date


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


@pytest.mark.parametrize(
    ("citing", "upstream"),
    [
        ("2024-01-02", date(2024, 3, 5)),
        (date(2024, 1, 2), "2024-03-05"),
    ],
)
def test_invalid_dates_fail_closed(citing: object, upstream: object) -> None:
    with pytest.raises(TypeError):
        conservative_public_date(
            citing_patent_grant_date=citing,  # type: ignore[arg-type]
            upstream_patent_grant_date=upstream,  # type: ignore[arg-type]
            citation_present_in_citing_grant_document=True,
        )
