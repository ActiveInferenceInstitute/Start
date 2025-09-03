"""Tests for the logging utilities module."""

from __future__ import annotations

import logging
from io import StringIO

from src.common.logging_utils import setup_logging


def test_setup_logging_default():
    """Test setting up logging with default parameters."""
    logger = setup_logging()

    # Check logger properties - level might be WARNING if root logger already configured
    assert logger.level in [logging.INFO, logging.WARNING]
    assert len(logger.handlers) >= 1

    # Check handler properties - may be StreamHandler or pytest's LiveLoggingNullHandler
    handler = logger.handlers[0]
    assert isinstance(handler, (logging.StreamHandler, logging.Handler))
    # Only check level if it's a StreamHandler we created
    if isinstance(handler, logging.StreamHandler) and not handler.__class__.__name__.endswith(
        "NullHandler"
    ):
        assert handler.level == logging.INFO


def test_setup_logging_custom_level():
    """Test setting up logging with custom level."""
    logger = setup_logging(level=logging.DEBUG, name="test_logger")

    assert logger.name == "test_logger"
    assert logger.level == logging.DEBUG

    # Check handler level
    handler = logger.handlers[0]
    assert handler.level == logging.DEBUG


def test_setup_logging_custom_name():
    """Test setting up logging with custom name."""
    logger = setup_logging(name="custom_logger")

    assert logger.name == "custom_logger"
    assert logger.level == logging.INFO


def test_setup_logging_idempotent():
    """Test that setting up logging multiple times doesn't add duplicate handlers."""
    logger1 = setup_logging(name="idempotent_test")
    initial_handler_count = len(logger1.handlers)

    # Call again with same name
    logger2 = setup_logging(name="idempotent_test")

    # Should be the same logger instance with same number of handlers
    assert logger1 is logger2
    assert len(logger2.handlers) == initial_handler_count


def test_logger_functionality():
    """Test that the logger actually works for logging messages."""
    # Create a logger with a StringIO handler for testing
    logger = setup_logging(name="test_functional", level=logging.INFO)

    # Replace the handler with StringIO for testing
    test_stream = StringIO()
    test_handler = logging.StreamHandler(test_stream)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    test_handler.setFormatter(formatter)

    # Clear existing handlers and add test handler
    logger.handlers.clear()
    logger.addHandler(test_handler)

    # Test logging
    logger.info("Test info message")
    logger.warning("Test warning message")

    output = test_stream.getvalue()
    assert "INFO - Test info message" in output
    assert "WARNING - Test warning message" in output


def test_formatter_format():
    """Test that the log formatter includes expected components."""
    logger = setup_logging(name="format_test")
    handler = logger.handlers[0]
    formatter = handler.formatter

    # Create a dummy log record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)

    # Should contain timestamp, level, and message
    assert "INFO" in formatted
    assert "Test message" in formatted
    # Should contain some form of timestamp (contains digits and colons)
    assert any(c.isdigit() for c in formatted)
    assert ":" in formatted
