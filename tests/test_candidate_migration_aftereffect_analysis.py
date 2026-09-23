import json


def _fixture():
    from tests.test_regime_trend_choppiness_analysis import (
        archive_manifest,
        rolling,
        write_csv,
    )
    from pathlib import Path
    import tempfile

    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    path = root / "data" / "TEST" / "1d.csv"
    rows = write_csv(path)

    rolling_data = rolling(rows)
    rolling_data["target_count"] = 5000
    rolling_data["research_candle_count"] = 4500

    archive = archive_manifest(rows, path)
    archive["safety"] = {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }
    return tmp, root, rows, rolling_data, archive


def test_migration_and_stable_destinations_are_separated():
    from automation.candidate_migration_aftereffect_analysis import analyze

    tmp, root, rows, rolling, archive = _fixture()
    try:
        result = analyze(rolling, archive)
    finally:
        tmp.cleanup()

    assert result["transition_count"] == 3
    assert result["migration_summary"]["after_migration"]["transition_count"] == 1
    assert result["migration_summary"]["after_stable_candidate"]["transition_count"] == 2
    assert (
        result["interpretation_scope"]["first_oos_after_migration_is_destination_window"]
        is True
    )


def test_analysis_is_deterministic():
    from automation.candidate_migration_aftereffect_analysis import analyze

    tmp, root, rows, rolling, archive = _fixture()
    try:
        first = analyze(rolling, archive)
        second = analyze(rolling, archive)
    finally:
        tmp.cleanup()

    assert first["analysis_fingerprint"] == second["analysis_fingerprint"]


def test_bad_safety_fails_closed():
    from automation.candidate_migration_aftereffect_analysis import analyze

    tmp, root, rows, rolling, archive = _fixture()
    try:
        rolling["safety"]["live_trading_enabled"] = True
        try:
            analyze(rolling, archive)
        except ValueError as exc:
            assert "Live trading" in str(exc)
        else:
            raise AssertionError("Expected safety failure")
    finally:
        tmp.cleanup()


def test_markdown_mentions_first_oos_semantics():
    from automation.candidate_migration_aftereffect_analysis import markdown, analyze

    tmp, root, rows, rolling, archive = _fixture()
    try:
        result = analyze(rolling, archive)
        report = markdown(result)
    finally:
        tmp.cleanup()

    assert "unmittelbar folgende OOS-Fenster" in report
