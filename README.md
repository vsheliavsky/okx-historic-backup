# OKX Historic Backup Tool

A Python utility for backing up historical trading data from the OKX cryptocurrency exchange. This tool fetches historical trades for specified instruments and stores them locally in a structured format.

## Overview

The OKX Historic Backup Tool automates the process of:
- Fetching historical trade data from the OKX Market API
- Tracking the latest backed-up trades to avoid duplicates
- Storing trades locally in chunked Parquet files for efficient storage and retrieval
- Supporting batch operations across multiple trading instruments

## Features

- **Incremental Backups**: Only fetches trades newer than the last backed-up trade for each instrument
- **Efficient Storage**: Uses Apache Parquet format with configurable chunk sizes for optimal storage efficiency
- **Pagination Support**: Automatically handles API pagination when fetching large amounts of historical data
- **Retry Logic**: Built-in retry mechanism with configurable attempts and wait times for resilient API calls
- **Flexible Configuration**: Customizable settings via `defaults.toml` for API parameters, storage paths, and instrument selections
- **Comprehensive Logging**: Detailed logging throughout the backup process for monitoring and troubleshooting

## Project Structure

```
okx-historic-backup/
├── src/okx_historic_backup/
│   ├── main.py                 # Entry point for the application
│   ├── backup_service.py       # Core backup orchestration logic
│   ├── okx_trade_fetcher.py   # OKX API integration for fetching trades
│   ├── file_storage/           # Storage layer abstraction
│   │   ├── storage_router.py   # Routes data to appropriate storage backend
│   │   ├── storage_readers/    # Reader implementations
│   │   └── storage_writers/    # Writer implementations
│   └── utilities/              # Helper functions and utilities
│       ├── custom_types.py     # Type definitions
│       ├── helpers.py          # Common utilities
│       └── input_param_parser.py # CLI argument parsing
├── defaults.toml               # Configuration file
├── pyproject.toml              # Project metadata and dependencies
└── README.md                   # This file
```

## Installation

### Prerequisites
- Python 3.14+
- pip or compatible package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd okx-historic-backup
```

2. Install dependencies:
```bash
pip install -e .
```

For development, install with dev dependencies:
```bash
pip install -e ".[dev]"
```

## Configuration

Edit `defaults.toml` to customize the tool's behavior:

```toml
[api_params]
instrument_ids = ["BTC-USDT", "ETH-USDT"]  # Instruments to backup
max_attempts = 3                             # Retry attempts for API calls
wait_time_sec = 2                            # Wait time between retries

[file_storage]
chunk_size = 2000                            # Trades per Parquet file
base_dir = "~/_backups_/raw_data/okx/historical_trades"  # Storage location
```

## Usage

After installation with `pip install -e .`, you can run the tool in two ways:

### Method 1: Using the CLI Command (Recommended)

```bash
okx-backup
```

With custom instruments:
```bash
okx-backup --instrument-ids BTC-USDT ETH-USDT XRP-USDT
```

### Method 2: Using Python Module

```bash
python -m okx_historic_backup
```

With custom instruments:
```bash
python -m okx_historic_backup --instrument-ids BTC-USDT ETH-USDT XRP-USDT
```

### Example Output

The tool will:
1. Log initialization and configuration loading
2. Fetch the latest backed-up trade ID for each instrument
3. Query the OKX API for trades newer than the last backup
4. Store new trades in Parquet files organized by instrument
5. Log completion status for each instrument

## Architecture

### Key Components

**BackupService**: Orchestrates the backup workflow by:
- Fetching the latest trade ID from storage for each instrument
- Requesting historical trades from OKXTradeFetcher
- Writing new trades to disk via StorageRouter

**OKXTradeFetcher**: Handles API interactions with the OKX Market API:
- Implements pagination for large datasets
- Applies retry logic with exponential backoff
- Yields trades one-at-a-time to minimize memory usage

**StorageRouter**: Manages data persistence:
- Routes trade data to the appropriate writer
- Implements chunking to create multiple files if necessary
- Normalizes numeric fields (size, price) for consistent storage

**StorageReader/Writer**: Abstract layer for persistence:
- LocalStorageReader: Reads existing trade data from local files
- LocalStorageWriter: Persists trade data to local Parquet files
- Supports future implementation of alternative backends (cloud storage, databases, etc.)

## Dependencies

- **pyarrow** (>=22.0.0): Apache Parquet format support for efficient storage
- **python-okx** (>=0.4.0): Official OKX API client library
- **retrying** (>=1.4.2): Retry decorator for resilient API calls

Development dependencies:
- **ruff** (>=0.9.0): Fast Python linter and formatter
- **ty** (>=0.0.1): Type checking utilities

## Contributing

When contributing to this project:

1. Run code formatting: `ruff format src/`
2. Lint code: `ruff check src/`
3. Follow PEP 8 style guidelines
4. Add docstrings to all public functions and classes

## Troubleshooting

### API Rate Limiting
If you encounter rate limit errors from OKX, increase `wait_time_sec` in `defaults.toml`.

### Storage Errors
Ensure the directory specified in `base_dir` exists and has write permissions.

### Missing Trades
Check the logs for API errors. The tool automatically resumes from the last backed-up trade, so re-running will continue the backup process.
