from data.binance_loader import load_binance_candles


def test_empty_symbol_is_rejected():
    try:
        load_binance_candles("", "1h", 3)
    except ValueError:
        return

    raise AssertionError(
        "Leeres Symbol wurde akzeptiert."
    )


def test_invalid_interval_is_rejected():
    try:
        load_binance_candles("BTCUSDT", "10h", 3)
    except ValueError:
        return

    raise AssertionError(
        "Ungültiges Intervall wurde akzeptiert."
    )


def test_invalid_limit_is_rejected():
    for limit in (0, 1001):
        try:
            load_binance_candles("BTCUSDT", "1h", limit)
        except ValueError:
            continue

        raise AssertionError(
            f"Ungültiges Limit {limit} wurde akzeptiert."
        )
