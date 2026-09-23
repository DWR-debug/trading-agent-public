from automation.asset_regime_interaction_analysis import (
    analyze_asset_interaction,
    markdown,
)


def test_asset_interaction_preserves_ex_ante_scope_and_asset_counts():
    from tests.test_regime_trend_choppiness_analysis import (
        archive_manifest,
        rolling,
        write_csv,
    )

    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        csv_path = root / "data" / "TEST" / "1d.csv"
        rows = write_csv(csv_path)
        result = analyze_asset_interaction(
            rolling(rows),
            archive_manifest(rows, csv_path),
            root / "data",
        )

    assert result["evaluation_count"] == 5
    assert result["transition_count"] == 3
    assert result["asset_summary"]["TEST"]["by_geometry"]["small"]["unique_market_windows"] == 3
    assert result["interpretation_scope"]["no_new_data_download"] is True
    assert result["safety"]["paper_only"] is True
    assert "Asset-Gesamtbild" in markdown(result)


def test_asset_interaction_fingerprint_is_deterministic():
    from tests.test_regime_trend_choppiness_analysis import (
        archive_manifest,
        rolling,
        write_csv,
    )

    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        csv_path = root / "data" / "TEST" / "1d.csv"
        rows = write_csv(csv_path)
        archive = archive_manifest(rows, csv_path)
        r1 = analyze_asset_interaction(
            rolling(rows), archive, root / "data"
        )
        r2 = analyze_asset_interaction(
            rolling(rows), archive, root / "data"
        )

    assert r1["analysis_fingerprint"] == r2["analysis_fingerprint"]
