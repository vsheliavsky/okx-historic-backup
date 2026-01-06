import pyarrow.parquet as pq

from okx_historic_backup.file_storage.storage_readers.local_storage_reader import (
    LocalStorageReader,
)


def test_get_latest_trade_id_deletes_corrupt_file_and_retries(
    base_test_dir, sample_trade_table, trade_date
):
    instrument = "BTC-USDT"
    reader = LocalStorageReader(base_dir=base_test_dir)

    # Create a real folder so _get_latest_file_name finds something
    folder = base_test_dir / instrument / "2026" / "01"
    folder.mkdir(parents=True)

    file_path_ok = folder / "1_test.parquet"
    pq.ParquetWriter(where=file_path_ok, schema=sample_trade_table.schema).write_table(
        table=sample_trade_table
    )

    file_path_corrupt = folder / "2_test.parquet"
    file_path_corrupt.write_text("dummy")

    result = reader.get_latest_trade_id(instrument)

    # ASSERTIONS
    assert result == "1002"  # From your mock_table fixture
    assert list(folder.glob("**/*.parquet")) == [file_path_ok]
