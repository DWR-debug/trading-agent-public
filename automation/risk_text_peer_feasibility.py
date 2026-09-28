"""Performance-free PIT feasibility primitives for C30 risk-text peer propagation.

The module stops at deterministic document visibility, TF-IDF representation,
cosine peer weights and a lagged peer-return state. It does not form portfolios,
rank candidates or evaluate returns.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from collections.abc import Mapping, Sequence

TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class RiskFiling:
    symbol: str
    accepted_at: datetime
    accession_id: str
    risk_text: str


def _validate_filing(filing: RiskFiling) -> None:
    if not filing.symbol:
        raise ValueError("filing.symbol must be non-empty")
    if not filing.accession_id:
        raise ValueError("filing.accession_id must be non-empty")
    if filing.accepted_at.tzinfo is None:
        raise ValueError("filing.accepted_at must be timezone-aware")
    if not isinstance(filing.risk_text, str):
        raise ValueError("filing.risk_text must be text")


def latest_visible_filings(
    filings: Sequence[RiskFiling],
    as_of: datetime,
) -> dict[str, RiskFiling]:
    """Select exactly one latest filing per symbol visible at as_of.

    Same-timestamp duplicate filings fail closed rather than silently applying
    a tie-break that could mask an amendment or duplicate-ingest defect.
    """
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    visible: dict[str, RiskFiling] = {}
    for filing in filings:
        _validate_filing(filing)
        if filing.accepted_at > as_of:
            continue
        existing = visible.get(filing.symbol)
        if existing is not None and filing.accepted_at == existing.accepted_at:
            raise ValueError(
                f"duplicate accepted_at for symbol {filing.symbol}: "
                f"{existing.accession_id} and {filing.accession_id}"
            )
        if existing is None or filing.accepted_at > existing.accepted_at:
            visible[filing.symbol] = filing
    return dict(sorted(visible.items()))


def tokenize(text: str) -> tuple[str, ...]:
    """Deterministic text normalization for the feasibility contract."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    return tuple(TOKEN_RE.findall(text.lower()))


def tfidf_vectors(documents: Mapping[str, str]) -> dict[str, dict[str, float]]:
    """Build L2-normalized TF-IDF vectors from the visible document set.

    IDF is fitted only on the supplied as-of corpus. No external vocabulary,
    stop-word list or learned model is used.
    """
    if not documents:
        raise ValueError("documents must not be empty")
    token_lists = {symbol: tokenize(text) for symbol, text in documents.items()}
    vocab = sorted({token for tokens in token_lists.values() for token in tokens})
    if not vocab:
        raise ValueError("visible documents contain no tokens")

    document_frequency = Counter()
    for tokens in token_lists.values():
        document_frequency.update(set(tokens))
    n_docs = len(token_lists)
    idf = {
        token: math.log((1.0 + n_docs) / (1.0 + document_frequency[token])) + 1.0
        for token in vocab
    }

    vectors: dict[str, dict[str, float]] = {}
    for symbol, tokens in token_lists.items():
        counts = Counter(tokens)
        total = len(tokens)
        raw = {
            token: (counts[token] / total) * idf[token]
            for token in vocab
            if counts[token]
        }
        norm = math.sqrt(sum(value * value for value in raw.values()))
        if norm == 0.0:
            raise ValueError(f"zero-norm TF-IDF vector for {symbol}")
        vectors[symbol] = {token: value / norm for token, value in raw.items()}
    return vectors


def cosine_similarity(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    """Cosine similarity for sparse L2-normalized vectors."""
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def risk_peer_similarity(
    filings: Sequence[RiskFiling],
    as_of: datetime,
) -> dict[str, dict[str, float]]:
    """Return the complete visible-filing similarity matrix without thresholds."""
    visible = latest_visible_filings(filings, as_of)
    vectors = tfidf_vectors({symbol: filing.risk_text for symbol, filing in visible.items()})
    symbols = tuple(vectors)
    return {
        symbol: {
            peer: (0.0 if peer == symbol else cosine_similarity(vectors[symbol], vectors[peer]))
            for peer in symbols
        }
        for symbol in symbols
    }


def lagged_peer_return_signal(
    filings: Sequence[RiskFiling],
    prior_returns: Mapping[str, float],
    as_of: datetime,
) -> dict[str, float]:
    """Similarity-weighted prior peer return using only visible filings.

    All non-self peers are eligible; similarity supplies the deterministic weight.
    No peer-count or similarity threshold is introduced.
    """
    similarities = risk_peer_similarity(filings, as_of)
    visible_symbols = tuple(similarities)
    missing_returns = [symbol for symbol in visible_symbols if symbol not in prior_returns]
    if missing_returns:
        raise ValueError(f"missing prior returns for visible symbols: {missing_returns}")

    result: dict[str, float] = {}
    for symbol in visible_symbols:
        weights = {
            peer: max(0.0, similarities[symbol][peer])
            for peer in visible_symbols
            if peer != symbol
        }
        denominator = sum(weights.values())
        if denominator <= 0.0:
            result[symbol] = 0.0
            continue
        result[symbol] = sum(
            weights[peer] * float(prior_returns[peer])
            for peer in weights
        ) / denominator
    return result
