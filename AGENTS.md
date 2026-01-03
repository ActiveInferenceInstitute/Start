# Repository-Level Technical Reference

## Overview

This document provides technical documentation for repository-level entry points, scripts, and main functions.

## Entry Point Scripts

### `run.sh`
**Purpose**: Main interactive terminal UI for the START project

**Functions**:
- `main()`: Main execution flow with menu loop
- `show_main_menu()`: Displays main menu with options
- `system_health_check()`: Runs comprehensive system diagnostics
- `environment_setup()`: Sets up development environment
- `run_curriculum_generator()`: Launches interactive curriculum generator
- `repo_management()`: Manages repository cloning operations
- `dramatic_exit()`: Handles graceful exit with animations
- `boot_sequence()`: Displays boot animation sequence
- `check_dependencies()`: Validates required system commands
- `ensure_project_root()`: Ensures script runs from project root

**Dependencies**: Python 3, git, curl, uv package manager

### `run_docs.sh`
**Purpose**: Build, serve, and deploy documentation website

**Functions**:
- `open_browser(url)`: Opens URL in default browser
- `is_port_in_use(port)`: Checks if TCP port is in use
- `find_free_port(start_port)`: Finds next available port
- `select_runner()`: Selects mkdocs runner (uvx/mkdocs/uv)

**Modes**:
- `--serve`: Serve documentation with live reload
- `--build`: Build static site
- `--deploy`: Deploy to GitHub Pages

**Environment Variables**:
- `DOCS_ADDRESS`: Server address (default: 127.0.0.1)
- `DOCS_PORT`: Server port (default: 8000)
- `NO_OPEN`: Disable auto-opening browser
- `CI`: Disable auto-open in CI environments

## Configuration Files

### `pyproject.toml`
Project configuration including dependencies, build settings, and metadata.

### `pytest.ini`
Pytest configuration for test discovery and execution.

### `mkdocs.yml`
MkDocs configuration for documentation site structure and theming.

### `uv.lock`
Lock file for dependency versions managed by uv.

## Main Directories

- `src/`: Core system implementation modules
- `learning/`: Curriculum creation scripts and workflows
- `data/`: Generated content and configuration files
- `docs/`: Documentation files
- `tests/`: Test suite
- `examples/`: Example files and demonstrations

## Cross-References

- [README.md](README.md) - User-facing project overview
- [docs/README.md](docs/README.md) - Documentation hub
- [learning/curriculum_creation/README.md](learning/curriculum_creation/README.md) - Curriculum creation guide
- [src/AGENTS.md](src/AGENTS.md) - Source code technical reference
