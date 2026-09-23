"""Deterministic candidate-selection profiles for controlled research experiments.

Profiles only change the ordering of already evaluated candidates. They do not
change the parameter space, backtest engine, validation gates, or risk limits.

The default profile `score_max` preserves the existing optimizer behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SelectionProfile:
    name: str
    description: str
    criterion: str

    def rank_key(self, result: Any, parameter_space: Any) -> tuple:
        """Return a higher-is-better deterministic ranking key."""
        if self.name == "score_max":
            return (result.score,)

        if self.name == "trade_rich":
            return (result.trade_count, result.score)

        if self.name == "risk_averse":
            return (
                -result.candidate.leverage,
                -result.candidate.risk_per_trade,
                result.score,
            )

        if self.name == "boundary_averse":
            return (
                _parameter_centrality(
                    result.candidate,
                    parameter_space,
                ),
                result.score,
            )

        raise ValueError(f"Unbekanntes Selection-Profil: {self.name}")


_PROFILES: tuple[SelectionProfile, ...] = (
    SelectionProfile(
        name="score_max",
        description="Kontrollprofil: maximiert den bestehenden Optimizer-Score.",
        criterion="score DESC",
    ),
    SelectionProfile(
        name="boundary_averse",
        description=(
            "Bevorzugt Kandidaten mit maximaler mittlerer Distanz zu "
            "den Parameterraum-Grenzen; Score nur als Tie-Breaker."
        ),
        criterion="parameter_centrality DESC, score DESC",
    ),
    SelectionProfile(
        name="risk_averse",
        description=(
            "Bevorzugt niedrigeren Hebel und geringeres Risiko pro Trade; "
            "Score dient als Tie-Breaker."
        ),
        criterion="leverage ASC, risk_per_trade ASC, score DESC",
    ),
    SelectionProfile(
        name="trade_rich",
        description=(
            "Bevorzugt Kandidaten mit mehr In-Sample-Trades; Score dient "
            "als Tie-Breaker."
        ),
        criterion="trade_count DESC, score DESC",
    ),
)


def _value_index(values: list | tuple, value: Any) -> int:
    """Find the deterministic index of a candidate value in the profile space."""
    ordered = tuple(sorted(values))
    try:
        return ordered.index(value)
    except ValueError as exc:
        raise ValueError(
            f"Kandidatenwert {value!r} fehlt im Parameterraum."
        ) from exc


def _centrality(values: list | tuple, value: Any) -> float:
    ordered = tuple(sorted(values))
    if len(ordered) <= 1:
        return 1.0

    index = _value_index(ordered, value)
    max_index = len(ordered) - 1
    distance_from_edge = min(index, max_index - index)
    return (2.0 * distance_from_edge) / max_index


def _parameter_centrality(candidate: Any, parameter_space: Any) -> float:
    values = (
        _centrality(
            parameter_space.momentum_lookbacks,
            candidate.strategy.momentum.lookback,
        ),
        _centrality(
            parameter_space.mean_reversion_windows,
            candidate.strategy.mean_reversion.window,
        ),
        _centrality(
            parameter_space.mean_reversion_thresholds,
            candidate.strategy.mean_reversion.threshold,
        ),
        _centrality(
            parameter_space.risk_per_trade_values,
            candidate.risk_per_trade,
        ),
        _centrality(
            parameter_space.leverage_values,
            candidate.leverage,
        ),
    )
    return sum(values) / len(values)


def get_selection_profile(name: str | None) -> SelectionProfile:
    selected = name or "score_max"
    for profile in _PROFILES:
        if profile.name == selected:
            return profile

    available = ", ".join(profile.name for profile in _PROFILES)
    raise ValueError(
        f"Unbekanntes Selection-Profil: {selected}. "
        f"Verfügbar: {available}"
    )


def list_selection_profiles() -> tuple[SelectionProfile, ...]:
    return _PROFILES


def available_selection_profile_names() -> tuple[str, ...]:
    return tuple(profile.name for profile in _PROFILES)


def selection_profile_identity(name: str | None) -> dict[str, str]:
    profile = get_selection_profile(name)
    return {
        "name": profile.name,
        "description": profile.description,
        "criterion": profile.criterion,
    }
