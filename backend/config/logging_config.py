"""
Logging Configuration for UAV Vision Construction Monitoring System
Sets up rotating file handlers and console logging for all modules.
"""

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging(log_dir: str = None, module_name: str = "app") -> logging.Logger:
    """
    Configure and return a logger with both file and console handlers.

    Args:
        log_dir:     Directory where log files will be stored.
        module_name: Name of the module creating the logger.

    Returns:
        Configured Logger instance.
    """
    from backend.config.settings import LOGS_DIR, LOGGING

    if log_dir is None:
        log_dir = LOGGING["log_dir"]

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers on re-import
    if logger.handlers:
        return logger

    # ── Formatter ──────────────────────────────────────────────
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Rotating File Handler ──────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / f"{module_name}.log",
        maxBytes=LOGGING["max_bytes"],
        backupCount=LOGGING["backup_count"],
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, LOGGING["file_level"]))
    file_handler.setFormatter(fmt)

    # ── Console Handler ─────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOGGING["console_level"]))
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Retrieve or create a configured logger for a named module.

    Args:
        module_name: Logger name / module identifier.

    Returns:
        Configured Logger.
    """
    return setup_logging(module_name=module_name)
