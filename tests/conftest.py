from unittest.mock import MagicMock

import pytest

from okx_historic_backup.okx_trade_fetcher import OKXTradeFetcher


@pytest.fixture
def mock_market_api():
    """Provides a mocked OKX MarketAPI instance."""
    mock_market_api = MagicMock()
    mock_market_api.get_history_trades = MagicMock()
    yield mock_market_api


@pytest.fixture
def mock_okx_trade_fetcher(mock_market_api):
    yield OKXTradeFetcher(market_api=mock_market_api)
