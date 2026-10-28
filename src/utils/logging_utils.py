"""
logging_utils.py — Consistent logger factory for all training scripts.
"""

import logging
import sys
from pathlib import Path


def get_logger(name: str,
               log_file: str | None = None,
               level: int = logging.INFO) -> logging.Logger:
    """
    Return a logger with:
      - StreamHandler → stdout (INFO and above)
      - FileHandler   → log_file (optional; creates parent dirs automatically)

    Re-uses an existing logger of the same name without adding duplicate handlers.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Optional file handler
    if log_file is not None:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
