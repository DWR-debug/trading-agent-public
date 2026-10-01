"""Q120 deterministic CFTC TFF positioning-divergence state.

Design/feasibility only. Uses one fixed S&P 500 futures market and the public
CFTC TFF trader categories. The state is based only on positions and open
interest known at the CFTC report's public release boundary.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

CONTRACT_NAME = "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"
CFTC_CODE = "13874A"


def _decimal(value: Any, field: str) -> Decimal:
    try:
        x = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Q120_INVALID_{field}") from exc
    if not x.is_finite():
        raise ValueError(f"Q120_INVALID_{field}")
    return x


def compile_state(row: dict[str, Any]) -> dict[str, Any]:
    required = (
        "market_and_exchange_names",
        "report_date",
        "open_interest_all",
        "asset_mgr_positions_long_all",
        "asset_mgr_positions_short_all",
        "lev_money_positions_long_all",
        "lev_money_positions_short_all",
        "release_date",
    )
    missing = [field for field in required if row.get(field) in (None, "")]
    if missing:
        raise ValueError("Q120_MISSING_FIELDS:" + ",".join(missing))

    if str(row["market_and_exchange_names"]) != CONTRACT_NAME:
        raise ValueError("Q120_UNEXPECTED_CONTRACT")
    if str(row.get("cftc_contract_market_code", "")) != CFTC_CODE:
        raise ValueError("Q120_UNEXPECTED_CONTRACT_CODE")

    report_date = str(row["report_date"])
    release_date = str(row["release_date"])
    if release_date < report_date:
        raise ValueError("Q120_PIT_RELEASE_BEFORE_REPORT")

    oi = _decimal(row["open_interest_all"], "open_interest")
    if oi <= 0:
        raise ValueError("Q120_NONPOSITIVE_OPEN_INTEREST")

    am_long = _decimal(row["asset_mgr_positions_long_all"], "asset_mgr_long")
    am_short = _decimal(row["asset_mgr_positions_short_all"], "asset_mgr_short")
    lm_long = _decimal(row["lev_money_positions_long_all"], "lev_money_long")
    lm_short = _decimal(row["lev_money_positions_short_all"], "lev_money_short")

    am_net = (am_long - am_short) / oi
    lm_net = (lm_long - lm_short) / oi
    gap = lm_net - am_net

    state = (
        "LEVERAGED_MORE_LONG"
        if gap > 0
        else "ASSET_MANAGER_MORE_LONG"
        if gap < 0
        else "ALIGNED"
    )

    return {
        "contract": CONTRACT_NAME,
        "cftc_contract_market_code": CFTC_CODE,
        "report_date": report_date,
        "release_date": release_date,
        "open_interest": str(oi),
        "asset_manager_net_oi": str(am_net),
        "leveraged_money_net_oi": str(lm_net),
        "positioning_gap": str(gap),
        "positioning_state": state,
        "pit_information_boundary": "public_release_date",
    }


def synthetic_contract() -> dict[str, bool]:
    base = {
        "market_and_exchange_names": CONTRACT_NAME,
        "cftc_contract_market_code": CFTC_CODE,
        "report_date": "2026-01-13",
        "release_date": "2026-01-16",
        "open_interest_all": 1000,
        "asset_mgr_positions_long_all": 600,
        "asset_mgr_positions_short_all": 300,
        "lev_money_positions_long_all": 700,
        "lev_money_positions_short_all": 200,
    }
    a = compile_state(base)

    reverse = dict(base)
    reverse["asset_mgr_positions_long_all"] = 700
    reverse["asset_mgr_positions_short_all"] = 200
    reverse["lev_money_positions_long_all"] = 400
    reverse["lev_money_positions_short_all"] = 500
    b = compile_state(reverse)

    aligned = dict(base)
    aligned["lev_money_positions_long_all"] = 600
    aligned["lev_money_positions_short_all"] = 300
    c = compile_state(aligned)

    return {
        "positive_gap": a["positioning_state"] == "LEVERAGED_MORE_LONG",
        "negative_gap": b["positioning_state"] == "ASSET_MANAGER_MORE_LONG",
        "zero_gap": c["positioning_state"] == "ALIGNED",
        "release_boundary_recorded": a["pit_information_boundary"] == "public_release_date",
    }
