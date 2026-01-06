from datetime import UTC, datetime
from logging import getLogger

from okx_historic_backup.file_storage import StorageReader, StorageRouter
from okx_historic_backup.okx_trade_fetcher import OKXTradeFetcher
from okx_historic_backup.utilities.custom_types import (
    CLIArgs,
    InstrumentId,
    TradeId,
    _Timestamp,
)

logger = getLogger(__name__)


class BackupService:
    """Service responsible for backing up historical trading data for financial
    instruments.

    This service orchestrates the backup process by coordinating between storage
    operations, data retrieval, and persistence. It fetches historical trades for
    instruments and stores them using the configured storage backend.
    """

    def __init__(
        self,
        storage_router: StorageRouter,
        storage_reader: StorageReader,
        trade_fetcher: OKXTradeFetcher,
    ):
        self.storage_router = storage_router
        self.storage_reader = storage_reader
        self.trade_fetcher = trade_fetcher

    def _get_start(self) -> _Timestamp:
        yesterday_utc = datetime.now(tz=UTC).date()
        yesterday_midnight_utc = datetime(
            year=yesterday_utc.year,
            month=yesterday_utc.month,
            day=yesterday_utc.day,
            tzinfo=UTC,
        )
        return str(int(yesterday_midnight_utc.timestamp() * 1_000))

    def _backup_instrument(
        self,
        instrument_id: InstrumentId,
        stop_at: TradeId | None,
        start_at: TradeId | _Timestamp | None,
    ):
        """
        Backup historical trades for a specific instrument since yesterday midnight UTC.

        Retrieves the latest stored trade ID for the instrument, fetches all trades
        that occurred between the latest stored trade ID and yesterday midnight UTC,
        and processes them through the storage router to persist new trades.

        Args:
            instrument_id (str): The unique identifier of the instrument to backup. # TODO: amend

        Returns:
            None

        Raises:
            Exception: May raise exceptions from storage_reader, trade_fetcher, or
                       storage_router if operations fail.
        """

        start_at = start_at or self._get_start()
        stop_at = stop_at or self.storage_reader.get_latest_trade_id(
            instrument_id=instrument_id
        )
        logger.info(f"Starting backup for instrument {instrument_id}")

        trades = self.trade_fetcher.yield_historical_trades(
            instrument_id=instrument_id,
            after=start_at,
        )

        self.storage_router.process_trades(trades=trades, stop_at=stop_at)
        logger.info(f"Backup completed for instrument {instrument_id}")

    def backup_all_instruments(self, cli_args: CLIArgs):
        """
        Backup all instruments in the provided collection.

        Args:
            instrument_ids (Iterable[InstrumentId]): An iterable collection of  # TODO: amend
                instrument IDs to be backed up.

        Returns:
            None
        """
        for instrument_id in cli_args.instrument_ids:
            self._backup_instrument(
                instrument_id=instrument_id,
                start_at=cli_args.start_at,
                stop_at=cli_args.stop_at,
            )
