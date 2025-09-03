"""Terminal color utilities and ANSI escape sequences.

This module provides comprehensive color support for terminal applications,
including Matrix-style green effects and various styling options.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Optional


class Color(Enum):
    """ANSI color codes for terminal output."""
    
    # Basic colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Special colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    STRIKETHROUGH = "\033[9m"


class MatrixColors:
    """Matrix-style color scheme constants."""
    
    MATRIX_GREEN = "\033[38;2;0;255;65m"  # Bright Matrix green
    DARK_GREEN = "\033[38;2;0;100;0m"     # Dark green
    LIGHT_GREEN = "\033[38;2;100;255;100m" # Light green
    CYBER_BLUE = "\033[38;2;0;255;255m"   # Cyber blue
    WARNING_RED = "\033[38;2;255;50;50m"   # Warning red
    GOLD = "\033[38;2;255;215;0m"         # Gold
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_DARK_GREEN = "\033[48;2;0;20;0m"


def is_color_supported() -> bool:
    """Check if the terminal supports color output.
    
    Returns:
        True if colors are supported, False otherwise
    """
    return (
        os.getenv("TERM") != "dumb" and
        hasattr(os.sys.stdout, "isatty") and
        os.sys.stdout.isatty()
    )


def colorize(text: str, color: Color | str, reset: bool = True) -> str:
    """Apply color to text if color is supported.
    
    Args:
        text: Text to colorize
        color: Color enum value or ANSI color string
        reset: Whether to add reset sequence at the end
        
    Returns:
        Colorized text string, or plain text if colors not supported
    """
    if not is_color_supported():
        return text
    
    color_code = color.value if isinstance(color, Color) else color
    reset_code = Color.RESET.value if reset else ""
    
    return f"{color_code}{text}{reset_code}"


def matrix_text(text: str, style: str = "normal") -> str:
    """Apply Matrix-style coloring to text.
    
    Args:
        text: Text to style
        style: Style type - 'normal', 'bright', 'dim', 'warning'
        
    Returns:
        Matrix-styled text
    """
    if not is_color_supported():
        return text
    
    styles = {
        "normal": MatrixColors.MATRIX_GREEN,
        "bright": MatrixColors.LIGHT_GREEN,
        "dim": MatrixColors.DARK_GREEN,
        "warning": MatrixColors.WARNING_RED,
        "gold": MatrixColors.GOLD,
        "cyber": MatrixColors.CYBER_BLUE,
    }
    
    color_code = styles.get(style, MatrixColors.MATRIX_GREEN)
    return f"{color_code}{text}{Color.RESET.value}"


def gradient_text(text: str, start_color: str, end_color: str) -> str:
    """Create a gradient effect across text characters.
    
    Args:
        text: Text to apply gradient to
        start_color: Starting ANSI color code
        end_color: Ending ANSI color code
        
    Returns:
        Text with gradient effect
    """
    if not is_color_supported():
        return text
    if len(text) <= 1:
        return colorize(text, start_color)
    
    # Simple gradient by alternating colors for now
    # In a more sophisticated version, we'd interpolate RGB values
    result = ""
    for i, char in enumerate(text):
        if i % 2 == 0:
            result += colorize(char, start_color, reset=False)
        else:
            result += colorize(char, end_color, reset=False)
    
    return result + Color.RESET.value


def rainbow_text(text: str) -> str:
    """Apply rainbow colors to text.
    
    Args:
        text: Text to colorize
        
    Returns:
        Rainbow-colored text
    """
    if not is_color_supported():
        return text
    
    colors = [
        Color.RED,
        Color.YELLOW,
        Color.GREEN,
        Color.CYAN,
        Color.BLUE,
        Color.MAGENTA,
    ]
    
    result = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        result += colorize(char, color, reset=False)
    
    return result + Color.RESET.value


def clear_screen() -> str:
    """Return ANSI sequence to clear screen.
    
    Returns:
        Clear screen ANSI sequence
    """
    return "\033[2J\033[H"


def hide_cursor() -> str:
    """Return ANSI sequence to hide cursor.
    
    Returns:
        Hide cursor ANSI sequence
    """
    return "\033[?25l"


def show_cursor() -> str:
    """Return ANSI sequence to show cursor.
    
    Returns:
        Show cursor ANSI sequence
    """
    return "\033[?25h"


def move_cursor(row: int, col: int) -> str:
    """Return ANSI sequence to move cursor to position.
    
    Args:
        row: Row position (1-based)
        col: Column position (1-based)
        
    Returns:
        Move cursor ANSI sequence
    """
    return f"\033[{row};{col}H"


def get_terminal_size() -> tuple[int, int]:
    """Get terminal size in rows and columns.
    
    Returns:
        Tuple of (rows, columns)
    """
    try:
        import shutil
        columns, rows = shutil.get_terminal_size()
        return rows, columns
    except Exception:
        return 24, 80  # Fallback to standard terminal size
