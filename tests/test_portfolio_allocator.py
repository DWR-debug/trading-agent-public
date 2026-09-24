import pytest

from portfolio.allocator import (
    FixedPortfolioAllocator,
    PortfolioAllocationError,
    PortfolioConstraints,
)


def test_fixed_allocator_accepts_valid_long_only_weights():
    allocator = FixedPortfolioAllocator()
    result = allocator.validate({"trend": 0.5, "momentum": 0.5})
    assert result == {"momentum": 0.5, "trend": 0.5}


def test_fixed_allocator_supports_signed_long_short_exposures_within_gross_limit():
    allocator = FixedPortfolioAllocator(
        PortfolioConstraints(gross_exposure_limit=1.0, net_exposure_limit=1.0)
    )
    result = allocator.validate({"long": 0.5, "short": -0.5})
    assert result == {"long": 0.5, "short": -0.5}


def test_fixed_allocator_fails_closed_on_gross_breach():
    with pytest.raises(PortfolioAllocationError):
        FixedPortfolioAllocator().validate({"a": 0.6, "b": 0.5})


def test_fixed_allocator_fails_closed_on_net_breach():
    with pytest.raises(PortfolioAllocationError):
        FixedPortfolioAllocator().validate({"a": 0.8, "b": 0.4})


def test_fixed_allocator_fails_closed_on_non_finite_weight():
    with pytest.raises(PortfolioAllocationError):
        FixedPortfolioAllocator().validate({"a": float("nan")})


def test_compose_sleeves_adds_signed_symbol_exposures_deterministically():
    allocator = FixedPortfolioAllocator()
    result = allocator.compose({
        "trend": {"SPY": 0.5},
        "hedge": {"SPY": -0.25, "TLT": 0.25},
    })
    assert result == {"SPY": 0.25, "TLT": 0.25}
