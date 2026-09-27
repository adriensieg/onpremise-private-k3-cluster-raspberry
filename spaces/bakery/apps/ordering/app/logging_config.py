"""Minimal, readable logging setup."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    # anyio/mcp can be chatty at DEBUG; keep them at INFO unless asked otherwise.
    if level.upper() != "DEBUG":
        logging.getLogger("mcp").setLevel(logging.INFO)
