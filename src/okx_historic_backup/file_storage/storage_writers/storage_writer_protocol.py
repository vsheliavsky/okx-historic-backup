from datetime import date
from typing import Protocol

import pyarrow as pa


class StorageWriter(Protocol):
    def write(self, table: pa.Table, trade_date: date) -> None: ...

    def close(self, trade_date: date) -> None: ...

    def close_all(self) -> None: ...
