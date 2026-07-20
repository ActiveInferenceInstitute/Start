from __future__ import annotations

from src.terminal.menu import Menu, MenuItem, MenuTheme


def test_menu_navigation_skips_disabled_items() -> None:
    menu = Menu(
        "Test",
        [MenuItem("one"), MenuItem("disabled", enabled=False), MenuItem("three")],
    )
    menu._move_to_next_enabled(1)
    assert menu.items[menu.selected_index].label == "three"
    keep_open, value = menu.handle_input("q")
    assert keep_open is False
    assert value is None


def test_menu_theme_and_rendering() -> None:
    menu = Menu("Title", [MenuItem("one", description="desc")], theme=MenuTheme())
    assert "Title" in menu._render_header()
    assert "one" in menu._render_items()


def test_menu_initial_selection_and_input_fallback_paths(monkeypatch) -> None:
    menu = Menu(
        "Test",
        [MenuItem("disabled", enabled=False), MenuItem("enabled")],
    )
    assert menu.selected_index == 1

    submenu = Menu("Sub", [MenuItem("sub-value")])
    parent = Menu("Parent", [MenuItem("sub", submenu=submenu)])
    monkeypatch.setattr(submenu, "show", lambda: "sub-result")
    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    assert parent._show_with_input() == "sub-result"

    blank_then_quit = iter(["", "", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(blank_then_quit))
    assert Menu("Blank", [MenuItem("one")])._show_with_input() is None

    interrupting = Menu("Interrupt", [MenuItem("one")])

    def raise_import_error():
        raise ImportError

    monkeypatch.setattr(interrupting, "_show_with_getch", raise_import_error)
    inputs = iter(["q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    assert interrupting.show() is None


def test_menu_getch_handles_interrupt(monkeypatch) -> None:
    class BrokenStdin:
        def fileno(self) -> int:
            raise KeyboardInterrupt

    monkeypatch.setattr("sys.stdin", BrokenStdin())
    assert Menu("Interrupt", [MenuItem("one")])._show_with_getch() is None


def test_dialog_interrupt_paths(monkeypatch) -> None:
    from src.terminal.menu import confirmation_dialog, input_dialog

    monkeypatch.setattr("src.terminal.menu.print_animated", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("builtins.input", lambda _prompt: (_ for _ in ()).throw(EOFError))

    assert confirmation_dialog("Continue") is False
    assert input_dialog("Value") is None
