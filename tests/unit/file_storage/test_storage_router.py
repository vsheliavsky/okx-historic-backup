from datetime import date
from unittest.mock import MagicMock

import pytest

from okx_historic_backup.file_storage.storage_router import StorageRouter


@pytest.fixture
def mock_writer():
    writer = MagicMock()
    writer.write = MagicMock()
    writer.close = MagicMock()
    writer.close_all = MagicMock()
    return writer


def test_router_flushes_on_chunk_size(mock_writer):
    # Set chunk size to 2
    router = StorageRouter(storage_writer=mock_writer, chunk_size=2)

    trades = [
        {"tradeId": "1", "ts": 1704067200000, "instId": "BTC"},  # 2024-01-01
        {"tradeId": "2", "ts": 1704067201000, "instId": "BTC"},  # 2024-01-01
        {"tradeId": "3", "ts": 1704067202000, "instId": "BTC"},  # 2024-01-01
    ]

    router.process_trades(trades, stop_at=None)

    # Should have called write twice:
    # Once for the chunk (size 2) and once for the remaining record in finally
    assert mock_writer.write.call_count == 2
    mock_writer.close_all.assert_called_once()


def test_router_switches_date_boundaries(mock_writer):
    router = StorageRouter(storage_writer=mock_writer, chunk_size=10)

    day1_ts = 1704067200000  # 2024-01-01
    day2_ts = 1704153600000  # 2024-01-02

    trades = [
        {"tradeId": "1", "ts": day1_ts, "instId": "BTC"},
        {"tradeId": "2", "ts": day2_ts, "instId": "BTC"},  # Trigger switch
    ]

    router.process_trades(trades, stop_at=None)

    # When Day 2 arrives, it should close Day 1
    mock_writer.close.assert_called_with(trade_date=date(2024, 1, 1))
    # Finally block handles the rest
    mock_writer.close_all.assert_called_once()


def test_router_stops_at_sentinel(mock_writer):
    router = StorageRouter(storage_writer=mock_writer, chunk_size=10)

    trades = [
        {"tradeId": "1", "ts": 1704067200000, "instId": "BTC"},
        {"tradeId": "STOP", "ts": 1704067201000, "instId": "BTC"},
        {"tradeId": "2", "ts": 1704067202000, "instId": "BTC"},
    ]

    router.process_trades(trades, stop_at="STOP")

    # Should only process the first trade
    # _flush_all in finally will write that one trade
    assert mock_writer.write.call_count == 1
    # Verify the third trade was never buffered
    last_table = mock_writer.write.call_args[1]["table"]
    assert last_table.num_rows == 1


def test_router_cleanup_on_exception(mock_writer):
    router = StorageRouter(storage_writer=mock_writer, chunk_size=10)

    # Generator that yields one trade then crashes
    def flaky_gen():
        yield {"tradeId": "1", "ts": 1704067200000, "instId": "BTC"}
        raise RuntimeError("Network failed mid-iteration")

    with pytest.raises(RuntimeError, match="Network failed"):
        router.process_trades(flaky_gen(), stop_at=None)

    # Ensure even on crash, data was flushed and writers were closed
    assert mock_writer.write.call_count == 1
    mock_writer.close_all.assert_called_once()
