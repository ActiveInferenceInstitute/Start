from __future__ import annotations

import logging


def setup_logging(level: int = logging.INFO, name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name if name else "")
    if not logger.handlers:
        logger.setLevel(level)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger



