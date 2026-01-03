import os
from logging import getLogger
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

logger = getLogger(__name__)


class LocalStorageWriter:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.expanduser(base_dir)
        self.writers: dict[str, pq.ParquetWriter] = {}

    def write(self, table: pa.Table, file_name: str):
        logger.info(f"Saving table to {file_name}")

        if file_name not in self.writers:
            path = os.path.join(self.base_dir, file_name)

            parent_dir = Path(path).parent
            if not parent_dir.exists():
                logger.info(f"Directory {parent_dir} does not exist. Creating it...")
                parent_dir.mkdir(parents=True, exist_ok=True)

            self.writers[file_name] = pq.ParquetWriter(path, table.schema)
        self.writers[file_name].write_table(table)

    def close(self):
        logger.info("Closing all writers")
        for w in self.writers.values():
            if w.is_open:
                w.close()
