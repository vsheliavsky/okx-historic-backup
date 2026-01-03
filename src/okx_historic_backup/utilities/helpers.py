import logging
import sys
import tomllib
from datetime import datetime
from pathlib import Path


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
