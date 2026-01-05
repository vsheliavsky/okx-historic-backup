import logging
import sys
import tomllib
from datetime import datetime
from pathlib import Path

import httpx


def setup_logging(level=logging.INFO) -> logging.Logger:
    log_filename = f"backup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler(sys.stdout)],
    )

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
