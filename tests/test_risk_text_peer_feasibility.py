from __future__ import annotations

from datetime import datetime, timezone

import pytest

from automation.risk_text_peer_feasibility import (
    RiskFiling,
    lagged_peer_return_signal,
    latest_visible_filings,
    risk_peer_similarity,
    tfidf_vectors,
)


def dt(day: int) -> datetime:
    return datetime(2026, 1, day, tzinfo=timezone.utc)


def filing(symbol: str, day: int, accession: str, text: str) -> RiskFiling:
    return RiskFiling(symbol, dt(day), accession, text)


def test_latest_visible_filings_is_pit_bounded() -> None:
    filings = (
        filing("AAA", 2, "A1", "supply chain insurance"),
        filing("AAA", 10, "A2", "future shock text"),
        filing("BBB", 3, "B1", "supply chain"),
    )
    visible = latest_visible_filings(filings, dt(5))
    assert set(visible) == {"AAA", "BBB"}
    assert visible["AAA"].accession_id == "A1"


def test_same_timestamp_duplicate_fails_closed() -> None:
    filings = (
        filing("AAA", 2, "A1", "one"),
        filing("AAA", 2, "A2", "two"),
    )
    with pytest.raises(ValueError, match="duplicate accepted_at"):
        latest_visible_filings(filings, dt(5))


def test_future_filing_mutation_cannot_change_similarity() -> None:
    filings = (
        filing("AAA", 2, "A1", "commodity supply insurance"),
        filing("BBB", 3, "B1", "commodity supply"),
        filing("AAA", 10, "A2", "completely unrelated future language"),
    )
    before = risk_peer_similarity(filings, dt(5))
    mutated = list(filings)
    mutated[-1] = filing("AAA", 10, "A2", "commodity commodity commodity")
    after = risk_peer_similarity(mutated, dt(5))
    assert after == before


def test_future_text_is_excluded_from_tfidf_fit() -> None:
    visible = {
        "AAA": "supply chain risk",
        "BBB": "supply chain logistics",
    }
    vectors = tfidf_vectors(visible)
    assert set(vectors) == {"AAA", "BBB"}


def test_peer_signal_uses_nonself_peers_only() -> None:
    filings = (
        filing("AAA", 2, "A1", "supply chain insurance"),
        filing("BBB", 3, "B1", "supply chain logistics"),
        filing("CCC", 4, "C1", "cyber security"),
    )
    signals = lagged_peer_return_signal(
        filings,
        {"AAA": 0.50, "BBB": 0.10, "CCC": -0.80},
        dt(5),
    )
    assert signals["AAA"] != pytest.approx(0.50)


def test_future_filing_cannot_change_peer_signal() -> None:
    base = (
        filing("AAA", 2, "A1", "supply chain insurance"),
        filing("BBB", 3, "B1", "supply chain logistics"),
    )
    extended = base + (
        filing("BBB", 10, "B2", "future financial language"),
        filing("AAA", 12, "A2", "future unrelated language"),
    )
    before = lagged_peer_return_signal(base, {"AAA": 0.20, "BBB": -0.10}, dt(5))
    after = lagged_peer_return_signal(extended, {"AAA": 0.20, "BBB": -0.10}, dt(5))
    assert after == before


def test_empty_vocabulary_fails_closed() -> None:
    with pytest.raises(ValueError, match="no tokens"):
        tfidf_vectors({"AAA": "!!!"})
