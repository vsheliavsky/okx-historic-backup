import logging
import os
import sys
import tomllib
from datetime import datetime
from pathlib import Path

import httpx


def setup_logging(level=logging.INFO) -> logging.Logger:
    # 1. Create the logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 2. Define the log file path
    log_filename = f"backup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = os.path.join(log_dir, log_filename)

    log_format = "%(asctime)s | [%(levelname)s] | %(name)s: %(message)s"

    # 3. Configure the root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )

    # 4. Silence httpx unless the global level is DEBUG
    # If the user passed INFO, httpx will be set to WARNING
    if level > logging.DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)
    else:
        logging.getLogger("httpx").setLevel(logging.DEBUG)

    return logging.getLogger("BackupSystem")


def load_defaults(config_name: str = "defaults.toml") -> dict:
    default_path = Path(__file__).parent.parent.parent.parent / config_name
    with open(default_path, "rb") as f:
        return tomllib.load(f)


def is_retryable_httpx_error(exception):
    """
    Returns True for transient network/server issues.
    Returns False for permanent client errors (400, 401, 404).
    """
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on Rate Limit (429) and Server Errors (5xx)
        return exception.response.status_code in [429, 500, 502, 503, 504]

    # Retry on timeouts and connection drops (Transport errors)
    return isinstance(exception, (httpx.TimeoutException, httpx.NetworkError))
