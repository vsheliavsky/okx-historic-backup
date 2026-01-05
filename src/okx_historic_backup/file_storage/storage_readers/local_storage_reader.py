import os
from logging import getLogger
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq
from pyarrow import ArrowInvalid
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from okx_historic_backup.utilities.custom_types import InstrumentId, TradeId

logger = getLogger(__name__)


class LocalStorageReader:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.expanduser(base_dir)

    def _get_all_instrument_files(self, instrument_id: InstrumentId):
        instrument_path = Path(self.base_dir) / instrument_id

        # Check if instrument directory exists
        if not instrument_path.is_dir():
            logger.info(f"Instrument path {instrument_path} does not exist.")
            return None

        # Recursive glob: '**' tells Pathlib to look through all subfolders
        # This will find: .../2025/12/31.parquet and .../2026/01/01.parquet
        parquet_files = list(instrument_path.glob("**/*.parquet"))
        return parquet_files

        if not parquet_files:
            logger.info(f"No parquet files found for instrument {instrument_id}.")
            return None

    def _get_latest_file_name(self, instrument_id: InstrumentId) -> str | None:
        """Navigates instrument_id/year/month/day.parquet to find the most recent file.

        Args:
            instrument_id (InstrumentId): The instrument ID to look up.
        Returns:
            str | None: The path to the latest parquet file or None if not found.
        """
        # Sorting works perfectly here because the paths are hierarchical:
        # '2025/12/31.parquet' comes before '2026/01/01.parquet' alphabetically
        parquet_files = self._get_all_instrument_files(instrument_id=instrument_id)
        if not parquet_files:
            return None

        parquet_files.sort()

        # Return the absolute path of the last (latest) file
        _abs_path = str(parquet_files[-1])
        logger.info(f"Latest parquet file for {instrument_id} is {_abs_path}")
        return _abs_path

    @retry(
        retry=retry_if_exception_type(ArrowInvalid),
        stop=stop_after_attempt(2),  # Total attempts: 1 (original) + 1 (retry)
        reraise=True,  # Raise the final ArrowInvalid if the 2nd attempt also fails
    )
    def get_latest_trade_id(self, instrument_id: InstrumentId) -> TradeId | None:
        """Find the latest parquet file for the specified instrument_id and get the
        latest tradeId based on the max timestamp.

        Args:
            instrument_id (InstrumentId): The instrument ID to look up.

        Returns:
            TradeId | None: The latest tradeId or None if not found.
        """
        file_path = self._get_latest_file_name(instrument_id)
        if not file_path:
            return None

        try:
            pf = pq.ParquetFile(file_path)
            last_rg_idx = pf.num_row_groups - 1
            if last_rg_idx < 0:
                logger.info(f"No row groups found in file {file_path}")
                return None

            #  Read only the necessary columns into an Arrow Table
            # -> find the max timestamp
            # -> find the index of that timestamp
            table = pf.read_row_group(last_rg_idx, columns=["ts", "tradeId"])
            max_ts = pc.max(table.column("ts"))
            idx = pc.index(table.column("ts"), max_ts)

            if idx.as_py() == -1:  # Not found
                logger.info(f"No trades found in file {file_path}")
                return None

            latest_id_scalar = table.column("tradeId")[idx.as_py()]

            trade_id = str(latest_id_scalar)
            logger.info(
                f"Latest tradeId for instrument {instrument_id} "
                + f"in file {file_path} is {trade_id}"
            )
            return trade_id

        except ArrowInvalid as ai:
            logger.error(f"Corruption detected: {file_path}")
            if os.path.exists(file_path):
                os.remove(file_path)
            raise ai
