from data.csv_loader import load_candles
from data.quality import validate_candles


def test_csv_data_passes_quality_validation():
    candles = load_candles("tests/sample_candles.csv")

    validate_candles(candles)

    assert len(candles) == 3
