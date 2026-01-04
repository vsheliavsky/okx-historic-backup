import argparse

from .custom_types import CLIArgs


def parse_input_args(defaults: dict) -> CLIArgs:
    parser = argparse.ArgumentParser(
        description="OKX Historical Trade Loader - Fetch and save trade data to Parquet"
    )

    parser.add_argument(
        "--instrument_ids",
        type=str,
        default=defaults["api_params"]["instrument_ids"],
        choices=defaults["api_params"]["instrument_ids"],
        help="The OKX instrument ID (e.g., BTC-USDT)",
        nargs="+",
    )

    parser.add_argument(
        "--after",
        type=str,
        default=None,
        help="Fetch data older than this tradeId",
    )

    args = parser.parse_args()

    return CLIArgs(
        instrument_ids=args.instrument_ids,
        after=args.after,
    )
