"""Matrix-style terminal animations and effects.

This module provides various terminal animation effects including:
- Digital rain (Matrix-style falling characters)
- Typewriter effects
- Glitch effects
- Loading animations
"""

from __future__ import annotations

import random
import string
import sys
import time
from typing import Generator, List, Optional

from .colors import (
    MatrixColors,
    clear_screen,
    get_terminal_size,
    hide_cursor,
    matrix_text,
    move_cursor,
    show_cursor,
)


class MatrixRain:
    """Matrix-style digital rain animation."""
    
    def __init__(self, duration: float = 3.0, density: float = 0.1):
        """Initialize Matrix rain animation.
        
        Args:
            duration: Animation duration in seconds
            density: Character density (0.0 to 1.0)
        """
        self.duration = duration
        self.density = density
        self.rows, self.cols = get_terminal_size()
        self.columns: List[List[dict]] = [[] for _ in range(self.cols)]
        
        # Matrix characters (mix of ASCII, numbers, and some special chars)
        self.chars = (
            string.ascii_letters + 
            string.digits + 
            "!@#$%^&*()_+-=[]{}|;:,.<>?~`"
        )
    
    def _create_drop(self, col: int) -> dict:
        """Create a new falling character drop.
        
        Args:
            col: Column position
            
        Returns:
            Dictionary representing a character drop
        """
        return {
            "char": random.choice(self.chars),
            "row": 0,
            "age": 0,
            "max_age": random.randint(5, 15),
        }
    
    def _update_drops(self) -> None:
        """Update all falling character drops."""
        for col in range(self.cols):
            # Maybe spawn new drop
            if random.random() < self.density and len(self.columns[col]) < 3:
                self.columns[col].append(self._create_drop(col))
            
            # Update existing drops
            for drop in self.columns[col][:]:
                drop["row"] += 1
                drop["age"] += 1
                
                # Remove drops that are too old or off screen
                if drop["row"] >= self.rows or drop["age"] >= drop["max_age"]:
                    self.columns[col].remove(drop)
    
    def _render_frame(self) -> str:
        """Render a single animation frame.
        
        Returns:
            ANSI-formatted frame string
        """
        frame = clear_screen() + hide_cursor()
        
        for col in range(self.cols):
            for drop in self.columns[col]:
                if 0 <= drop["row"] < self.rows:
                    # Determine color based on age
                    if drop["age"] < 2:
                        color_style = "bright"
                    elif drop["age"] < 5:
                        color_style = "normal" 
                    else:
                        color_style = "dim"
                    
                    frame += move_cursor(drop["row"] + 1, col + 1)
                    frame += matrix_text(drop["char"], color_style)
        
        return frame
    
    def animate(self) -> Generator[str, None, None]:
        """Generate animation frames.
        
        Yields:
            ANSI-formatted frame strings
        """
        start_time = time.time()
        
        while time.time() - start_time < self.duration:
            self._update_drops()
            yield self._render_frame()
            time.sleep(0.1)
        
        # Final frame to clean up
        yield clear_screen() + show_cursor()


def typewriter_effect(text: str, delay: float = 0.05, color_style: str = "normal") -> Generator[str, None, None]:
    """Create a typewriter effect for text display.
    
    Args:
        text: Text to display with typewriter effect
        delay: Delay between characters in seconds
        color_style: Matrix color style to use
        
    Yields:
        Progressive text strings
    """
    for i in range(len(text) + 1):
        partial_text = text[:i]
        yield matrix_text(partial_text, color_style)
        time.sleep(delay)


