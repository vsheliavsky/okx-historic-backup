from typing import Protocol

import pyarrow as pa


class StorageWriter(Protocol):
    def write(
        self,
        table: pa.Table,
        file_name: str,
    ) -> None: ...

    def close(self) -> None: ...
