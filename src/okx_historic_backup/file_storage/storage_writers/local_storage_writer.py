import os
from datetime import date
from logging import getLogger
from pathlib import Path
from uuid import uuid7

import pyarrow as pa
import pyarrow.parquet as pq
from okx_historic_backup.utilities.custom_types import InstrumentId

logger = getLogger(__name__)


class LocalStorageWriter:
    """Handles persistent storage of trade data to the local filesystem using Parquet.

    This class manages multiple active Parquet writers, organizing files into a
    hierarchical directory structure based on instrument ID and date. It ensures
    that directories are created on demand and provides mechanisms to close
    specific or all active file handles.

    Attributes:
        base_dir (str): The root directory where Parquet files will be stored.
        writers (dict[date, pq.ParquetWriter]): A mapping of dates to their
            respective active ParquetWriter instances.
    """

    def __init__(self, base_dir: str):
        self.base_dir = os.path.expanduser(base_dir)
        self.writers: dict[date, pq.ParquetWriter] = {}

    def write(self, table: pa.Table, trade_date: date) -> None:
        """Writes a PyArrow Table to a date-specific Parquet file.

        The file path is automatically generated using the pattern:
        `{base_dir}/{instrument_id}/{year}/{month}/{day}_{uuid7}.parquet`.
        If a writer for the given date does not exist, a new one is initialized
        and the necessary directory structure is created.

        Args:
            table: The PyArrow Table containing trade records to persist.
            trade_date: The execution date used to determine the storage path.

        Note:
            The instrument ID is extracted directly from the 'instId' column
             of the provided table.
        """
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
        """Closes the Parquet writer associated with a specific date.

        This ensures all buffered data for that date is flushed to disk
        and the file handle is released.

        Args:
            trade_date: The date key of the writer to be closed.
        """
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
        """Closes all currently active Parquet writers.

        This is typically called during teardown or when a processing
        batch is complete to prevent memory leaks or file corruption.
        """
        logger.info("Closing all writers")
        for w in self.writers.values():
            w.close()
