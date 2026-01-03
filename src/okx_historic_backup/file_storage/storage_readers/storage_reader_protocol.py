from typing import Protocol

from utilities.custom_types import InstrumentId, TradeId


class StorageReader(Protocol):
    def _get_latest_file_name(
        self, instrument_id: InstrumentId
    ) -> InstrumentId | None: ...

    def get_latest_trade_id(self, instrument_id: InstrumentId) -> TradeId | None: ...
