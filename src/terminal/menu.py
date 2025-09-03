"""Interactive terminal menu system with Matrix-style theming.

This module provides interactive menu functionality with keyboard navigation,
Matrix-style visual effects, and support for nested menus.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from .animations import matrix_banner, print_animated
from .colors import clear_screen, matrix_text, move_cursor, show_cursor


@dataclass
class MenuItem:
    """Represents a menu item with action and styling."""
    
    label: str
    action: Optional[Callable[[], Any]] = None
    submenu: Optional['Menu'] = None
    description: str = ""
    enabled: bool = True
    style: str = "normal"  # normal, bright, dim, warning, gold, cyber


@dataclass 
class MenuTheme:
    """Visual theme configuration for menus."""
    
    title_style: str = "gold"
    selected_style: str = "bright"
    normal_style: str = "normal"
    disabled_style: str = "dim" 
    border_style: str = "cyber"
    description_style: str = "dim"


class Menu:
    """Interactive terminal menu with Matrix styling."""
    
    def __init__(
        self,
        title: str,
        items: List[MenuItem],
        theme: Optional[MenuTheme] = None,
        show_descriptions: bool = True,
    ):
        """Initialize menu.
        
        Args:
            title: Menu title
            items: List of menu items
            theme: Visual theme (uses default if None)
            show_descriptions: Whether to show item descriptions
        """
        self.title = title
        self.items = items
        self.theme = theme or MenuTheme()
        self.show_descriptions = show_descriptions
        self.selected_index = 0
        
        # Find first enabled item
        self._move_to_next_enabled()
    
    def _move_to_next_enabled(self, direction: int = 1) -> None:
        """Move selection to next enabled item.
        
        Args:
            direction: 1 for forward, -1 for backward
        """
        start_index = self.selected_index
        
        while True:
            self.selected_index = (self.selected_index + direction) % len(self.items)
            
            if self.items[self.selected_index].enabled:
                break
            
            # Prevent infinite loop if no enabled items
            if self.selected_index == start_index:
                break
    
    def _render_header(self) -> str:
        """Render menu header with title and banner.
        
        Returns:
            Formatted header string
        """
        header = clear_screen()
        header += matrix_banner(self.title) + "\n"
        return header
    
    def _render_items(self) -> str:
        """Render menu items with selection highlighting.
        
        Returns:
            Formatted menu items string
        """
        lines = []
        
        for i, item in enumerate(self.items):
            # Determine style
            if not item.enabled:
                style = self.theme.disabled_style
                prefix = "   "
            elif i == self.selected_index:
                style = self.theme.selected_style
                prefix = " ▶ "
            else:
                style = item.style or self.theme.normal_style
                prefix = "   "
            
            # Format item
            item_text = f"{prefix}{item.label}"
            lines.append(matrix_text(item_text, style))
            
            # Add description if enabled and item is selected
            if (self.show_descriptions and 
                item.description and 
                i == self.selected_index):
                desc_text = f"     {item.description}"
                lines.append(matrix_text(desc_text, self.theme.description_style))
        
        return "\n".join(lines)
    
    def _render_footer(self) -> str:
        """Render menu footer with navigation instructions.
        
        Returns:
            Formatted footer string
        """
        instructions = [
            "↑/↓: Navigate",
            "Enter: Select", 
            "q: Quit",
        ]
        
        footer = "\n" + matrix_text("─" * 50, self.theme.border_style) + "\n"
        footer += matrix_text(" | ".join(instructions), self.theme.description_style)
        
        return footer
    
    def render(self) -> str:
        """Render complete menu.
        
        Returns:
            Complete formatted menu string
        """
        return self._render_header() + self._render_items() + self._render_footer()
    
    def handle_input(self, key: str) -> Tuple[bool, Any]:
        """Handle keyboard input.
        
        Args:
            key: Input key character
            
        Returns:
            Tuple of (continue_menu, result)
        """
        if key == "q" or key == "\x1b":  # q or Escape
            return False, None
        elif key == "\033[A":  # Up arrow
            self._move_to_next_enabled(-1)
        elif key == "\033[B":  # Down arrow
            self._move_to_next_enabled(1)
        elif key == "\r" or key == "\n":  # Enter
            selected_item = self.items[self.selected_index]
            
            if not selected_item.enabled:
                return True, None
            
            if selected_item.submenu:
                # Show submenu
                result = selected_item.submenu.show()
                return True, result
            elif selected_item.action:
                # Execute action
                try:
                    result = selected_item.action()
                    return False, result
                except Exception as e:
                    print(matrix_text(f"Error: {e}", "warning"))
                    input(matrix_text("Press Enter to continue...", "dim"))
                    return True, None
            else:
                return False, selected_item.label
        
        return True, None
    
    def show(self) -> Any:
        """Display menu and handle user interaction.
        
        Returns:
            Selected item result or None
        """
        # Try to use system-specific input handling
        try:
            return self._show_with_getch()
        except ImportError:
            return self._show_with_input()
    
    def _show_with_input(self) -> Any:
        """Fallback menu display using standard input.
        
        Returns:
            Selected item result or None
        """
        while True:
            print(self.render())
            
            try:
                # Show numbered options for easier selection
                print(matrix_text("\nEnter number or q to quit:", "cyber"))
                for i, item in enumerate(self.items):
                    if item.enabled:
                        print(matrix_text(f"{i+1}. {item.label}", "normal"))
                
                choice = input(matrix_text("> ", "bright")).strip().lower()
                
                if choice == 'q':
                    return None
                
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(self.items) and self.items[index].enabled:
                        item = self.items[index]
                        
                        if item.submenu:
                            result = item.submenu.show()
                            if result is not None:
                                return result
                        elif item.action:
                            return item.action()
                        else:
                            return item.label
                    else:
                        print(matrix_text("Invalid selection!", "warning"))
                        input(matrix_text("Press Enter to continue...", "dim"))
                except ValueError:
                    print(matrix_text("Please enter a number!", "warning"))
                    input(matrix_text("Press Enter to continue...", "dim"))
                    
            except (KeyboardInterrupt, EOFError):
                return None
    
    def _show_with_getch(self) -> Any:
        """Show menu with single-character input handling.
        
        Returns:
            Selected item result or None
        """
        # Try to import platform-specific getch
        try:
            import msvcrt
            
            def getch():
                return msvcrt.getch().decode('utf-8')
        except ImportError:
            import termios
            import tty
            
            def getch():
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    # Handle both old and new Python versions
                    if hasattr(tty, 'cbreak'):
                        tty.cbreak(fd)
                    else:
                        tty.setcbreak(fd)
                    char = sys.stdin.read(1)
                    
                    # Handle escape sequences (arrow keys)
                    if char == '\033':
                        char += sys.stdin.read(2)
                    
                    return char
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        try:
            while True:
                print(self.render())
                
                key = getch()
                should_continue, result = self.handle_input(key)
                
                if not should_continue:
                    return result
        except (KeyboardInterrupt, EOFError):
            print(show_cursor())
            return None


class MenuBuilder:
    """Builder pattern for creating complex menus."""
    
    def __init__(self, title: str):
        """Initialize menu builder.
        
        Args:
            title: Menu title
        """
        self.title = title
        self.items: List[MenuItem] = []
        self.theme = MenuTheme()
        self.show_descriptions = True
    
    def add_item(
        self,
        label: str,
        action: Optional[Callable[[], Any]] = None,
        description: str = "",
        style: str = "normal",
        enabled: bool = True,
    ) -> 'MenuBuilder':
        """Add a menu item.
        
        Args:
            label: Item label
            action: Action to execute when selected
            description: Item description
            style: Visual style
            enabled: Whether item is selectable
            
        Returns:
            Self for method chaining
        """
        item = MenuItem(
            label=label,
            action=action,
            description=description,
            style=style,
            enabled=enabled,
        )
        self.items.append(item)
        return self
    
    def add_submenu(
        self,
        label: str,
        submenu: Menu,
        description: str = "",
        style: str = "normal",
    ) -> 'MenuBuilder':
        """Add a submenu item.
        
        Args:
            label: Item label
            submenu: Submenu to show when selected
            description: Item description
            style: Visual style
            
        Returns:
            Self for method chaining
        """
        item = MenuItem(
            label=label,
            submenu=submenu,
            description=description,
            style=style,
        )
        self.items.append(item)
        return self
    
    def add_separator(self, label: str = "─" * 30) -> 'MenuBuilder':
        """Add a visual separator.
        
        Args:
            label: Separator text
            
        Returns:
            Self for method chaining
        """
        item = MenuItem(
            label=label,
            enabled=False,
            style="dim",
        )
        self.items.append(item)
        return self
    
    def set_theme(self, theme: MenuTheme) -> 'MenuBuilder':
        """Set menu theme.
        
        Args:
            theme: Menu theme configuration
            
        Returns:
            Self for method chaining
        """
        self.theme = theme
        return self
    
    def build(self) -> Menu:
        """Build the menu.
        
        Returns:
            Configured menu instance
        """
        return Menu(
            title=self.title,
            items=self.items,
            theme=self.theme,
            show_descriptions=self.show_descriptions,
        )


def confirmation_dialog(message: str, default_yes: bool = False) -> bool:
    """Show a yes/no confirmation dialog.
    
    Args:
        message: Confirmation message
        default_yes: Default to yes if True, no if False
        
    Returns:
        True if user confirms, False otherwise
    """
    default = "Y/n" if default_yes else "y/N"
    
    print_animated(f"\n{message}", "typewriter")
    
    while True:
        try:
            response = input(matrix_text(f"Continue? ({default}): ", "cyber")).strip().lower()
            
            if not response:
                return default_yes
            
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print(matrix_text("Please enter y/yes or n/no", "warning"))
        except (KeyboardInterrupt, EOFError):
            return False


def input_dialog(
    prompt: str,
    default: str = "",
    validation: Optional[Callable[[str], bool]] = None,
    error_message: str = "Invalid input",
) -> Optional[str]:
    """Show an input dialog with optional validation.
    
    Args:
        prompt: Input prompt message
        default: Default value
        validation: Optional validation function
        error_message: Error message for invalid input
        
    Returns:
        User input string or None if cancelled
    """
    print_animated(f"\n{prompt}", "typewriter")
    
    if default:
        print(matrix_text(f"(Default: {default})", "dim"))
    
    while True:
        try:
            value = input(matrix_text("> ", "bright")).strip()
            
            if not value and default:
                value = default
            
            if validation and not validation(value):
                print(matrix_text(error_message, "warning"))
                continue
            
            return value
        except (KeyboardInterrupt, EOFError):
            return None
