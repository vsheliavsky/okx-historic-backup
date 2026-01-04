from backup_service import BackupService
from file_storage import LocalStorageReader, LocalStorageWriter, StorageRouter
from okx_trade_fetcher import OKXTradeFetcher
from utilities.helpers import load_defaults, setup_logging
from utilities.input_param_parser import parse_input_args


def main():
    logger = setup_logging()
    logger.info("Starting OKX Historic Backup Tool")

    defaults = load_defaults()

    input_params = parse_input_args(defaults)

    storage_router = StorageRouter(
        storage_writer=LocalStorageWriter(
            base_dir=defaults["file_storage"]["base_dir"]
        ),
        chunk_size=defaults["file_storage"]["chunk_size"],
    )

    backup_service = BackupService(
        storage_router=storage_router,
        storage_reader=LocalStorageReader(
            base_dir=defaults["file_storage"]["base_dir"],
        ),
        trade_fetcher=OKXTradeFetcher(),
    )

    backup_service.backup_all_instruments(instrument_ids=input_params.instrument_ids)


if __name__ == "__main__":
    main()
