"""Deterministic, performance-free feasibility primitives for the unusual frontier.

This module intentionally stops before portfolio formation/performance evaluation.
Its only purpose is to freeze the mathematical construction and provide
future-mutation tests that can be run without paid data, APIs or model calls.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import TypeAlias

NumericSequence: TypeAlias = Sequence[float]

ILLUSION_LOOKBACK_SESSIONS = 21
INDUSTRY_RELATIVE_REVERSAL_LOOKBACK_SESSIONS = 21


def parse_sec_assigned_sic(header_text: str) -> str:
    """Parse the issuer SIC from an EDGAR filing header without inference."""
    if not isinstance(header_text, str) or not header_text.strip():
        raise ValueError("SEC header text must be non-empty")
    patterns = (
        r"<ASSIGNED-SIC>\s*(\d{4})\b",
        r"STANDARD INDUSTRIAL CLASSIFICATION:\s*[^\r\n\[]+\[(\d{4})\]",
    )
    for pattern in patterns:
        match = re.search(pattern, header_text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    raise ValueError("SEC assigned SIC not found")


def pit_sec_industry_mapping(
    filing_headers: Sequence[Mapping[str, object]],
    decision_time: str,
) -> dict[str, str]:
    """Return latest visible symbol->SIC mapping using EDGAR acceptance time."""
    visible = []
    for row in filing_headers:
        symbol = row.get("symbol")
        acceptance_time = row.get("acceptance_time")
        accession = row.get("accession")
        sic = row.get("sic")
        if not all(isinstance(v, str) and v.strip() for v in (symbol, acceptance_time, accession, sic)):
            raise ValueError("filing header rows require symbol, acceptance_time, accession, sic")
        if acceptance_time <= decision_time:
            visible.append((symbol.strip(), acceptance_time.strip(), accession.strip(), sic.strip()))

    mapping: dict[str, tuple[str, str, str]] = {}
    for symbol, acceptance_time, accession, sic in visible:
        prior = mapping.get(symbol)
        if prior is not None and acceptance_time == prior[0] and sic != prior[2]:
            raise ValueError("CONFLICTING_SAME_ACCEPTANCE_SIC")
        candidate = (acceptance_time, accession, sic)
        if prior is None or candidate > prior:
            mapping[symbol] = candidate
    return {symbol: row[2] for symbol, row in mapping.items()}


def _finite(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _validate_simple_returns(returns: NumericSequence) -> None:
    for i, value in enumerate(returns):
        value = _finite(value, f"returns[{i}]")
        if value <= -1.0:
            raise ValueError(f"returns[{i}] must be greater than -1")


def compounded_return(returns: NumericSequence) -> float:
    """Cumulative compounded return from simple period returns."""
    _validate_simple_returns(returns)
    return math.prod(1.0 + float(value) for value in returns) - 1.0


def illusion_momentum_gap(returns: NumericSequence) -> float:
    """Fixed C29 signal: compounded cumulative return minus summed simple returns."""
    _validate_simple_returns(returns)
    return compounded_return(returns) - sum(float(value) for value in returns)


def simple_returns_from_closes(closes: Sequence[float]) -> tuple[float, ...]:
    """Convert a close-price path into simple returns without future observations."""
    if len(closes) < 2:
        raise ValueError("at least two closes are required")
    values = tuple(_finite(value, f"closes[{i}]") for i, value in enumerate(closes))
    if any(value <= 0.0 for value in values):
        raise ValueError("close prices must be positive")
    return tuple(values[i] / values[i - 1] - 1.0 for i in range(1, len(values)))


def illusion_momentum_gap_at(
    closes: Sequence[float],
    decision_index: int,
    *,
    lookback_sessions: int = ILLUSION_LOOKBACK_SESSIONS,
) -> float:
    """C29 at decision time; data ends at decision_index, never at index + 1."""
    if lookback_sessions < 2:
        raise ValueError("lookback_sessions must be at least 2")
    start = decision_index - lookback_sessions
    if start < 0 or decision_index >= len(closes):
        raise IndexError("insufficient close history for decision_index")
    return illusion_momentum_gap(
        simple_returns_from_closes(closes[start : decision_index + 1])
    )


def industry_relative_reversal_residual(
    one_month_returns: Mapping[str, float],
    industry_by_symbol: Mapping[str, str],
) -> dict[str, float]:
    """M4 residual return after subtracting the equal-weight industry return.

    The returned value is a raw residual. The eventual reversal implementation
    can transform this deterministically to exposure without changing the
    residual construction.
    """
    symbols = tuple(one_month_returns)
    if not symbols:
        raise ValueError("one_month_returns must not be empty")
    missing = [s for s in symbols if s not in industry_by_symbol]
    if missing:
        raise ValueError(f"missing industry mapping for: {missing}")
    buckets: dict[str, list[float]] = {}
    for symbol in symbols:
        industry = industry_by_symbol[symbol]
        buckets.setdefault(industry, []).append(
            _finite(one_month_returns[symbol], f"return[{symbol}]")
        )
    means = {
        industry: sum(values) / len(values)
        for industry, values in buckets.items()
    }
    return {
        symbol: float(one_month_returns[symbol]) - means[industry_by_symbol[symbol]]
        for symbol in symbols
    }


def industry_relative_reversal_residual_at(
    closes_by_symbol: Mapping[str, Sequence[float]],
    industry_by_symbol: Mapping[str, str],
    decision_index: int,
    *,
    lookback_sessions: int = INDUSTRY_RELATIVE_REVERSAL_LOOKBACK_SESSIONS,
) -> dict[str, float]:
    """M4 at decision time using only completed prices through decision_index."""
    if lookback_sessions < 1:
        raise ValueError("lookback_sessions must be positive")
    if not closes_by_symbol:
        raise ValueError("closes_by_symbol must not be empty")
    start = decision_index - lookback_sessions
    if start < 0:
        raise IndexError("insufficient close history for decision_index")
    returns: dict[str, float] = {}
    for symbol, closes in closes_by_symbol.items():
        if decision_index >= len(closes):
            raise IndexError(f"decision_index out of range for {symbol}")
        first = _finite(closes[start], f"{symbol}.closes[{start}]")
        last = _finite(closes[decision_index], f"{symbol}.closes[{decision_index}]")
        if first <= 0.0 or last <= 0.0:
            raise ValueError(f"close prices must be positive for {symbol}")
        returns[symbol] = last / first - 1.0
    return industry_relative_reversal_residual(returns, industry_by_symbol)


def frontier_specs() -> tuple[dict[str, object], ...]:
    """Frozen mechanism metadata; no ranking or selection is implied."""
    return (
        {
            "code": "C29",
            "name": "ILLUSION_MOMENTUM_GAP",
            "lookback_sessions": ILLUSION_LOOKBACK_SESSIONS,
            "data_channel": "daily_close_only",
            "performance_ready": False,
        },
        {
            "code": "M4",
            "name": "INDUSTRY_RELATIVE_REVERSAL_RESIDUAL",
            "lookback_sessions": INDUSTRY_RELATIVE_REVERSAL_LOOKBACK_SESSIONS,
            "data_channel": "daily_close_plus_pit_industry_mapping",
            "performance_ready": False,
        },
    )
