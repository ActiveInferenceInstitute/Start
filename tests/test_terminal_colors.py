from __future__ import annotations

from src.terminal.colors import Color, MatrixColors, colorize, is_color_supported, matrix_text


def test_color_constants_and_plain_terminal(monkeypatch) -> None:
    assert Color.RED.value == "\033[31m"
    assert MatrixColors.MATRIX_GREEN.startswith("\033[")
    monkeypatch.setenv("TERM", "dumb")
    assert is_color_supported() is False
    assert colorize("text", Color.RED) == "text"
    assert matrix_text("text") == "text"


def test_colorize_without_reset_on_supported_terminal(monkeypatch) -> None:
    monkeypatch.setenv("TERM", "dumb")
    assert colorize("text", Color.RED, reset=False) == "text"
