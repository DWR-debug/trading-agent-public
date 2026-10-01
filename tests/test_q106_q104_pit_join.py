from __future__ import annotations

from automation.q106_q104_pit_join import (
    build_acceptance_index,
    future_mutation_invariant,
    lineage_rows,
    treasury_future_invariant,
)


def test_q106_sec_acceptance_lineage_is_pit_stable():
    submissions = {
        "filings": {
            "recent": {
                "form": ["10-Q", "10-Q"],
                "accessionNumber": ["a1", "a2"],
                "acceptanceDateTime": [
                    "2025-04-01T14:00:00Z",
                    "2025-07-01T14:00:00Z",
                ],
            }
        }
    }
    facts = {
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {
                        "shares": [
                            {"val": 100, "accn": "a1", "filed": "2025-04-01"},
                            {"val": 110, "accn": "a2", "filed": "2025-07-01"},
                        ]
                    }
                }
            }
        }
    }
    rows = lineage_rows(facts, build_acceptance_index(submissions))
    assert len(rows) == 2
    assert future_mutation_invariant(
        rows,
        [dict(rows[0], accn="future", accepted_at="2025-10-01T14:00:00+00:00")],
        "2025-08-01T00:00:00Z",
    )


def test_q106_treasury_future_rows_cannot_change_prior_state():
    base = [{"record_date": "2025-06-10", "auction_date": "2025-06-04"}]
    future = [{"record_date": "2025-07-10", "auction_date": "2025-07-03"}]
    assert treasury_future_invariant(base, future, "2025-06-30")
