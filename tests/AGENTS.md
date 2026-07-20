# Test Suite Technical Reference

## Overview

Technical documentation for test files and their coverage.

## Test Files

### Common Utilities
- `test_common_io.py`: File I/O operations
- `test_paths.py`: Path management
- `test_terminal_*.py`: Terminal utilities and UI behavior
- `test_config.py`: Configuration loading

### LLM API Integration
- `test_clients.py`: API client builders
- `test_domain.py`: Domain research
- `test_entity.py`: Entity research
- `test_openrouter_integration.py`: OpenRouter integration
- `test_curriculum_generation.py`: Curriculum generation utilities

### System Utilities
- `test_system_dependencies.py`: Dependency checking
- `test_system_reporting.py`: System reporting
- `test_system_environment.py`: Environment setup

### Terminal UI
- `test_terminal_animations.py`: Animations
- `test_terminal_colors.py`: Color utilities
- `test_terminal_menu.py`: Menu system

### Visualization
- `test_visualization_runner.py`: Visualization runner

### Curriculum Creation
- `test_curriculum_entrypoints.py`: Curriculum script helpers and translation chunks
- `test_core_hardening.py`: Configuration, provider, pipeline, and transactional behavior
- `test_remaining_source.py`: Repository, system, reporting, terminal, and CLI coverage
- `test_curriculum_sections.py`: Curriculum sections
- `test_curriculum_scripts_integration.py`: Integration tests

### Repository Management
- `test_repos_cloning.py`: Repository cloning
- `test_repos_manager.py`: Repository manager
- `test_repos_cloning.py`: Clone utilities

### Integration Tests
- `test_run_script_integration.py`: Run script integration
- `test_run_script_integration.py`: Run script integration

## Test Utilities

### `conftest.py`
Pytest configuration and fixtures:
- Common fixtures
- Test setup/teardown
- Isolated temporary configurations

## Cross-References

- [README.md](README.md) - Test suite overview
- [../docs/TESTING.md](../docs/TESTING.md) - Testing guide
- [../pytest.ini](../pytest.ini) - Pytest configuration
