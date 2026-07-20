from __future__ import annotations

import json
import logging
import os
import re

_SECRET_PATTERNS = (
    re.compile(r"(?:sk|pplx)-[A-Za-z0-9_-]+"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    re.compile(r"(?i)(api[_ -]?key\s*[:=]\s*)\S+"),
)


def redact_log_value(value: object) -> str:
    """Redact common credentials before a value reaches a log sink."""

    text = str(value)
    text = _SECRET_PATTERNS[0].sub("[redacted-key]", text)
    text = _SECRET_PATTERNS[1].sub("Bearer [redacted]", text)
    text = _SECRET_PATTERNS[2].sub(r"\1[redacted]", text)
    return text[:2000]


class _StructuredFormatter(logging.Formatter):
    """Compact JSON formatter for CI and log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_log_value(record.getMessage()),
        }
        run_id = getattr(record, "run_id", None)
        if run_id:
            payload["run_id"] = redact_log_value(run_id)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def setup_logging(
    level: int = logging.INFO,
    name: str | None = None,
    *,
    structured: bool | None = None,
) -> logging.Logger:
    """Configure one process-local logger with optional JSON output.

    Set ``START_LOG_FORMAT=json`` to enable structured records without
    changing callers that expect human-readable console logs.
    """

    logger = logging.getLogger(name if name else "")
    if not logger.handlers:
        logger.setLevel(level)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        if structured is None:
            structured = os.environ.get("START_LOG_FORMAT", "").casefold() == "json"
        formatter: logging.Formatter = (
            _StructuredFormatter()
            if structured
            else logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger
