import pyarrow.parquet as pq

from okx_historic_backup.file_storage.storage_writers.local_storage_writer import (
    LocalStorageWriter,
)


def test_writer_creates_correct_structure(
    base_test_dir, sample_trade_table, trade_date
):
    writer = LocalStorageWriter(str(base_test_dir))

    writer.write(sample_trade_table, trade_date)
    writer.close_all()

    # Check if directory exists: base/inst/year/month/
    expected_dir = base_test_dir / "BTC-USDT" / "2026" / "1"
    assert expected_dir.exists()

    # Check if file was created
    files = list(expected_dir.glob("*.parquet"))
    assert len(files) == 1

    # Verify file content
    saved_table = pq.read_table(files[0])
    assert saved_table.num_rows == 2
    assert saved_table.column("tradeId")[0].as_py() == "1001"
