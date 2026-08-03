"""Application logging with console and rotating files."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")


def configure_logging(level: str = "INFO") -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if any(getattr(h, "name", None) == "booking_file" for h in root.handlers):
        return
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler = RotatingFileHandler(
        LOG_DIR/"backend.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    handler.name = "booking_file"
    handler.setFormatter(formatter)
    root.addHandler(handler)
    client = RotatingFileHandler(
        LOG_DIR/"frontend.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    client.name = "frontend_file"
    client.setFormatter(formatter)
    frontend_logger = logging.getLogger("frontend")
    frontend_logger.addHandler(client)
    frontend_logger.propagate = False
    frontend_logger.setLevel(logging.INFO)
