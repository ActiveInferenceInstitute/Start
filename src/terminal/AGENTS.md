# Terminal UI Utilities Technical Reference

## Overview

Technical documentation for terminal UI utilities, menus, animations, and styling.

## Module: `menu.py`

### Classes

#### `MenuItem`
Represents a menu item with action and styling.

**Attributes**:
- `label: str`: Menu item label
- `action: Optional[Callable[[], Any]]`: Action function
- `submenu: Optional[Menu]`: Nested submenu
- `description: str`: Item description
- `enabled: bool`: Whether item is enabled (default: True)
- `style: str`: Visual style (normal, bright, dim, warning, gold, cyber)

#### `MenuTheme`
Visual theme configuration for menus.

**Attributes**:
- `title_style: str`: Title styling
- `item_style: str`: Item styling
- `selected_style: str`: Selected item styling
- `border_style: str`: Border styling
- `description_style: str`: Description styling

#### `Menu`
Interactive terminal menu with Matrix styling.

**Methods**:
- `show()`: Display and handle menu interaction
- `_render_header()`: Render menu header
- `_render_items()`: Render menu items
- `_move_to_next_enabled(direction: int)`: Move to next enabled item

#### `MenuBuilder`
Builder pattern for menu construction.

**Methods**:
- `add_item(label, action, description, enabled, style)`: Add menu item
- `add_separator()`: Add separator
- `build()`: Build Menu instance

### Functions

#### `confirmation_dialog(message: str, default_yes: bool = False) -> bool`
Shows confirmation dialog.

**Parameters**:
- `message`: Confirmation message
- `default_yes`: Default to yes (default: False)

**Returns**: True if confirmed, False otherwise

#### `input_dialog(prompt: str, default: Optional[str] = None) -> str`
Shows input dialog.

**Parameters**:
- `prompt`: Input prompt
- `default`: Default value

**Returns**: User input string

## Module: `colors.py`

### Classes

#### `Color`
ANSI color codes enum.

**Values**: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BRIGHT_*, RESET, BOLD, DIM, ITALIC, UNDERLINE, BLINK, REVERSE, STRIKETHROUGH

#### `MatrixColors`
Matrix-style color scheme constants.

### Functions

#### `colorize(text: str, color: Color | str, reset: bool = True) -> str`
Colorizes text with ANSI codes.

**Parameters**:
- `text`: Text to colorize
- `color`: Color enum or string
- `reset`: Whether to reset color after text (default: True)

**Returns**: Colorized text string

#### `matrix_text(text: str, style: str = "normal") -> str`
Applies Matrix-style text formatting.

**Parameters**:
- `text`: Text to format
- `style`: Style name (normal, bright, dim, warning, gold, cyber)

**Returns**: Formatted text string

#### `clear_screen() -> str`
Returns ANSI code to clear terminal screen.

**Returns**: Clear screen escape sequence

#### `hide_cursor() -> str` / `show_cursor() -> str`
Returns ANSI codes to control cursor visibility.

**Returns**: Cursor visibility escape sequence

#### `move_cursor(row: int, col: int) -> str`
Returns ANSI code to move cursor position.

**Parameters**:
- `row`: Row position
- `col`: Column position

**Returns**: Cursor movement escape sequence

#### `get_terminal_size() -> tuple[int, int]`
Gets terminal dimensions.

**Returns**: Tuple of (rows, columns)

## Module: `animations.py`

### Classes

#### `MatrixRain`
Matrix-style digital rain animation.

**Methods**:
- `run()`: Run animation
- `_create_drop(col: int)`: Create falling character drop
- `_update_drops()`: Update all drops

#### `LoadingSpinner`
Loading spinner animation.

**Methods**:
- `start()`: Start spinner
- `stop()`: Stop spinner
- `update()`: Update spinner state

### Functions

#### `typewriter_effect(text: str, delay: float = 0.05, color: Optional[str] = None) -> Generator[str, None, None]`
Creates typewriter text effect.

**Parameters**:
- `text`: Text to animate
- `delay`: Delay between characters (default: 0.05)
- `color`: Optional color

**Returns**: Generator yielding animated text

#### `glitch_effect(text: str, iterations: int = 5, color: Optional[str] = None) -> Generator[str, None, None]`
Creates glitch text effect.

**Parameters**:
- `text`: Text to glitch
- `iterations`: Number of glitch iterations (default: 5)
- `color`: Optional color

**Returns**: Generator yielding glitched text

#### `matrix_banner(text: str, width: Optional[int] = None) -> str`
Creates Matrix-style banner.

**Parameters**:
- `text`: Banner text
- `width`: Optional banner width

**Returns**: Formatted banner string

#### `print_animated(text: str, animation_type: str = "typewriter", **kwargs) -> None`
Prints text with animation.

**Parameters**:
- `text`: Text to print
- `animation_type`: Animation type (typewriter, glitch, etc.)
- `**kwargs`: Additional animation parameters

## Cross-References

- [README.md](README.md) - Module overview and usage
- [../README.md](../README.md) - Source code overview
