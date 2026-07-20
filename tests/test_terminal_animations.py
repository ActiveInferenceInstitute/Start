from __future__ import annotations

from src.terminal.animations import LoadingSpinner, MatrixRain, glitch_effect, typewriter_effect


def test_zero_delay_typewriter_is_deterministic(monkeypatch) -> None:
    monkeypatch.setenv("TERM", "dumb")
    frames = list(typewriter_effect("Hello", delay=0))
    assert frames == ["", "H", "He", "Hel", "Hell", "Hello"]


def test_zero_duration_animations_complete() -> None:
    assert list(MatrixRain(duration=0).animate())
    assert list(glitch_effect("hello", intensity=1, duration=0))[-1] == "hello"


def test_spinner_advances() -> None:
    spinner = LoadingSpinner("Loading", "dots")
    first = spinner.next_frame()
    second = spinner.next_frame()
    assert first != second
