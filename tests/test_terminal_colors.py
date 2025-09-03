"""Tests for terminal colors module."""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

from src.terminal.colors import (
    Color,
    MatrixColors,
    clear_screen,
    colorize,
    get_terminal_size,
    gradient_text,
    hide_cursor,
    is_color_supported,
    matrix_text,
    move_cursor,
    rainbow_text,
    show_cursor,
)


class TestColor:
    """Test Color enum."""
    
    def test_basic_colors(self):
        """Test basic color codes."""
        assert Color.RED.value == "\033[31m"
        assert Color.GREEN.value == "\033[32m"
        assert Color.BLUE.value == "\033[34m"
        assert Color.RESET.value == "\033[0m"
    
    def test_bright_colors(self):
        """Test bright color codes."""
        assert Color.BRIGHT_RED.value == "\033[91m"
        assert Color.BRIGHT_GREEN.value == "\033[92m"
        assert Color.BRIGHT_BLUE.value == "\033[94m"
    
    def test_special_formatting(self):
        """Test special formatting codes."""
        assert Color.BOLD.value == "\033[1m"
        assert Color.DIM.value == "\033[2m"
        assert Color.UNDERLINE.value == "\033[4m"


class TestMatrixColors:
    """Test Matrix color constants."""
    
    def test_matrix_colors(self):
        """Test Matrix-specific color constants."""
        assert MatrixColors.MATRIX_GREEN == "\033[38;2;0;255;65m"
        assert MatrixColors.CYBER_BLUE == "\033[38;2;0;255;255m"
        assert MatrixColors.GOLD == "\033[38;2;255;215;0m"


class TestColorSupport:
    """Test color support detection."""
    
    def test_color_supported_with_tty(self):
        """Test color support with TTY."""
        with patch.dict(os.environ, {"TERM": "xterm-256color"}):
            with patch("os.sys.stdout.isatty", return_value=True):
                assert is_color_supported() is True
    
    def test_color_not_supported_dumb_terminal(self):
        """Test color not supported with dumb terminal."""
        with patch.dict(os.environ, {"TERM": "dumb"}):
            assert is_color_supported() is False
    
    def test_color_not_supported_no_tty(self):
        """Test color not supported without TTY."""
        with patch("os.sys.stdout.isatty", return_value=False):
            assert is_color_supported() is False
    
    def test_color_not_supported_no_isatty(self):
        """Test color support when isatty is not available."""
        with patch("os.sys.stdout", spec=[]):  # Remove isatty method
            assert is_color_supported() is False


class TestColorize:
    """Test colorize function."""
    
    def test_colorize_with_color_enum(self):
        """Test colorizing text with Color enum."""
        result = colorize("test", Color.RED)
        expected = f"{Color.RED.value}test{Color.RESET.value}"
        
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = colorize("test", Color.RED)
            assert result == expected
    
    def test_colorize_with_string_color(self):
        """Test colorizing text with string color code."""
        color_code = "\033[31m"
        
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = colorize("test", color_code)
            expected = f"{color_code}test{Color.RESET.value}"
            assert result == expected
    
    def test_colorize_no_reset(self):
        """Test colorizing text without reset."""
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = colorize("test", Color.RED, reset=False)
            expected = f"{Color.RED.value}test"
            assert result == expected
    
    def test_colorize_no_color_support(self):
        """Test colorizing when colors not supported."""
        with patch("src.terminal.colors.is_color_supported", return_value=False):
            result = colorize("test", Color.RED)
            assert result == "test"


class TestMatrixText:
    """Test matrix_text function."""
    
    def test_matrix_text_normal_style(self):
        """Test matrix text with normal style."""
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = matrix_text("test", "normal")
            expected = f"{MatrixColors.MATRIX_GREEN}test{Color.RESET.value}"
            assert result == expected
    
    def test_matrix_text_bright_style(self):
        """Test matrix text with bright style."""
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = matrix_text("test", "bright")
            expected = f"{MatrixColors.LIGHT_GREEN}test{Color.RESET.value}"
            assert result == expected
    
    def test_matrix_text_warning_style(self):
        """Test matrix text with warning style."""
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = matrix_text("test", "warning")
            expected = f"{MatrixColors.WARNING_RED}test{Color.RESET.value}"
            assert result == expected
    
    def test_matrix_text_unknown_style(self):
        """Test matrix text with unknown style falls back to normal."""
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = matrix_text("test", "unknown")
            expected = f"{MatrixColors.MATRIX_GREEN}test{Color.RESET.value}"
            assert result == expected
    
    def test_matrix_text_no_color_support(self):
        """Test matrix text when colors not supported."""
        with patch("src.terminal.colors.is_color_supported", return_value=False):
            result = matrix_text("test", "bright")
            assert result == "test"


