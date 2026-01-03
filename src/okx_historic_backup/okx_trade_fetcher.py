from collections.abc import Generator
from logging import getLogger

from okx.MarketData import MarketAPI
from utilities.custom_types import (
    HistoricalTradeFetchParams,
    InstrumentId,
    Trade,
    TradeId,
    _Timestamp,
)

logger = getLogger(__name__)


class OKXTradeFetcher:
    def __init__(self, market_api: MarketAPI | None = None):
        self.api = market_api or MarketAPI()

    def yield_historical_trades(
        self,
        instrument_id: InstrumentId,
        after: TradeId | _Timestamp,
        before: TradeId | None = None,
    ) -> Generator[Trade]:
        while True:
            # OKX 'after' parameter is the tradeId/_Timestamp to fetch data older than,
            # while before is newer than
            logger.info(
                f"Fetching trades for {instrument_id} after {after} before {before}"
            )

            params: HistoricalTradeFetchParams = {
                "instId": instrument_id,
                "after": after,
            }
            if before is not None:
                params["before"] = before

            response = self.api.get_history_trades(**params)

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
