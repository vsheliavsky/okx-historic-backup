from collections.abc import Generator
from logging import getLogger

from okx.MarketData import MarketAPI
from retrying import retry
from utilities.custom_types import (
    InstrumentId,
    QueryParamTypeEnum,
    Trade,
    TradeId,
    _Timestamp,
)
from utilities.helpers import load_defaults

logger = getLogger(__name__)
API_DEFAULTS = load_defaults()["api_params"]
MAX_ATTEMPTS = API_DEFAULTS["max_attempts"]
WAIT_TIME_SEC = API_DEFAULTS["wait_time_sec"]


class OKXTradeFetcher:
    def __init__(
        self,
        market_api: MarketAPI | None = None,
    ):
        self.api = market_api or MarketAPI()

    @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=WAIT_TIME_SEC)
    def yield_historical_trades(
        self,
        instrument_id: InstrumentId,
        after: TradeId | _Timestamp,
    ) -> Generator[Trade]:
        type = QueryParamTypeEnum._Timestamp
        while True:
            # OKX 'after' parameter is the tradeId/_Timestamp to fetch data older than,
            # while before is newer than
            logger.info(f"Fetching trades for {instrument_id} after {after}")

            response = self.api.get_history_trades(
                instId=instrument_id, after=after, type=type.value
            )

            trades = response.get("data", [])
            if not trades:
                break

            for trade in trades:
                yield {
                    **trade,
                    "sz": float(trade["sz"]),
                    "px": float(trade["px"]),
                    "ts": int(trade["ts"]),
                }

            # Update pagination cursor to the last trade ID in the batch
            after = trades[-1]["tradeId"]
            type = QueryParamTypeEnum.TradeId
