"""Q186 conservative citation-visibility contract.

Pre-formal only. A citation edge is admitted to an upstream patent's
pre-grant graph only when the citation is directly evidenced in the public
grant document of the citing patent and the citing patent grant predates the
upstream grant strictly. Same-day and later dates fail closed.
"""
from __future__ import annotations

from datetime import date


def conservative_public_date(
    *,
    citing_patent_grant_date: date,
    upstream_patent_grant_date: date,
    citation_present_in_citing_grant_document: bool,
) -> date | None:
    """Return the conservative public boundary for a citation edge."""
    if not isinstance(citing_patent_grant_date, date):
        raise TypeError("citing_patent_grant_date must be datetime.date")
    if not isinstance(upstream_patent_grant_date, date):
        raise TypeError("upstream_patent_grant_date must be datetime.date")
    if not citation_present_in_citing_grant_document:
        return None
    if citing_patent_grant_date >= upstream_patent_grant_date:
        return None
    return citing_patent_grant_date
