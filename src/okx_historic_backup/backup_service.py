from datetime import UTC, datetime, timedelta
from logging import getLogger

from file_storage import StorageReader, StorageRouter

from .okx_trade_fetcher import OKXTradeFetcher

logger = getLogger(__name__)


class BackupService:
    def __init__(self, storage_router: StorageRouter, storage_reader: StorageReader):
        self.storage_router = storage_router
        self.storage_reader = storage_reader
        self.trade_fetcher = OKXTradeFetcher()

    def _backup_instrument(self, instrument_id: str):
        logger.info(f"Starting backup for instrument {instrument_id}")

        latest_stored_trade_id = self.storage_reader.get_latest_trade_id(
            instrument_id=instrument_id
        )

        yesterday_utc = datetime.now(tz=UTC).date() - timedelta(days=1)
        yesterday_midnight_utc = datetime(
            year=yesterday_utc.year,
            month=yesterday_utc.month,
            day=yesterday_utc.day,
            tzinfo=UTC,
        )
        yesterday_midnight_utc_timestamp = str(
            yesterday_midnight_utc.timestamp() * 1_000
        )

        trades = self.trade_fetcher.yield_historical_trades(
            instrument_id=instrument_id,
            after=yesterday_midnight_utc_timestamp,
            before=latest_stored_trade_id,
        )

        self.storage_router.process_trades(trades=trades)
        logger.info(f"Backup completed for instrument {instrument_id}")

    def backup_all_instruments(self, instrument_ids: list[str]):
        for instrument_id in instrument_ids:
            self._backup_instrument(instrument_id=instrument_id)