class TestGradientText:
    """Test gradient_text function."""
    
    def test_gradient_text_with_colors(self):
        """Test gradient text effect."""
        start_color = "\033[31m"  # Red
        end_color = "\033[32m"    # Green
        
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = gradient_text("test", start_color, end_color)
            # Should alternate colors and end with reset
            assert start_color in result
            assert end_color in result
            assert result.endswith(Color.RESET.value)
    
    def test_gradient_text_single_char(self):
        """Test gradient text with single character."""
        start_color = "\033[31m"
        end_color = "\033[32m"
        
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = gradient_text("a", start_color, end_color)
            expected = f"{start_color}a{Color.RESET.value}"
            assert result == expected
    
    def test_gradient_text_no_color_support(self):
        """Test gradient text when colors not supported."""
        start_color = "\033[31m"
        end_color = "\033[32m"
        
        with patch("src.terminal.colors.is_color_supported", return_value=False):
            result = gradient_text("test", start_color, end_color)
            assert result == "test"


class TestRainbowText:
    """Test rainbow_text function."""
    
    def test_rainbow_text_with_colors(self):
        """Test rainbow text effect."""
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            result = rainbow_text("test")
            # Should contain different color codes and end with reset
            assert "\033[31m" in result  # Red
            assert "\033[33m" in result  # Yellow
            assert result.endswith(Color.RESET.value)
    
    def test_rainbow_text_no_color_support(self):
        """Test rainbow text when colors not supported."""
        with patch("src.terminal.colors.is_color_supported", return_value=False):
            result = rainbow_text("test")
            assert result == "test"


class TestTerminalControl:
    """Test terminal control functions."""
    
    def test_clear_screen(self):
        """Test clear screen ANSI sequence."""
        result = clear_screen()
        assert result == "\033[2J\033[H"
    
    def test_hide_cursor(self):
        """Test hide cursor ANSI sequence."""
        result = hide_cursor()
        assert result == "\033[?25l"
    
    def test_show_cursor(self):
        """Test show cursor ANSI sequence."""
        result = show_cursor()
        assert result == "\033[?25h"
    
    def test_move_cursor(self):
        """Test move cursor ANSI sequence."""
        result = move_cursor(5, 10)
        assert result == "\033[5;10H"


class TestTerminalSize:
    """Test terminal size detection."""
    
    def test_get_terminal_size_success(self):
        """Test getting terminal size successfully."""
        with patch("shutil.get_terminal_size", return_value=(80, 24)):
            rows, cols = get_terminal_size()
            assert rows == 24
            assert cols == 80
    
    def test_get_terminal_size_fallback(self):
        """Test terminal size fallback on error."""
        with patch("shutil.get_terminal_size", side_effect=Exception("Error")):
            rows, cols = get_terminal_size()
            assert rows == 24  # Fallback values
            assert cols == 80


@pytest.mark.integration
class TestColorIntegration:
    """Integration tests for color functionality."""
    
    def test_color_chain(self):
        """Test chaining multiple color operations."""
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            text = "Hello World"
            
            # Apply multiple color effects
            colored = colorize(text, Color.BOLD, reset=False)
            colored = colorize(colored, Color.RED, reset=True)
            
            assert Color.BOLD.value in colored
            assert Color.RED.value in colored
            assert colored.endswith(Color.RESET.value)
    
    def test_matrix_styles_complete(self):
        """Test all Matrix styles work."""
        styles = ["normal", "bright", "dim", "warning", "gold", "cyber"]
        
        with patch("src.terminal.colors.is_color_supported", return_value=True):
            for style in styles:
                result = matrix_text("test", style)
                assert result != "test"  # Should be modified
                assert result.endswith(Color.RESET.value)
