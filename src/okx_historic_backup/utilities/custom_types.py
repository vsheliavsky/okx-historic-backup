from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict

type InstrumentId = str
type TradeId = str
type _Timestamp = str
type Trade = dict[str, Any]
type Trades = list[Trade]


class HistoricalTradeFetchParams(TypedDict):
    instId: InstrumentId
    after: NotRequired[TradeId | _Timestamp]
    before: NotRequired[TradeId]


@dataclass
class CLIArgs:
    """Structured container for parsed arguments."""

    instrument_ids: Iterable[InstrumentId]
    after: str | None
    before: str | None
