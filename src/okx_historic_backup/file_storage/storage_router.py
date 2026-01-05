from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, date, datetime
from logging import getLogger

import pyarrow as pa
from okx_historic_backup.utilities.custom_types import Trade, TradeId

from .storage_writers.storage_writer_protocol import StorageWriter

logger = getLogger(__name__)


class StorageRouter:
    """Routes and buffers trade data to storage based on dates and chunk sizes.

    This class manages the lifecycle of trade data ingestion, ensuring that trades
    are grouped by their execution date and written to storage using a provided
    StorageWriter implementation. It handles memory buffering and triggers
    flushes when a buffer reaches a specified chunk size or when the date changes.

    Attributes:
        storage_writer (StorageWriter): The backend writer responsible for data
            persistence.
        chunk_size (int): Maximum number of records to hold in memory before flushing.
        buffers (dict): A mapping of dates to lists of trade dictionaries.
        current_date (date): The date currently being processed to detect date
            boundaries.
    """

    def __init__(self, storage_writer: StorageWriter, chunk_size: int):
        self.storage_writer = storage_writer
        self.chunk_size = chunk_size
        self.buffers = defaultdict(list)
        self.current_date = date(year=1970, month=1, day=1)

    def process_trades(self, trades: Iterable[Trade], stop_at: TradeId | None):
        """Iterates through trades, routing them to date-specific buffers and flushing.

        This method processes an iterable of trades. If it encounters a `trade_id`
        that matches the `stop_at`, it stops processing.
        It detects when a trade belongs to a new date, triggers a flush/close for the
        previous date, and manages chunk-based flushes.

        Args:
            trades: An iterable collection of trade dictionaries.
            stop_at: The id where iteration should stop.
        Raises:
            Exception: Re-raises any exception encountered during processing after
                attempting to flush remaining buffers and close writers.
        """
        try:
            for trade in trades:
                if trade["tradeId"] == stop_at:
                    logger.info(f"Reached sentinel value(stop_at): {stop_at}.")
                    break

                # Route by date
                trade_date = datetime.fromtimestamp(
                    int(trade["ts"]) / 1_000, tz=UTC
                ).date()

                if trade_date != self.current_date:
                    logger.info(f"Flushing and switching to buffer for {trade_date}")
                    self._flush(trade_date=self.current_date)
                    self.storage_writer.close(trade_date=self.current_date)
                    self.current_date = trade_date

                self.buffers[trade_date].append(trade)

                # Chunk check
                if len(self.buffers[trade_date]) >= self.chunk_size:
                    self._flush(trade_date=trade_date)

        except Exception as e:
            logger.error(f"Error processing trades: {e}")
            raise
        finally:
            # Final cleanup - ensure writer is closed even if error occurs
            self._flush_all()
            self.storage_writer.close_all()

    def _flush(self, trade_date: date):
        """Converts buffered data for a specific date into a PyArrow Table and writes
        it.

        Args:
            trade_date: The specific date key in the buffer to be flushed.
        """
        if not self.buffers[trade_date]:
            logger.info(f"No records to flush for {trade_date}")
            return

        table = pa.Table.from_pylist(self.buffers[trade_date])

        instrument_id = self.buffers[trade_date][0]["instId"]

        logger.info(
            f"Flushing {len(self.buffers[trade_date])} "
            + f"{instrument_id} records for {trade_date}"
        )

        self.storage_writer.write(table=table, trade_date=trade_date)

        logger.info(f"Clearing buffer for {trade_date}")
        self.buffers[trade_date] = []

    def _flush_all(self):
        """Iterates through all existing buffers and flushes them to the storage
        writer."""
        for trade_date in list(self.buffers.keys()):
            self._flush(trade_date=trade_date)
