import os
from datetime import date
from logging import getLogger
from pathlib import Path
from uuid import uuid7

import pyarrow as pa
import pyarrow.parquet as pq
from utilities.custom_types import InstrumentId

logger = getLogger(__name__)


class LocalStorageWriter:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.expanduser(base_dir)
        self.writers: dict[date, pq.ParquetWriter] = {}

    def write(self, table: pa.Table, trade_date: date) -> None:
        instrument_id: InstrumentId = table.column("instId")[0].as_py()
        file_name = (
            f"{instrument_id}/{trade_date.year}/"
            + f"{trade_date.month}/{trade_date.day}_{uuid7()}.parquet"
        )
        logger.info(f"Saving table to {file_name}")

        if trade_date not in self.writers:
            path = os.path.join(self.base_dir, file_name)
            parent_dir = Path(path).parent

            if not parent_dir.exists():
                logger.info(f"Directory {parent_dir} does not exist. Creating it...")
                parent_dir.mkdir(parents=True, exist_ok=True)

            self.writers[trade_date] = pq.ParquetWriter(path, table.schema)

        self.writers[trade_date].write_table(table)

    def close(self, trade_date: date):
        logger.info(f"Closing writer {trade_date}")
        if not trade_date:
            logger.info("No writer specified to close")
            return
        if trade_date not in self.writers:
            logger.info(f"Writer {trade_date} not found among active writers")
            return

        self.writers[trade_date].close()
        del self.writers[trade_date]

    def close_all(self):
        logger.info("Closing all writers")
        for w in self.writers.values():
            w.close()
