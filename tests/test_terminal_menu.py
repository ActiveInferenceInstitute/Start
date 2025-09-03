"""Tests for terminal menu module."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.terminal.menu import (
    Menu,
    MenuBuilder,
    MenuItem,
    MenuTheme,
    confirmation_dialog,
    input_dialog,
)


class TestMenuItem:
    """Test MenuItem dataclass."""
    
    def test_menu_item_basic(self):
        """Test basic menu item creation."""
        item = MenuItem("Test Item")
        assert item.label == "Test Item"
        assert item.action is None
        assert item.submenu is None
        assert item.description == ""
        assert item.enabled is True
        assert item.style == "normal"
    
    def test_menu_item_with_action(self):
        """Test menu item with action."""
        def test_action():
            return "test result"
        
        item = MenuItem("Action Item", action=test_action)
        assert item.label == "Action Item"
        assert item.action == test_action
        assert item.action() == "test result"
    
    def test_menu_item_disabled(self):
        """Test disabled menu item."""
        item = MenuItem("Disabled", enabled=False)
        assert item.enabled is False
    
    def test_menu_item_with_description(self):
        """Test menu item with description."""
        item = MenuItem("Test", description="Test description")
        assert item.description == "Test description"


class TestMenuTheme:
    """Test MenuTheme dataclass."""
    
    def test_menu_theme_defaults(self):
        """Test default menu theme."""
        theme = MenuTheme()
        assert theme.title_style == "gold"
        assert theme.selected_style == "bright"
        assert theme.normal_style == "normal"
        assert theme.disabled_style == "dim"
        assert theme.border_style == "cyber"
        assert theme.description_style == "dim"
    
    def test_menu_theme_custom(self):
        """Test custom menu theme."""
        theme = MenuTheme(
            title_style="cyan",
            selected_style="red",
        )
        assert theme.title_style == "cyan"
        assert theme.selected_style == "red"
        assert theme.normal_style == "normal"  # Default


class TestMenu:
    """Test Menu class."""
    
    def test_menu_initialization(self):
        """Test menu initialization."""
        items = [MenuItem("Item 1"), MenuItem("Item 2")]
        menu = Menu("Test Menu", items)
        
        assert menu.title == "Test Menu"
        assert len(menu.items) == 2
        assert menu.selected_index == 0
        assert menu.show_descriptions is True
    
    def test_menu_find_enabled_item(self):
        """Test finding enabled items."""
        items = [
            MenuItem("Disabled 1", enabled=False),
            MenuItem("Enabled 1", enabled=True),
            MenuItem("Disabled 2", enabled=False),
        ]
        menu = Menu("Test", items)
        
        # Should start on first enabled item
        assert menu.selected_index == 1
    
    def test_menu_move_to_next_enabled(self):
        """Test navigation to next enabled item."""
        items = [
            MenuItem("Item 1", enabled=True),
            MenuItem("Item 2", enabled=False),
            MenuItem("Item 3", enabled=True),
        ]
        menu = Menu("Test", items)
        
        assert menu.selected_index == 0
        menu._move_to_next_enabled(1)  # Move forward
        assert menu.selected_index == 2  # Should skip disabled item
    
    def test_menu_move_to_previous_enabled(self):
        """Test navigation to previous enabled item."""
        items = [
            MenuItem("Item 1", enabled=True),
            MenuItem("Item 2", enabled=False),
            MenuItem("Item 3", enabled=True),
        ]
        menu = Menu("Test", items)
        menu.selected_index = 2
        
        menu._move_to_next_enabled(-1)  # Move backward
        assert menu.selected_index == 0  # Should skip disabled item
    
    def test_menu_render_header(self):
        """Test menu header rendering."""
        items = [MenuItem("Item 1")]
        menu = Menu("Test Title", items)
        
        header = menu._render_header()
        
        assert isinstance(header, str)
        assert "Test Title" in header
        assert "\033[2J\033[H" in header  # Clear screen
    
    def test_menu_render_items(self):
        """Test menu items rendering."""
        items = [
            MenuItem("Item 1", enabled=True),
            MenuItem("Item 2", enabled=False),
            MenuItem("Item 3", enabled=True, description="Test desc"),
        ]
        menu = Menu("Test", items)
        menu.selected_index = 2
        
        rendered = menu._render_items()
        
        assert "Item 1" in rendered
        assert "Item 2" in rendered
        assert "Item 3" in rendered
        assert "▶" in rendered  # Selection indicator
        assert "Test desc" in rendered  # Description for selected item
    
    def test_menu_render_footer(self):
        """Test menu footer rendering."""
        items = [MenuItem("Item 1")]
        menu = Menu("Test", items)
        
        footer = menu._render_footer()
        
        assert "↑/↓: Navigate" in footer
        assert "Enter: Select" in footer
        assert "q: Quit" in footer
    
    def test_menu_handle_input_navigation(self):
        """Test menu input handling for navigation."""
        items = [MenuItem("Item 1"), MenuItem("Item 2")]
        menu = Menu("Test", items)
        
        # Test down arrow
        continue_menu, result = menu.handle_input("\033[B")
        assert continue_menu is True
        assert result is None
        assert menu.selected_index == 1
        
        # Test up arrow
        continue_menu, result = menu.handle_input("\033[A")
        assert continue_menu is True
        assert result is None
        assert menu.selected_index == 0
    
    def test_menu_handle_input_quit(self):
        """Test menu input handling for quit."""
        items = [MenuItem("Item 1")]
        menu = Menu("Test", items)
        
        # Test 'q' key
        continue_menu, result = menu.handle_input("q")
        assert continue_menu is False
        assert result is None
        
        # Test escape key
        continue_menu, result = menu.handle_input("\x1b")
        assert continue_menu is False
        assert result is None
    
    def test_menu_handle_input_select_action(self):
        """Test menu input handling for selection with action."""
        def test_action():
            return "action result"
        
        items = [MenuItem("Action Item", action=test_action)]
        menu = Menu("Test", items)
        
        continue_menu, result = menu.handle_input("\r")
        assert continue_menu is False
        assert result == "action result"
    
    def test_menu_handle_input_select_no_action(self):
        """Test menu input handling for selection without action."""
        items = [MenuItem("Simple Item")]
        menu = Menu("Test", items)
        
        continue_menu, result = menu.handle_input("\r")
        assert continue_menu is False
        assert result == "Simple Item"
    
    def test_menu_handle_input_disabled_item(self):
        """Test handling selection of disabled item."""
        items = [MenuItem("Disabled", enabled=False)]
        menu = Menu("Test", items)
        menu.selected_index = 0  # Force selection on disabled
        
        continue_menu, result = menu.handle_input("\r")
        assert continue_menu is True
        assert result is None
    
    @patch('builtins.input', side_effect=['q'])
    @patch('builtins.print')
    def test_menu_show_with_input_quit(self, mock_print, mock_input):
        """Test menu show with input method - quit."""
        items = [MenuItem("Item 1")]
        menu = Menu("Test", items)
        
        result = menu._show_with_input()
        assert result is None
    
    @patch('builtins.input', side_effect=['1'])
    @patch('builtins.print')
    def test_menu_show_with_input_select(self, mock_print, mock_input):
        """Test menu show with input method - selection."""
        def test_action():
            return "selected"
        
        items = [MenuItem("Item 1", action=test_action)]
        menu = Menu("Test", items)
        
        result = menu._show_with_input()
        assert result == "selected"
    
    @patch('builtins.input', side_effect=['invalid', 'q'])
    @patch('builtins.print')
    def test_menu_show_with_input_invalid(self, mock_print, mock_input):
        """Test menu show with input method - invalid input."""
        items = [MenuItem("Item 1")]
        menu = Menu("Test", items)
        
        result = menu._show_with_input()
        assert result is None


class TestMenuBuilder:
    """Test MenuBuilder class."""
    
    def test_menu_builder_initialization(self):
        """Test menu builder initialization."""
        builder = MenuBuilder("Test Menu")
        assert builder.title == "Test Menu"
        assert len(builder.items) == 0
        assert builder.show_descriptions is True
    
    def test_menu_builder_add_item(self):
        """Test adding items to menu builder."""
        builder = MenuBuilder("Test")
        
        result = builder.add_item("Item 1", description="First item")
        
        assert result is builder  # Method chaining
        assert len(builder.items) == 1
        assert builder.items[0].label == "Item 1"
        assert builder.items[0].description == "First item"
    
    def test_menu_builder_add_item_with_action(self):
        """Test adding item with action."""
        def test_action():
            return "test"
        
        builder = MenuBuilder("Test")
        builder.add_item("Action Item", action=test_action)
        
        assert len(builder.items) == 1
        assert builder.items[0].action == test_action
    
    def test_menu_builder_add_submenu(self):
        """Test adding submenu item."""
        submenu = Menu("Submenu", [MenuItem("Sub Item")])
        builder = MenuBuilder("Test")
        
        result = builder.add_submenu("Submenu Item", submenu)
        
        assert result is builder
        assert len(builder.items) == 1
        assert builder.items[0].submenu == submenu
    
    def test_menu_builder_add_separator(self):
        """Test adding separator."""
        builder = MenuBuilder("Test")
        
        result = builder.add_separator("---")
        
        assert result is builder
        assert len(builder.items) == 1
        assert builder.items[0].label == "---"
        assert builder.items[0].enabled is False
    
    def test_menu_builder_set_theme(self):
        """Test setting menu theme."""
        theme = MenuTheme(title_style="red")
        builder = MenuBuilder("Test")
        
        result = builder.set_theme(theme)
        
        assert result is builder
        assert builder.theme == theme
    
    def test_menu_builder_build(self):
        """Test building menu."""
        builder = MenuBuilder("Test Menu")
        builder.add_item("Item 1")
        builder.add_item("Item 2")
        
        menu = builder.build()
        
        assert isinstance(menu, Menu)
        assert menu.title == "Test Menu"
        assert len(menu.items) == 2
        assert menu.items[0].label == "Item 1"
        assert menu.items[1].label == "Item 2"


class TestConfirmationDialog:
    """Test confirmation_dialog function."""
    
    @patch('builtins.input', return_value='y')
    @patch('src.terminal.menu.print_animated')
    def test_confirmation_dialog_yes(self, mock_print, mock_input):
        """Test confirmation dialog with yes response."""
        result = confirmation_dialog("Are you sure?")
        assert result is True
    
    @patch('builtins.input', return_value='n')
    @patch('src.terminal.menu.print_animated')
    def test_confirmation_dialog_no(self, mock_print, mock_input):
        """Test confirmation dialog with no response."""
        result = confirmation_dialog("Are you sure?")
        assert result is False
    
    @patch('builtins.input', return_value='')
    @patch('src.terminal.menu.print_animated')
    def test_confirmation_dialog_default_no(self, mock_print, mock_input):
        """Test confirmation dialog with default no."""
        result = confirmation_dialog("Are you sure?", default_yes=False)
        assert result is False
    
    @patch('builtins.input', return_value='')
    @patch('src.terminal.menu.print_animated')
    def test_confirmation_dialog_default_yes(self, mock_print, mock_input):
        """Test confirmation dialog with default yes."""
        result = confirmation_dialog("Are you sure?", default_yes=True)
        assert result is True
    
    @patch('builtins.input', side_effect=['invalid', 'yes'])
    @patch('src.terminal.menu.print_animated')
    @patch('builtins.print')
    def test_confirmation_dialog_invalid_then_valid(self, mock_print_builtin, mock_print_animated, mock_input):
        """Test confirmation dialog with invalid then valid input."""
        result = confirmation_dialog("Are you sure?")
        assert result is True
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    @patch('src.terminal.menu.print_animated')
    def test_confirmation_dialog_keyboard_interrupt(self, mock_print, mock_input):
        """Test confirmation dialog with keyboard interrupt."""
        result = confirmation_dialog("Are you sure?")
        assert result is False


class TestInputDialog:
    """Test input_dialog function."""
    
    @patch('builtins.input', return_value='user input')
    @patch('src.terminal.menu.print_animated')
    @patch('builtins.print')
    def test_input_dialog_basic(self, mock_print_builtin, mock_print_animated, mock_input):
        """Test basic input dialog."""
        result = input_dialog("Enter value:")
        assert result == "user input"
    
    @patch('builtins.input', return_value='')
    @patch('src.terminal.menu.print_animated')
    @patch('builtins.print')
    def test_input_dialog_default_value(self, mock_print_builtin, mock_print_animated, mock_input):
        """Test input dialog with default value."""
        result = input_dialog("Enter value:", default="default")
        assert result == "default"
    
    @patch('builtins.input', return_value='valid')
    @patch('src.terminal.menu.print_animated')
    @patch('builtins.print')
    def test_input_dialog_with_validation(self, mock_print_builtin, mock_print_animated, mock_input):
        """Test input dialog with validation."""
        def validate(value):
            return len(value) > 3
        
        result = input_dialog("Enter value:", validation=validate)
        assert result == "valid"
    
    @patch('builtins.input', side_effect=['no', 'valid'])
    @patch('src.terminal.menu.print_animated')
    @patch('builtins.print')
    def test_input_dialog_validation_retry(self, mock_print_builtin, mock_print_animated, mock_input):
        """Test input dialog with validation retry."""
        def validate(value):
            return len(value) > 3
        
        result = input_dialog("Enter value:", validation=validate)
        assert result == "valid"
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    @patch('src.terminal.menu.print_animated')
    @patch('builtins.print')
    def test_input_dialog_keyboard_interrupt(self, mock_print_builtin, mock_print_animated, mock_input):
        """Test input dialog with keyboard interrupt."""
        result = input_dialog("Enter value:")
        assert result is None


@pytest.mark.integration
class TestMenuIntegration:
    """Integration tests for menu functionality."""
    
    def test_menu_builder_complete_workflow(self):
        """Test complete menu building workflow."""
        # Create actions
        action_called = []
        
        def action1():
            action_called.append("action1")
            return "result1"
        
        def action2():
            action_called.append("action2")
            return "result2"
        
        # Build menu
        menu = (MenuBuilder("Integration Test")
                .add_item("Action 1", action1, "First action")
                .add_separator()
                .add_item("Action 2", action2, "Second action", style="bright")
                .add_item("Disabled", enabled=False)
                .build())
        
        assert len(menu.items) == 4
        assert menu.items[0].action == action1
        assert menu.items[1].enabled is False  # Separator
        assert menu.items[2].style == "bright"
        assert menu.items[3].enabled is False  # Disabled
    
    def test_menu_navigation_wrapping(self):
        """Test menu navigation wrapping."""
        items = [
            MenuItem("Item 1", enabled=True),
            MenuItem("Item 2", enabled=False),
            MenuItem("Item 3", enabled=True),
        ]
        menu = Menu("Test", items)
        
        # Start at first enabled (index 0)
        assert menu.selected_index == 0
        
        # Move forward to next enabled (index 2)
        menu._move_to_next_enabled(1)
        assert menu.selected_index == 2
        
        # Move forward should wrap to first enabled (index 0)
        menu._move_to_next_enabled(1)
        assert menu.selected_index == 0
    
    def test_menu_with_submenu(self):
        """Test menu with submenu functionality."""
        # Create submenu
        submenu_items = [MenuItem("Sub Item 1"), MenuItem("Sub Item 2")]
        submenu = Menu("Submenu", submenu_items)
        
        # Create main menu with submenu
        main_items = [MenuItem("Main Item"), MenuItem("Submenu Item", submenu=submenu)]
        main_menu = Menu("Main Menu", main_items)
        
        # Test submenu reference
        assert main_menu.items[1].submenu == submenu
        assert len(main_menu.items[1].submenu.items) == 2
    
    @patch('src.terminal.menu.print_animated')
    @patch('builtins.print')
    def test_dialog_integration(self, mock_print, mock_print_animated):
        """Test dialog functions integration."""
        with patch('builtins.input', return_value='test input'):
            # Test input dialog
            result = input_dialog("Test prompt", default="default")
            assert result == "test input"
        
        with patch('builtins.input', return_value='y'):
            # Test confirmation dialog
            result = confirmation_dialog("Confirm?")
            assert result is True
