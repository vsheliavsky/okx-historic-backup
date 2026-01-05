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
        "--start_at",
        type=str,
        default=None,
        help="Fetch data older than this _Timestamp",
    )

    parser.add_argument(
        "--stop_at",
        type=str,
        default=None,
        help="Stop fetching at this tradeId",
    )

    args = parser.parse_args()

    match (args.instrument_ids, args.start_at, args.stop_at):
        case (None, _, _):
            raise ValueError(f"Invalid input for instrument_ids: {args.instrument_ids}")
        case (list(), str(), None):
            raise ValueError("Passed start_at, but not stop_at")
        case (list(), None, str()):
            raise ValueError("Passed stop_at, but not start_at")
        case _:
            return CLIArgs(
                instrument_ids=args.instrument_ids,
                start_at=args.start_at,
                stop_at=args.stop_at,
            )
