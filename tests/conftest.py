from datetime import date
from unittest.mock import MagicMock

import pyarrow as pa
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


@pytest.fixture
def base_test_dir(tmp_path):
    """Provides a temporary directory for file operations."""
    return tmp_path


@pytest.fixture
def sample_schema():
    """Shared schema for trades."""
    return pa.schema(
        [
            ("instId", pa.string()),
            ("ts", pa.int64()),
            ("px", pa.float64()),
            ("sz", pa.float64()),
            ("tradeId", pa.string()),
        ]
    )


@pytest.fixture
def sample_trade_table(sample_schema):
    """Provides a PyArrow Table with sample data."""
    data = {
        "instId": ["BTC-USDT", "BTC-USDT"],
        "ts": [1704067200000, 1704067260000],
        "px": [42000.0, 42100.0],
        "sz": [0.1, 0.2],
        "tradeId": ["1001", "1002"],
    }
    return pa.Table.from_pydict(data, schema=sample_schema)


@pytest.fixture
def trade_date():
    return date(2026, 1, 1)
