from unittest.mock import patch

import httpx
import pytest

from okx_historic_backup.utilities.custom_types import QueryParamTypeEnum


def test_fetch_single_page_success_after_retries(
    mock_okx_trade_fetcher, mock_market_api
):
    mock_request = httpx.Request("GET", "https://test.com")
    mock_response = httpx.Response(status_code=429, request=mock_request)
    error_429 = httpx.HTTPStatusError(
        message="Too Many Requests",
        request=mock_response.request,
        response=mock_response,
    )
    error_timeout = httpx.TimeoutException("Timeout", request=mock_request)
    error_network = httpx.NetworkError("Timeout", request=mock_request)

    success_response = {"data": [{"tradeId": "1", "sz": "1", "px": "1", "ts": "1"}]}

    mock_market_api.get_history_trades.side_effect = [
        error_429,
        error_timeout,
        error_network,
        success_response,
    ]
    with (
        patch("tenacity.nap.time.sleep", return_value=None),
    ):
        result = mock_okx_trade_fetcher._fetch_single_page(
            instrument_id="BTC-USDT", after="12345", type=QueryParamTypeEnum._Timestamp
        )

    assert result == success_response["data"]
    assert mock_market_api.get_history_trades.call_count == 4


def test_fetch_single_page_raises(mock_okx_trade_fetcher, mock_market_api) -> None:
    mock_request = httpx.Request("GET", "https://test.com")
    mock_response = httpx.Response(status_code=400, request=mock_request)
    error_400 = httpx.HTTPStatusError(
        message="400",
        request=mock_response.request,
        response=mock_response,
    )
    mock_market_api.get_history_trades.side_effect = error_400
    with (
        patch("tenacity.nap.time.sleep", return_value=None),
        pytest.raises(httpx.HTTPStatusError),
    ):
        mock_okx_trade_fetcher._fetch_single_page(
            instrument_id="BTC-USDT", after="12345", type=QueryParamTypeEnum._Timestamp
        )


def test_pagination(mock_okx_trade_fetcher, mock_market_api) -> None:
    """Test that pagination correctly updates 'after' and switches types
    + StopItteration on no data."""
    page_1 = {
        "data": [
            {
                "tradeId": "101",
                "sz": "1.5",
                "px": "50000",
                "ts": "1600000000000",
            }
        ]
    }
    page_2 = {"data": []}
    mock_market_api.get_history_trades.side_effect = [page_1, page_2]

    results = mock_okx_trade_fetcher.yield_historical_trades(
        "BTC-USDT", "1600000000000"
    )

    _ = next(results)
    mock_market_api.get_history_trades.assert_called_with(
        instId="BTC-USDT", after="1600000000000", type="2"
    )

    with pytest.raises(StopIteration):
        _ = next(results)
        mock_market_api.get_history_trades.assert_called_with(
            instId="BTC-USDT", after="101", type="1"
        )
