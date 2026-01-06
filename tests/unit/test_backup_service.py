from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from okx_historic_backup.backup_service import BackupService
from okx_historic_backup.utilities.custom_types import CLIArgs


@pytest.fixture
def mock_cli_args():
    return CLIArgs(instrument_ids=["BTC-USDT", "ETH-USDT"], start_at=None, stop_at=None)


@pytest.fixture
def mock_storage_reader():
    return MagicMock()


@pytest.fixture
def mock_storage_router():
    return MagicMock()


@pytest.fixture
def mock_trade_fetcher():
    return MagicMock()


def test_get_start_calculates_correct_midnight(
    mock_storage_router, mock_storage_reader, mock_trade_fetcher
):
    service = BackupService(
        mock_storage_router, mock_storage_reader, mock_trade_fetcher
    )

    # Freeze time to a specific date: 2026-01-05 15:30:00
    frozen_now = datetime(2026, 1, 5, 15, 30, 0, tzinfo=UTC)

    with patch("okx_historic_backup.backup_service.datetime") as mock_dt:
        mock_dt.now.return_value = frozen_now
        # We need to mock the constructor for the return value of _get_start
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

        start_ts = service._get_start()

        # Expected: 2026-01-05 00:00:00 UTC
        expected_dt = datetime(2026, 1, 5, 0, 0, 0, tzinfo=UTC)
        expected_ts = str(int(expected_dt.timestamp() * 1_000))

        assert start_ts == expected_ts


def test_backup_instrument_orchestration(
    mock_storage_router, mock_storage_reader, mock_trade_fetcher
):
    service = BackupService(
        mock_storage_router, mock_storage_reader, mock_trade_fetcher
    )

    instrument = "SOL-USDT"
    mock_storage_reader.get_latest_trade_id.return_value = "PREV_ID"
    mock_trade_fetcher.yield_historical_trades.return_value = iter(
        [{"tradeId": "NEW_1"}]
    )

    # Act
    service._backup_instrument(instrument, stop_at=None, start_at="START_TS")

    # Verify Reader was checked for the sentinel (stop_at)
    mock_storage_reader.get_latest_trade_id.assert_called_with(instrument_id=instrument)

    # Verify Fetcher was called with start_at
    mock_trade_fetcher.yield_historical_trades.assert_called_with(
        instrument_id=instrument, after="START_TS"
    )

    # Verify Router was called with the trades and the stop_at ID
    mock_storage_router.process_trades.assert_called_once()
    args, kwargs = mock_storage_router.process_trades.call_args
    assert kwargs["stop_at"] == "PREV_ID"


def test_backup_all_instruments_loops_correctly(
    mock_storage_router, mock_storage_reader, mock_trade_fetcher, mock_cli_args
):
    service = BackupService(
        mock_storage_router, mock_storage_reader, mock_trade_fetcher
    )

    # Patch the internal _backup_instrument to avoid deep integration testing here
    with patch.object(service, "_backup_instrument") as mock_backup_one:
        service.backup_all_instruments(mock_cli_args)

        # Should be called for BTC and ETH (from mock_cli_args)
        assert mock_backup_one.call_count == 2
        mock_backup_one.assert_any_call(
            instrument_id="BTC-USDT", start_at=None, stop_at=None
        )


def test_backup_instrument_prefers_cli_args(
    mock_storage_router, mock_storage_reader, mock_trade_fetcher
):
    service = BackupService(
        mock_storage_router, mock_storage_reader, mock_trade_fetcher
    )

    # If the user provides stop_at and start_at via CLI,
    # the service should NOT call the reader or _get_start.
    service._backup_instrument("BTC-USDT", stop_at="USER_STOP", start_at="USER_START")

    mock_storage_reader.get_latest_trade_id.assert_not_called()
    mock_trade_fetcher.yield_historical_trades.assert_called_with(
        instrument_id="BTC-USDT", after="USER_START"
    )
    mock_storage_router.process_trades.assert_called_with(
        trades=mock_trade_fetcher.yield_historical_trades(), stop_at="USER_STOP"
    )
