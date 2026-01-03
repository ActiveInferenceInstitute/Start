# Terminal UI Utilities

Terminal UI utilities for interactive menus, animations, and styling.

## Overview

This module provides Matrix-style terminal UI components including interactive menus, animations, color utilities, and dialog functions.

## Modules

### `menu.py`
Interactive menu system:
- `Menu`: Main menu class with keyboard navigation
- `MenuItem`: Menu item dataclass
- `MenuTheme`: Visual theme configuration
- `MenuBuilder`: Builder pattern for menu construction
- `confirmation_dialog()`: Confirmation dialog function
- `input_dialog()`: Input dialog function

### `colors.py`
Terminal color and styling utilities:
- `Color`: ANSI color codes enum
- `MatrixColors`: Matrix-style color scheme constants
- `colorize()`: Colorize text
- `matrix_text()`: Apply Matrix-style text formatting
- `gradient_text()`: Create gradient text effects
- `clear_screen()`: Clear terminal screen
- `hide_cursor()` / `show_cursor()`: Cursor visibility control
- `move_cursor()`: Move cursor position
- `get_terminal_size()`: Get terminal dimensions

### `animations.py`
Matrix-style animations and effects:
- `MatrixRain`: Matrix-style digital rain animation
- `typewriter_effect()`: Typewriter text animation
- `glitch_effect()`: Glitch text effect
- `LoadingSpinner`: Loading spinner animation
- `matrix_banner()`: Create Matrix-style banner
- `boot_sequence()`: Boot sequence animation generator
- `print_animated()`: Print text with animation

## Usage Examples

```python
from src.terminal.menu import MenuBuilder
from src.terminal.colors import matrix_text, colorize, Color
from src.terminal.animations import matrix_banner, print_animated

# Create menu
menu = (MenuBuilder("Main Menu")
    .add_item("Option 1", lambda: print("Selected 1"))
    .add_item("Option 2", lambda: print("Selected 2"))
    .build())

menu.show()

# Use colors
print(matrix_text("Hello Matrix", "bright"))
print(colorize("Colored text", Color.GREEN))

# Use animations
print_animated("Loading...", "typewriter")
print(matrix_banner("TITLE"))
```

## Navigation

- [AGENTS.md](AGENTS.md) - Complete function reference
- [../README.md](../README.md) - Source code overview
