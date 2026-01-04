from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime
from logging import getLogger

import pyarrow as pa
from utilities.custom_types import Trade

from .storage_writers.storage_writer_protocol import StorageWriter

logger = getLogger(__name__)


class StorageRouter:
    def __init__(self, storage_writer: StorageWriter, chunk_size: int):
        self.storage_writer = storage_writer
        self.chunk_size = chunk_size
        self.buffers = defaultdict(list)
        self.current_date = date(year=1970, month=1, day=1)

    def process_trades(self, trades: Iterable[Trade]):
        try:
            for trade in trades:
                # Route by date
                trade_date = datetime.fromtimestamp(int(trade["ts"]) / 1_000).date()
                if trade_date != self.current_date:
                    logger.info(f"Flushing and switching to buffer for {trade_date}")
                    self._flush(trade_date=self.current_date)
                    self.storage_writer.close(trade_date=trade_date)
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
        for trade_date in list(self.buffers.keys()):
            self._flush(trade_date=trade_date)
