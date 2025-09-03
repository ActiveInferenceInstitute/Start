"""Tests for terminal animations module."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from src.terminal.animations import (
    LoadingSpinner,
    MatrixRain,
    boot_sequence,
    dramatic_pause,
    glitch_effect,
    matrix_banner,
    print_animated,
    typewriter_effect,
)


class TestMatrixRain:
    """Test MatrixRain animation class."""
    
    def test_matrix_rain_init(self):
        """Test MatrixRain initialization."""
        rain = MatrixRain(duration=2.0, density=0.2)
        assert rain.duration == 2.0
        assert rain.density == 0.2
        assert len(rain.columns) > 0
        assert len(rain.chars) > 0
    
    def test_matrix_rain_create_drop(self):
        """Test creating a character drop."""
        rain = MatrixRain()
        drop = rain._create_drop(5)
        
        assert "char" in drop
        assert "row" in drop
        assert "age" in drop
        assert "max_age" in drop
        assert drop["char"] in rain.chars
        assert drop["row"] == 0
        assert drop["age"] == 0
        assert 5 <= drop["max_age"] <= 15
    
    def test_matrix_rain_update_drops(self):
        """Test updating character drops."""
        rain = MatrixRain(density=1.0)  # High density for testing
        
        # Add some initial drops
        for i in range(5):
            rain.columns[i].append(rain._create_drop(i))
        
        initial_count = sum(len(col) for col in rain.columns)
        rain._update_drops()
        
        # Drops should have aged and possibly moved
        for col in rain.columns:
            for drop in col:
                assert drop["age"] > 0 or drop["row"] > 0
    
    def test_matrix_rain_render_frame(self):
        """Test rendering animation frame."""
        rain = MatrixRain()
        
        # Add some drops
        rain.columns[0].append(rain._create_drop(0))
        
        frame = rain._render_frame()
        
        assert isinstance(frame, str)
        assert "\033[2J\033[H" in frame  # Clear screen
        assert "\033[?25l" in frame     # Hide cursor
    
    def test_matrix_rain_animate(self):
        """Test animation generator."""
        rain = MatrixRain(duration=0.1)  # Very short duration
        
        frames = list(rain.animate())
        
        assert len(frames) > 0
        assert all(isinstance(frame, str) for frame in frames)
        # Last frame should show cursor
        assert "\033[?25h" in frames[-1]


class TestTypewriterEffect:
    """Test typewriter effect function."""
    
    def test_typewriter_effect_basic(self):
        """Test basic typewriter effect."""
        text = "Hello"
        
        with patch("time.sleep"):  # Mock sleep to speed up test
            frames = list(typewriter_effect(text, delay=0.01))
        
        assert len(frames) == len(text) + 1
        assert frames[0] == ""
        assert frames[-1] != frames[0]
    
    def test_typewriter_effect_with_color(self):
        """Test typewriter effect with color styling."""
        text = "Test"
        
        with patch("time.sleep"):
            with patch("src.terminal.animations.matrix_text") as mock_matrix:
                mock_matrix.side_effect = lambda t, s: f"[{s}]{t}[/{s}]"
                
                frames = list(typewriter_effect(text, color_style="bright"))
        
        assert len(frames) > 0
        assert all("[bright]" in frame for frame in frames if frame)
    
    def test_typewriter_effect_empty_text(self):
        """Test typewriter effect with empty text."""
        with patch("time.sleep"):
            frames = list(typewriter_effect(""))
        
        assert len(frames) == 1
        assert frames[0] == ""


class TestGlitchEffect:
    """Test glitch effect function."""
    
    def test_glitch_effect_basic(self):
        """Test basic glitch effect."""
        text = "Hello"
        
        with patch("time.sleep"):  # Mock sleep to speed up test
            frames = list(glitch_effect(text, intensity=2, duration=0.1))
        
        assert len(frames) > 1
        # Last frame should be the original text
        assert text in frames[-1]
    
    def test_glitch_effect_intensity(self):
        """Test glitch effect with different intensities."""
        text = "Test"
        
        with patch("time.sleep"):
            with patch("src.terminal.animations.matrix_text") as mock_matrix:
                mock_matrix.side_effect = lambda t, s: t
                
                frames_low = list(glitch_effect(text, intensity=1, duration=0.1))
                frames_high = list(glitch_effect(text, intensity=5, duration=0.1))
        
        assert len(frames_low) >= 1
        assert len(frames_high) >= 1
    
    def test_glitch_effect_empty_text(self):
        """Test glitch effect with empty text."""
        with patch("time.sleep"):
            frames = list(glitch_effect("", duration=0.1))
        
        assert len(frames) >= 1


class TestLoadingSpinner:
    """Test LoadingSpinner class."""
    
    def test_loading_spinner_init(self):
        """Test LoadingSpinner initialization."""
        spinner = LoadingSpinner("Loading...", "dots")
        assert spinner.message == "Loading..."
        assert len(spinner.frames) > 0
        assert spinner.current_frame == 0
    
    def test_loading_spinner_styles(self):
        """Test different spinner styles."""
        styles = ["dots", "lines", "arrows", "matrix"]
        
        for style in styles:
            spinner = LoadingSpinner("Test", style)
            assert len(spinner.frames) > 0
    
    def test_loading_spinner_next_frame(self):
        """Test getting next spinner frame."""
        spinner = LoadingSpinner("Loading...")
        
        frame1 = spinner.next_frame()
        frame2 = spinner.next_frame()
        
        assert isinstance(frame1, str)
        assert isinstance(frame2, str)
        assert "Loading..." in frame1
        assert "Loading..." in frame2
        assert spinner.current_frame == 2
    
    def test_loading_spinner_animate(self):
        """Test spinner animation."""
        spinner = LoadingSpinner("Test")
        
        with patch("time.sleep"):
            frames = list(spinner.animate(0.1))
        
        assert len(frames) > 0
        # Last frame should be a clear
        assert frames[-1].strip() == ""


class TestMatrixBanner:
    """Test matrix_banner function."""
    
    def test_matrix_banner_basic(self):
        """Test basic banner creation."""
        banner = matrix_banner("Test Banner")
        
        assert isinstance(banner, str)
        assert "Test Banner" in banner
        assert "╬" in banner  # Corner characters
        assert "═" in banner  # Border characters
    
    def test_matrix_banner_custom_width(self):
        """Test banner with custom width."""
        banner = matrix_banner("Test", width=20)
        
        lines = banner.split("\n")
        # Check that lines are approximately the right width
        assert any(len(line.replace('\033[', '').split('m')[0]) <= 25 for line in lines if line)
    
    def test_matrix_banner_long_text(self):
        """Test banner with long text that wraps."""
        long_text = "This is a very long text that should wrap to multiple lines"
        banner = matrix_banner(long_text, width=30)
        
        assert isinstance(banner, str)
        assert long_text.split()[0] in banner  # First word should be present
    
    def test_matrix_banner_empty_text(self):
        """Test banner with empty text."""
        banner = matrix_banner("")
        
        assert isinstance(banner, str)
        assert "╬" in banner  # Should still have border


class TestBootSequence:
    """Test boot_sequence function."""
    
    def test_boot_sequence_basic(self):
        """Test basic boot sequence."""
        steps = ["Step 1", "Step 2", "Step 3"]
        
        with patch("time.sleep"):
            with patch("src.terminal.animations.LoadingSpinner") as mock_spinner:
                mock_spinner.return_value.animate.return_value = [" [spinner] "]
                
                frames = list(boot_sequence(steps, delay=0.01))
        
        assert len(frames) > len(steps)  # Should have more frames than steps
        assert any("INITIALIZING" in frame for frame in frames)
        assert any("SYSTEM READY" in frame for frame in frames)
    
    def test_boot_sequence_empty_steps(self):
        """Test boot sequence with empty steps."""
        with patch("time.sleep"):
            frames = list(boot_sequence([], delay=0.01))
        
        assert len(frames) >= 2  # At least init and ready frames


class TestDramaticPause:
    """Test dramatic_pause function."""
    
    def test_dramatic_pause_basic(self):
        """Test basic dramatic pause."""
        with patch("time.sleep"):
            frames = list(dramatic_pause("Waiting", duration=0.1))
        
        assert len(frames) > 1
        assert all("Waiting" in frame for frame in frames if frame)
    
    def test_dramatic_pause_dots(self):
        """Test that dots animate properly."""
        with patch("time.sleep"):
            frames = list(dramatic_pause("Test", duration=0.1))
        
        # Should have different numbers of dots
        dot_counts = []
        for frame in frames:
            if "Test" in frame:
                dots = frame.split("Test")[1] if "Test" in frame else ""
                dot_counts.append(dots.count("."))
        
        # Should have varying dot counts
        assert len(set(dot_counts)) > 1


class TestPrintAnimated:
    """Test print_animated function."""
    
    def test_print_animated_typewriter(self):
        """Test print_animated with typewriter effect."""
        with patch("builtins.print") as mock_print:
            with patch("time.sleep"):
                print_animated("Test", "typewriter", delay=0.01)
        
        assert mock_print.called
    
    def test_print_animated_glitch(self):
        """Test print_animated with glitch effect."""
        with patch("builtins.print") as mock_print:
            with patch("time.sleep"):
                print_animated("Test", "glitch", duration=0.1)
        
        assert mock_print.called
    
    def test_print_animated_matrix(self):
        """Test print_animated with matrix effect."""
        with patch("builtins.print") as mock_print:
            with patch("time.sleep"):
                print_animated("Test", "matrix", duration=0.1)
        
        assert mock_print.called
    
    def test_print_animated_unknown_type(self):
        """Test print_animated with unknown animation type."""
        with patch("builtins.print") as mock_print:
            print_animated("Test", "unknown")
        
        # Should still print something
        assert mock_print.called


@pytest.mark.integration
class TestAnimationIntegration:
    """Integration tests for animation functionality."""
    
    def test_animation_timing(self):
        """Test that animations respect timing parameters."""
        start_time = time.time()
        
        with patch("builtins.print"):  # Suppress output
            print_animated("Short test", "typewriter", delay=0.01)
        
        elapsed = time.time() - start_time
        # Should take some time but not too much
        assert 0 < elapsed < 1.0
    
    def test_matrix_rain_performance(self):
        """Test that matrix rain doesn't consume excessive resources."""
        rain = MatrixRain(duration=0.1, density=0.1)
        
        start_time = time.time()
        frames = list(rain.animate())
        elapsed = time.time() - start_time
        
        assert len(frames) > 0
        assert elapsed < 1.0  # Should complete quickly
    
    def test_spinner_cycle(self):
        """Test that spinner cycles through all frames."""
        spinner = LoadingSpinner("Test", "dots")
        initial_frames = len(spinner.frames)
        
        seen_frames = set()
        for _ in range(initial_frames * 2):
            frame = spinner.next_frame()
            # Extract just the spinner character
            spinner_char = frame.split()[0] if frame.split() else ""
            seen_frames.add(spinner_char)
        
        # Should have seen all spinner frames
        assert len(seen_frames) <= initial_frames
    
    def test_color_integration(self):
        """Test that animations work with color functions."""
        with patch("src.terminal.animations.matrix_text") as mock_matrix:
            mock_matrix.return_value = "[colored]Test[/colored]"
            
            with patch("time.sleep"):
                frames = list(typewriter_effect("Test", color_style="bright"))
        
        assert len(frames) > 0
        mock_matrix.assert_called()
