from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Any

type InstrumentId = str
type TradeId = str
type _Timestamp = str
type Trade = dict[str, Any]
type Trades = list[Trade]


@dataclass
class CLIArgs:
    """Structured container for parsed arguments."""

    instrument_ids: Iterable[InstrumentId]
    after: TradeId | _Timestamp | None


class QueryParamTypeEnum(Enum):
    TradeId = "1"
    _Timestamp = "2"
