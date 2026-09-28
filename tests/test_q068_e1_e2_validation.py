import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from automation.q067_alpha_mechanisms import (
    Q067_SLEEVES,
    apply_turnover_hysteresis,
    build_alpha_sleeves,
    equal_weight_ensemble,
)
from automation.q068_fresh_coverage import FROZEN_SYMBOLS
from automation import q068_fresh_coverage, q068_pit


def _bar(ts, value):
    return type(
        "Bar",
        (),
        {
            "timestamp": ts,
            "open": value,
            "high": value + 1.0,
            "low": value - 1.0,
            "close": value,
            "volume": 1000.0,
        },
    )()


def _assets(count=3500):
    base = datetime(2011, 1, 3, tzinfo=timezone.utc)
    return {
        symbol: tuple(
            _bar(base + timedelta(days=i), 100.0 + i + slot)
            for i in range(count)
        )
        for slot, symbol in enumerate(FROZEN_SYMBOLS)
    }




def test_q068_coverage_snapshot_path_uses_execution_trial_identity():
    prereg = json.loads(
        Path("research/preregistrations/q068_fixed_mechanism_freeze_2026_09_28.json")
        .read_text(encoding="utf-8")
    )
    scoped = q068_fresh_coverage._coverage_snapshot_spec(prereg)
    assert prereg["trial_id"] == "Q-2026-09-28-068-DESIGN-FREEZE"
    assert scoped["trial_id"] == "T-2026-09-28-068-COVERAGE"

def test_q068_symbols_are_frozen_and_distinct():
    assert FROZEN_SYMBOLS == ("ETR", "PPL", "WEC", "FE", "D", "EXR", "PSA", "O")
    assert len(FROZEN_SYMBOLS) == len(set(FROZEN_SYMBOLS))


def test_q068_reuses_exact_six_sleeves_without_sleeve_drift():
    assets = _assets()
    sleeves = build_alpha_sleeves(assets, symbols=FROZEN_SYMBOLS)
    assert tuple(sleeves) == Q067_SLEEVES


def test_q068_ensemble_is_bounded():
    assets = _assets(3500)
    sleeves = build_alpha_sleeves(assets, symbols=FROZEN_SYMBOLS)
    ensemble = equal_weight_ensemble(sleeves, symbols=FROZEN_SYMBOLS)
    assert all(sum(row.values()) <= 1.0 + 1e-12 for row in ensemble)


def test_q068_turnover_hysteresis_keeps_entry_exit_semantics():
    symbols = FROZEN_SYMBOLS
    aggregate = (
        {symbol: (0.125 if symbol == symbols[0] else 0.0) for symbol in symbols},
        {symbol: (0.10 if symbol == symbols[0] else 0.0) for symbol in symbols},
        {symbol: 0.0 for symbol in symbols},
    )
    out = apply_turnover_hysteresis(aggregate, symbols=symbols)
    assert out[1][symbols[0]] == out[0][symbols[0]]
    assert out[2][symbols[0]] == 0.0


def test_q068_pit_constants_are_fixed():
    assert q068_pit.Q068_SYMBOLS == FROZEN_SYMBOLS
    assert q068_pit.COVERAGE_TRIAL_ID == "T-2026-09-28-068-COVERAGE"
    assert q068_pit.PIT_TRIAL_ID == "T-2026-09-28-068-PIT"
    assert q068_pit.STEP == 113
    assert q068_pit.MIN_HISTORY == 273


def test_q068_coverage_and_pit_workflow_is_self_hosted_and_fail_closed():
    text = Path(".github/workflows/q068-coverage-pit.yml").read_text(encoding="utf-8")
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "Q068 COVERAGE PASSED" in text
    assert "Q068 PIT PASSED" in text
    assert "performance_trial_authorized" in text
    assert "selection_used" in text
    assert "research/evidence/q068_coverage_result.json" in text
    assert "research/evidence/q068_pit_result.json" in text
    assert "ref: ${{ github.sha }}" in text
    assert "echo Q068_EXACT_SOURCE_SHA=%GITHUB_SHA%" in text


