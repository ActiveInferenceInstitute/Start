from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from src.repos.clone_repo import clone_repository as clone_with_gitpython
from src.repos.clone_repo import main as clone_cli_main
from src.repos.clone_repo import parse_args
from src.repos.cloning import (
    CloneResult,
    RepoInfo,
    clone_all_repositories,
    clone_multiple_repositories,
    clone_repository,
    estimate_clone_time,
    get_clone_destination,
    get_repository_status,
    update_repository,
    validate_repository_url,
)
from src.repos.manager import (
    RepositoryManager,
    format_clone_results,
    format_repository_status,
    format_repository_summary,
)
from src.system.dependencies import (
    DependencyCheck,
    DependencyReport,
    check_project_files,
    check_python_package,
    check_system_tool,
    check_uv_environment,
    format_dependency_report,
    get_installation_instructions,
    get_optional_python_packages,
    get_optional_system_tools,
    get_required_system_tools,
    run_comprehensive_dependency_check,
)
from src.system.environment import (
    is_uv_available,
    run_health_check,
    run_uv_sync,
    setup_project_environment,
)
from src.system.reporting import (
    SystemInfo,
    check_system_requirements,
    format_system_report,
    generate_system_report,
    get_cpu_info,
    get_git_info,
    get_resource_usage,
    run_command_safely,
)
from src.terminal import animations, colors
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
from src.terminal.menu import (
    Menu,
    MenuBuilder,
    MenuItem,
    MenuTheme,
    confirmation_dialog,
    input_dialog,
)


