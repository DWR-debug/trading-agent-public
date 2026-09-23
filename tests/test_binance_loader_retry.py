from unittest.mock import patch

import urllib.error

from data import binance_loader


def test_fetch_json_retries_rate_limit_then_succeeds():
    error = urllib.error.HTTPError(
        url="https://example.test",
        code=429,
        msg="rate limited",
        hdrs={"Retry-After": "0"},
        fp=None,
    )

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"[]"

    with patch(
        "data.binance_loader.urllib.request.urlopen",
        side_effect=[error, Response()],
    ) as urlopen, patch(
        "data.binance_loader.time.sleep"
    ) as sleep:
        assert binance_loader._fetch_json(
            "https://example.test"
        ) == []
        assert urlopen.call_count == 2
        sleep.assert_called_once_with(0.0)


def test_fetch_json_retries_server_error():
    error = urllib.error.HTTPError(
        url="https://example.test",
        code=503,
        msg="temporary",
        hdrs={},
        fp=None,
    )

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"[]"

    with patch(
        "data.binance_loader.urllib.request.urlopen",
        side_effect=[error, Response()],
    ), patch(
        "data.binance_loader.time.sleep"
    ) as sleep:
        assert binance_loader._fetch_json(
            "https://example.test"
        ) == []
        sleep.assert_called_once_with(1.0)
