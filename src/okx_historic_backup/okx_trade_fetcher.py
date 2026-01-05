from collections.abc import Generator, Sequence
from logging import getLogger

from okx.MarketData import MarketAPI
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from okx_historic_backup.utilities.custom_types import (
    InstrumentId,
    QueryParamTypeEnum,
    Trade,
    TradeId,
    _Timestamp,
)
from okx_historic_backup.utilities.helpers import (
    is_retryable_httpx_error,
    load_defaults,
)

logger = getLogger(__name__)
API_DEFAULTS = load_defaults()["api_params"]
MAX_ATTEMPTS = API_DEFAULTS["max_attempts"]
MIN_TIME_SEC = API_DEFAULTS["min_time_sec"]
MAX_TIME_SEC = API_DEFAULTS["max_time_sec"]
MULTIPLIER = API_DEFAULTS["multiplier"]


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

    @retry(
        retry=retry_if_exception(is_retryable_httpx_error),
        wait=wait_exponential(
            multiplier=MULTIPLIER, min=MIN_TIME_SEC, max=MAX_TIME_SEC
        ),
        stop=stop_after_attempt(MAX_ATTEMPTS),
        reraise=True,
    )
    def _fetch_single_page(
        self,
        instrument_id: InstrumentId,
        after: TradeId | _Timestamp,
        type: QueryParamTypeEnum,
    ) -> Sequence[Trade] | None:
        logger.info(f"Fetching trades for {instrument_id} after {after}")

        response = self.api.get_history_trades(
            instId=instrument_id, after=after, type=type.value
        )

        return response.get("data", None)

    def yield_historical_trades(
        self,
        instrument_id: InstrumentId,
        after: TradeId | _Timestamp,
    ) -> Generator[Trade]:
        type = QueryParamTypeEnum._Timestamp
        while True:
            trades = self._fetch_single_page(
                instrument_id=instrument_id, after=after, type=type
            )

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