def _git(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _local_remote(tmp_path: Path) -> tuple[Path, Path]:
    bare = tmp_path / "remote.git"
    source = tmp_path / "source"
    _git("init", "--bare", str(bare))
    _git("init", "-b", "main", str(source))
    _git("config", "user.email", "tests@example.invalid", cwd=source)
    _git("config", "user.name", "START tests", cwd=source)
    (source / "README.md").write_text("initial", encoding="utf-8")
    _git("add", ".", cwd=source)
    _git("commit", "-m", "initial", cwd=source)
    _git("remote", "add", "origin", str(bare), cwd=source)
    _git("push", "-u", "origin", "main", cwd=source)
    return bare, source


def test_repository_operations_cover_real_local_git_paths(tmp_path: Path) -> None:
    bare, _ = _local_remote(tmp_path)
    clone_root = tmp_path / "clones"
    destination = get_clone_destination("project", clone_root)
    assert destination == clone_root.resolve() / "project"
    assert estimate_clone_time("https://github.com/ActiveInferenceInstitute/x") == "30-60 seconds"
    assert estimate_clone_time("https://github.com/x/RxInfer") == "10-30 seconds"
    assert estimate_clone_time("https://github.com/x/pymdp") == "15-45 seconds"
    assert estimate_clone_time("file:///tmp/repository") == "10-90 seconds"

    messages: list[str] = []
    info = RepoInfo("project", str(bare), branch="main", shallow=True)
    first = clone_repository(
        info,
        destination,
        base_dir=clone_root,
        progress_callback=messages.append,
        allow_unsafe_sources=True,
    )
    assert first.success and first.destination == destination
    assert any("Starting clone" in message for message in messages)

    forced = clone_repository(
        info, destination, force=True, base_dir=clone_root, allow_unsafe_sources=True
    )
    assert forced.success
    no_force = clone_repository(info, destination, base_dir=clone_root, allow_unsafe_sources=True)
    assert not no_force.success and "already exists" in (no_force.error_message or "")
    preserved = clone_repository(
        RepoInfo("project", str(tmp_path / "missing.git"), shallow=False),
        destination,
        force=True,
        base_dir=clone_root,
        allow_unsafe_sources=True,
    )
    assert preserved.success is False
    assert (destination / ".git").exists()
    failed = clone_repository(
        RepoInfo("missing", str(tmp_path / "missing.git"), shallow=False),
        clone_root / "missing",
        base_dir=clone_root,
        allow_unsafe_sources=True,
    )
    assert not failed.success and "Git clone failed" in (failed.error_message or "")
    invalid_url = clone_repository(RepoInfo("invalid", "-bad"), clone_root / "invalid")
    assert not invalid_url.success and "Unsafe repository URL" in (invalid_url.error_message or "")
    root_guard = clone_repository(
        RepoInfo("root", str(bare)),
        Path("/"),
        force=True,
        base_dir=Path("/"),
        allow_unsafe_sources=True,
    )
    assert not root_guard.success and "Refusing destructive" in (root_guard.error_message or "")

    unknown = clone_multiple_repositories(["unknown"], base_dir=clone_root)
    assert not unknown[0].success and "Unknown repository" in (unknown[0].error_message or "")
    assert clone_all_repositories(category="not-a-category", base_dir=clone_root) == []
    assert validate_repository_url(str(bare)) is False
    assert validate_repository_url(str(bare), allow_unsafe_sources=True) is True
    assert (
        validate_repository_url(str(tmp_path / "not-a-repository"), allow_unsafe_sources=True)
        is False
    )

    changed = destination / "README.md"
    changed.write_text("changed", encoding="utf-8")
    status = get_repository_status(destination)
    assert status["uncommitted_changes"] is True
    assert status["last_commit"]
    assert get_repository_status(tmp_path / "missing")["exists"] is False
    assert get_repository_status(tmp_path / "plain")["is_git_repo"] is False
    (tmp_path / "plain").mkdir()
    assert update_repository(tmp_path / "plain") == (False, "Not a git repository")

    _git("checkout", "--detach", cwd=destination)
    detached = update_repository(destination)
    assert detached[0] is False and "detached" in detached[1]
    _git("checkout", "main", cwd=destination)
    _git("remote", "remove", "origin", cwd=destination)
    no_remote = update_repository(destination)
    assert no_remote[0] is False and "Failed to update" in no_remote[1]


def test_clone_rejects_symlink_boundaries(tmp_path: Path) -> None:
    bare, _ = _local_remote(tmp_path)
    clone_root = tmp_path / "clones"
    outside = tmp_path / "outside"
    outside.mkdir()
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(outside, target_is_directory=True)
    result = clone_repository(
        RepoInfo("linked", str(bare)),
        linked_root / "linked",
        base_dir=clone_root,
        allow_unsafe_sources=True,
    )
    assert result.success is False
    assert "symlink" in (result.error_message or "").lower()
    assert not (outside / "linked").exists()


def test_repository_manager_and_gitpython_entrypoint(tmp_path: Path) -> None:
    bare, _ = _local_remote(tmp_path)
    destination = tmp_path / "gitpython-clone"
    assert clone_with_gitpython(str(bare), destination, allow_unsafe_sources=True).exists()
    assert parse_args(["--url", str(bare), "--dest", str(tmp_path / "other")]).url == str(bare)
    assert (
        clone_cli_main(
            [
                "--url",
                str(bare),
                "--dest",
                str(tmp_path / "cli"),
                "--allow-unsafe-sources",
            ]
        )
        == 0
    )

    manager = RepositoryManager(tmp_path / "managed")
    assert manager.list_available_repositories()
    assert manager.get_repository_categories()
    assert manager.clone_repository("unknown").success is False
    assert manager.clone_repositories(["unknown"])[0].success is False
    assert manager.clone_all(category="not-a-category") == []
    assert manager.list_cloned_repositories() == {}
    assert manager.update_repository("missing")[0] is False
    assert manager.update_all_repositories() == []
    assert manager.get_all_repository_status() == {}
    assert manager.cleanup_failed_clones() == []
    summary = manager.get_summary()
    assert summary["available_count"] > 0
    valid_setup, setup_issues = manager.validate_setup()
    assert isinstance(valid_setup, bool)
    assert isinstance(setup_issues, list)
    exported = manager.export_configuration()
    assert exported["base_dir"] == str(manager.base_dir)
    assert manager.delete_repository("missing")[0] is False
    outside = manager.base_dir.parent / "outside"
    outside.mkdir()
    assert manager.delete_repository("../outside")[0] is False

    assert "Successful: 1" in format_clone_results(
        [CloneResult("x", True, size_mb=1.0, clone_time=1.0)]
    )
    assert "Available repositories" in format_repository_summary(summary)
    assert "Not a git repository" in format_repository_status(
        {"plain": get_repository_status(outside)}
    )


def test_dependency_reporting_paths(monkeypatch) -> None:
    missing = check_python_package("package_that_is_not_installed_for_start_tests", required=False)
    assert not missing.available and missing.install_hint
    assert check_system_tool("python").available
    absent = check_system_tool("tool_that_is_not_installed_for_start_tests", required=False)
    assert not absent.available and absent.install_hint
    assert get_required_system_tools()
    assert get_optional_system_tools()
    assert get_optional_python_packages()
    assert check_uv_environment().name == "uv-environment"
    assert all(check.available for check in check_project_files())

    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    report = run_comprehensive_dependency_check()
    assert report.all_required_available is False
    formatted = format_dependency_report(report, show_optional=False)
    assert "MISSING REQUIRED DEPENDENCIES" in formatted
    assert "INSTALLATION INSTRUCTIONS" in get_installation_instructions()
    minimal = DependencyReport(
        python_packages=[
            DependencyCheck("x", True, False, error_message="missing", install_hint="install")
        ],
        system_tools=[DependencyCheck("git", True, True, version="git")],
        optional_tools=[DependencyCheck("uv", False, False, install_hint="install uv")],
        missing_required=["python:x"],
    )
    assert "python:x" in format_dependency_report(minimal)
    from src.system.dependencies import probe_api_connectivity

    with pytest.raises(ValueError, match="greater than zero"):
        probe_api_connectivity(0)
    probe = probe_api_connectivity(0.01)
    assert {"perplexity", "openrouter", "errors"} <= set(probe)


def test_environment_health_and_subprocess_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PATH", "")
    success, messages = setup_project_environment()
    assert success is False
    assert any("uv not found" in message for message in messages)
    assert is_uv_available() is False

    sync_success, sync_output = run_uv_sync(
        root=tmp_path,
        command=[sys.executable, "-c", "print('synced')"],
    )
    assert sync_success is True and "synced" in sync_output
    monkeypatch.setenv("PERPLEXITY_API_KEY", "perplexity-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    for directory in ("src", "data", "data/config", "data/prompts", "tests"):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    configured, configured_messages = setup_project_environment(
        project_root=tmp_path,
        sync_command=[sys.executable, "-c", "print('synced')"],
    )
    assert configured is True, configured_messages
    assert any("Dependencies synced" in message for message in configured_messages)

    healthy, details = run_health_check()
    assert isinstance(healthy, bool)
    assert set(details) == {
        "python_environment",
        "dependencies",
        "configuration",
        "api_connectivity",
        "file_system",
    }
    assert isinstance(details["api_connectivity"]["healthy"], bool)

    ok, stdout, stderr = run_command_safely([sys.executable, "-c", "print('ok')"])
    assert ok and stdout.strip() == "ok" and stderr == ""
    failed, _, error = run_command_safely([sys.executable, "-c", "raise SystemExit(2)"])
    assert failed is False and error == ""
    timed_out, _, timeout_error = run_command_safely(
        [sys.executable, "-c", "import time; time.sleep(1)"], timeout=0.01
    )
    assert timed_out is False and "timed out" in timeout_error


def test_system_report_and_resource_formats() -> None:
    assert get_git_info()
    assert get_cpu_info()["logical_cores"]
    usage = get_resource_usage()
    assert usage.cpu_percent >= 0
    system = generate_system_report()
    detailed = format_system_report(system, detailed=True)
    compact = format_system_report(
        SystemInfo(
            hostname="host",
            os_name="test",
            os_version="1",
            architecture="x86",
            report_time="2026-01-01T00:00:00",
        ),
        detailed=False,
    )
    assert "SYSTEM REPORT" in detailed
    assert "SYSTEM REPORT" in compact
    requirements = check_system_requirements()
    assert set(requirements) == {
        "python_3_10_plus",
        "sufficient_memory",
        "sufficient_disk_space",
        "internet_connected",
    }


def test_terminal_color_and_animation_paths(monkeypatch) -> None:
    monkeypatch.setattr(colors, "is_color_supported", lambda: True)
    assert colors.colorize("x", colors.Color.RED).endswith(colors.Color.RESET.value)
    assert colors.colorize("x", "custom", reset=False).startswith("custom")
    assert colors.matrix_text("x", "gold") != "x"
    assert colors.matrix_text("x", "unknown") != "x"
    assert colors.gradient_text("abcd", "a", "b").endswith(colors.Color.RESET.value)
    assert colors.rainbow_text("rainbow").endswith(colors.Color.RESET.value)
    assert colors.clear_screen() and colors.hide_cursor() and colors.show_cursor()
    assert colors.move_cursor(2, 3) == "\033[2;3H"
    assert len(colors.get_terminal_size()) == 2

    monkeypatch.setattr(animations.time, "sleep", lambda _seconds: None)
    assert len(list(typewriter_effect("abc", delay=0))) == 4
    assert list(glitch_effect("abc", intensity=1, duration=0))[-1].endswith(
        colors.Color.RESET.value
    )
    rain = MatrixRain(duration=0, density=1)
    rain._update_drops()
    assert rain._render_frame()
    assert list(rain.animate())
    assert list(LoadingSpinner("load", "lines").animate(0))
    assert "TEST" in matrix_banner("TEST", width=20)
    assert list(dramatic_pause("wait", duration=0))
    monkeypatch.setattr(animations.random, "uniform", lambda _a, _b: 0)
    assert list(boot_sequence(["step"], delay=0))
    print_animated("text", animation_type="typewriter", delay=0)
    print_animated("text", animation_type="glitch", intensity=1, duration=0)
    print_animated("text", animation_type="unknown")


def test_menu_builder_navigation_and_dialogs(monkeypatch) -> None:
    action_result = Menu("Sub", [MenuItem("sub-result")])
    builder = MenuBuilder("Main")
    theme = MenuTheme(title_style="bright")
    builder.set_theme(theme).add_item("action", action=lambda: "done", description="run")
    builder.add_submenu("sub", action_result).add_separator("separator")
    menu = builder.build()
    assert menu.theme is theme
    assert menu.render()
    menu.selected_index = 0
    assert menu.handle_input("\n") == (False, "done")
    menu.selected_index = 1

    def unavailable_getch():
        raise ImportError

    monkeypatch.setattr(action_result, "_show_with_getch", unavailable_getch)
    submenu_input = iter(["q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(submenu_input))
    assert menu.handle_input("\n") == (True, None)
    menu.selected_index = 2
    assert menu.handle_input("\n") == (True, None)
    menu.handle_input("\033[A")
    menu.handle_input("\033[B")
    assert menu.handle_input("x") == (True, None)

    broken = Menu("Broken", [MenuItem("broken", action=lambda: 1 / 0)])
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    assert broken.handle_input("\n") == (True, None)
    assert Menu("empty", []).handle_input("\033[B") == (True, None)
    menu_quit_input = iter(["q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(menu_quit_input))
    assert menu._show_with_input() is None
    menu_action_input = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(menu_action_input))
    assert menu._show_with_input() == "done"

    monkeypatch.setattr("src.terminal.menu.print_animated", lambda *_args, **_kwargs: None)
    confirm_default_input = iter(["", "n"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(confirm_default_input))
    assert confirmation_dialog("Continue", default_yes=True) is True
    confirm_retry_input = iter(["bad", "yes"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(confirm_retry_input))
    assert confirmation_dialog("Continue") is True
    value_default_input = iter(["", "value"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(value_default_input))
    assert (
        input_dialog("Value", default="fallback", validation=lambda value: value == "value")
        == "value"
    )
    value_retry_input = iter(["bad", "good"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(value_retry_input))
    assert input_dialog("Value", validation=lambda value: value == "good") == "good"