def glitch_effect(text: str, intensity: int = 3, duration: float = 1.0) -> Generator[str, None, None]:
    """Create a glitch effect for text.
    
    Args:
        text: Original text
        intensity: Glitch intensity (number of variations)
        duration: Effect duration in seconds
        
    Yields:
        Glitched text strings
    """
    glitch_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?~`"
    
    start_time = time.time()
    original_chars = list(text)
    
    while time.time() - start_time < duration:
        # Create glitched version
        glitched = original_chars.copy()
        
        # Randomly replace some characters
        for _ in range(random.randint(1, intensity)):
            if glitched:
                pos = random.randint(0, len(glitched) - 1)
                glitched[pos] = random.choice(glitch_chars)
        
        yield matrix_text("".join(glitched), "warning")
        time.sleep(0.1)
    
    # Return to original
    yield matrix_text(text, "normal")


class LoadingSpinner:
    """ASCII loading spinner animation."""
    
    def __init__(self, message: str = "Loading", style: str = "dots"):
        """Initialize loading spinner.
        
        Args:
            message: Loading message to display
            style: Spinner style - 'dots', 'lines', 'arrows'
        """
        self.message = message
        
        styles = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "lines": ["-", "\\", "|", "/"],
            "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            "matrix": ["▓", "▒", "░", "▒", "▓"],
        }
        
        self.frames = styles.get(style, styles["dots"])
        self.current_frame = 0
    
    def next_frame(self) -> str:
        """Get next spinner frame.
        
        Returns:
            Formatted spinner frame
        """
        frame = self.frames[self.current_frame % len(self.frames)]
        self.current_frame += 1
        
        spinner_text = f"{frame} {self.message}"
        return matrix_text(spinner_text, "normal")
    
    def animate(self, duration: float) -> Generator[str, None, None]:
        """Animate spinner for given duration.
        
        Args:
            duration: Animation duration in seconds
            
        Yields:
            Spinner frames
        """
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Clear line and show spinner
            yield f"\r{self.next_frame()}"
            time.sleep(0.1)
        
        # Clear the spinner line
        yield f"\r{' ' * (len(self.message) + 10)}\r"


def matrix_banner(text: str, width: Optional[int] = None) -> str:
    """Create a Matrix-style banner with text.
    
    Args:
        text: Banner text
        width: Banner width (defaults to terminal width)
        
    Returns:
        Formatted banner string
    """
    if width is None:
        _, width = get_terminal_size()
        width = min(width, 80)  # Cap at 80 for readability
    
    # Create border
    border_char = "═"
    corner_char = "╬"
    
    # Build banner lines
    lines = []
    
    # Top border
    top_border = corner_char + border_char * (width - 2) + corner_char
    lines.append(matrix_text(top_border, "bright"))
    
    # Text lines (split if too long)
    words = text.split()
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= width - 6:  # Account for padding
            current_line += (" " if current_line else "") + word
        else:
            if current_line:
                padded = f"║  {current_line:<{width-6}}  ║"
                lines.append(matrix_text(padded, "gold"))
            current_line = word
    
    # Add final line if exists
    if current_line:
        padded = f"║  {current_line:<{width-6}}  ║"
        lines.append(matrix_text(padded, "gold"))
    
    # Add empty line for spacing
    empty_line = f"║{' ' * (width-2)}║"
    lines.append(matrix_text(empty_line, "bright"))
    
    # Bottom border
    bottom_border = corner_char + border_char * (width - 2) + corner_char
    lines.append(matrix_text(bottom_border, "bright"))
    
    return "\n".join(lines)


def boot_sequence(steps: List[str], delay: float = 0.5) -> Generator[str, None, None]:
    """Simulate a system boot sequence animation.
    
    Args:
        steps: List of boot step messages
        delay: Delay between steps
        
    Yields:
        Boot sequence frames
    """
    yield clear_screen()
    yield matrix_text("INITIALIZING ACTIVE INFERENCE MATRIX...", "cyber")
    time.sleep(delay)
    
    for i, step in enumerate(steps):
        # Show loading spinner for each step
        spinner = LoadingSpinner(step, "matrix")
        
        # Animate spinner for a bit
        for frame in spinner.animate(random.uniform(0.5, 2.0)):
            yield f"\n{frame}"
        
        # Show completion
        status = matrix_text(f"✓ {step}", "bright")
        yield f"\n{status}"
        
        time.sleep(delay * 0.3)
    
    yield matrix_text("\nSYSTEM READY", "gold")


def dramatic_pause(message: str = "...", duration: float = 2.0) -> Generator[str, None, None]:
    """Create a dramatic pause with animated dots.
    
    Args:
        message: Base message
        duration: Pause duration
        
    Yields:
        Animated pause frames
    """
    start_time = time.time()
    dots = ""
    
    while time.time() - start_time < duration:
        dots += "."
        if len(dots) > 3:
            dots = "."
        
        yield f"\r{matrix_text(message + dots, 'dim')}"
        time.sleep(0.5)
    
    yield f"\r{matrix_text(message, 'normal')}"


def print_animated(text: str, animation_type: str = "typewriter", **kwargs) -> None:
    """Print text with animation effect.
    
    Args:
        text: Text to animate
        animation_type: Type of animation ('typewriter', 'glitch', 'matrix')
        **kwargs: Additional arguments for animation functions
    """
    if animation_type == "typewriter":
        for frame in typewriter_effect(text, **kwargs):
            print(f"\r{frame}", end="", flush=True)
    elif animation_type == "glitch":
        for frame in glitch_effect(text, **kwargs):
            print(f"\r{frame}", end="", flush=True)
        time.sleep(0.1)
    elif animation_type == "matrix":
        rain = MatrixRain(**kwargs)
        for frame in rain.animate():
            print(frame, end="", flush=True)
    
    print()  # Final newline
