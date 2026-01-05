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
    """
    Fetcher for historical trades from OKX.

    This class handles pagination and retry logic for fetching historical trades
    for a given instrument, yielding trades one at a time to keep memory usage low.

    Attributes:
        api (MarketAPI): The OKX Market API instance used to fetch trade data.

    Methods:
        yield_historical_trades(instrument_id, after):
            Generator that yields historical trades for an instrument, starting
            from a specified trade ID or timestamp and moving backward in time.

            Args:
                instrument_id (InstrumentId): The OKX instrument identifier
                    (e.g., "BTC-USDT").
                after (TradeId | _Timestamp): The trade ID or timestamp to fetch
                    trades older than. On initial call, this is a _Timestamp;
                    on subsequent iterations, it's updated to the last trade ID
                    in the previous batch for pagination.

            Yields:
                Trade: Dictionary containing trade data with normalized fields:
                    - sz (float): Trade size
                    - px (float): Trade price
                    - ts (int): Trade timestamp
                    - All other fields from the API response

            Raises:
                Retries on failure up to MAX_ATTEMPTS times with WAIT_TIME_SEC
                between attempts before raising the exception.

            Note:
                The OKX 'after' parameter fetches trades older than the specified
                value, while 'before' fetches newer trades. Pagination uses tradeId
                after the first batch, then continues until no more trades are
                returned.
    """

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