def test_q068_preregistration_freezes_exact_discovery_batch_and_governance():
    prereg = json.loads(
        Path("research/preregistrations/q068_fixed_mechanism_freeze_2026_09_28.json")
        .read_text(encoding="utf-8")
    )
    assert prereg["symbols"] == list(FROZEN_SYMBOLS)
    assert prereg["source_discovery"]["workflow_run_id"] == 36389197475
    assert prereg["source_discovery"]["discovery_fingerprint"] == (
        "b85c7c35b593ce7b8ba4e4bb27de6fe1588338684d51330cd749da076cc5441e"
    )
    assert prereg["governance"]["performance_trial_authorized"] is False
    assert prereg["governance"]["holdout_used_for_selection"] is False
    assert prereg["governance"]["family_ranking"] is False
    assert "family_search" not in prereg["governance"]
    assert prereg["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_q068_performance_preregistration_is_pre_registered_but_not_authorized():
    prereg = json.loads(
        Path("research/preregistrations/q068_performance_2026_09_28.json")
        .read_text(encoding="utf-8")
    )
    assert prereg["status"] == "PREREGISTERED_PERFORMANCE"
    assert prereg["governance"]["performance_trial_authorized"] is False
    assert prereg["safety"]["live_trading_enabled"] is False


def test_q068_universe_is_registered_at_unique_new_priority():
    from research.asset_universes import get_universe

    universe = get_universe("validation_2026_09_28_q068_fresh_e1_e2")
    assert universe.priority == 73
    assert universe.symbols == FROZEN_SYMBOLS
    assert universe.target_count == 3500

def test_q068_self_hosted_evidence_persistence_uses_checkout_path_without_local_git():
    for path in (
        ".github/workflows/q068-coverage-pit.yml",
        ".github/workflows/q068-autonomous-advance.yml",
        ".github/workflows/q068-fixed-mechanism-performance.yml",
        ".github/workflows/q068-evidence-reconcile.yml",
    ):
        text = Path(path).read_text(encoding="utf-8")
        assert "automation\\github_contents_publish.py" in text
        assert "automation.github_contents_publish" not in text.replace(
            "automation\\github_contents_publish.py",
            "",
        )
        assert "git add " not in text
        assert "git push " not in text
        assert "for /f %%H in" not in text


def test_q068_workflow_chain_uses_explicit_workflow_dispatch():
    for path in (
        ".github/workflows/q068-autonomous-advance.yml",
        ".github/workflows/q068-fixed-mechanism-performance.yml",
        ".github/workflows/q068-evidence-reconcile.yml",
    ):
        text = Path(path).read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text
        assert "actions: write" in text
        assert "DISPATCH_" in text
        assert "https://api.github.com/repos/%GITHUB_REPOSITORY%/actions/workflows/" in text
        assert "github.token" in text


def test_q068_frozen_source_contract_is_explicitly_locked():
    expected = {
        "automation/q067_alpha_mechanisms.py": "344343f9910f1ea5eaa9a2d2c295a6f87a520bdc",
        "automation/q068_performance.py": "d85e17885ff56353ca677a3aa47d8a5e7b6ec056",
        "data/canonical_snapshot.py": "18c7c051b1b4d3f7f67bc395baf5ef3787e1b028",
        "execution/cost_contract.py": "21b54b45dbe708f3102851fd368ad1b64226b0ad",
        "config/settings.py": "9c7b5199ed09d11ca17eb72493aebf7a7666fd28",
    }
    for path in (
        ".github/workflows/q068-autonomous-advance.yml",
        ".github/workflows/q068-fixed-mechanism-performance.yml",
    ):
        text = Path(path).read_text(encoding="utf-8")
        for value in expected.values():
            assert value in text
        assert "Q068 SOURCE CONTRACT OK" in text or "Q068 AUTH SOURCE CONTRACT OK" in text


def test_q068_pipeline_state_requires_persistent_frozen_snapshot():
    text=Path("automation/q068_pipeline_state.py").read_text(encoding="utf-8")
    assert "Q068 frozen snapshot not persistently available with authoritative fingerprint" in text
    assert "snapshot_manifest" in text


def test_q068_authorization_contract_is_fail_closed_when_revoked():
    p=json.loads(Path("research/authorizations/q068_performance_2026_09_28.json").read_text(encoding="utf-8"))
    assert p["authorized"] is False
    assert p["performance_execution_authorized"] is False
    assert p["revoked"] is True
    assert p["scientific_status"] == "NO_SCIENTIFIC_OUTCOME"


def test_q068_performance_requires_explicit_dispatch_only():
    text=Path(".github/workflows/q068-fixed-mechanism-performance.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "research/authorizations/q068_performance_2026_09_28.json" not in text.split("permissions:", 1)[0]
