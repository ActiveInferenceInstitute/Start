# Test Suite

Comprehensive test suite for the START project.

## Overview

This directory contains tests covering real file I/O, local HTTP provider
protocols, local Git repositories, pipeline failures, and error handling.

## Test Organization

Tests are organized by module:
- `test_common_*.py`: Common utilities tests
- `test_config.py`: Configuration tests
- `test_clients.py`, `test_domain.py`, `test_entity.py`, `test_openrouter_integration.py`: LLM client and local protocol tests
- `test_system_*.py`: System utilities tests
- `test_terminal_*.py`: Terminal UI tests
- `test_visualization_*.py`: Visualization tests
- `test_curriculum_*.py`: Curriculum creation tests
- `test_core_hardening.py`, `test_curriculum_entrypoints.py`, `test_remaining_source.py`: cross-module and source coverage tests

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_domain.py

# Run with markers
uv run pytest -m "not integration"
uv run pytest -m integration
```

## Test Configuration

Configuration in `pytest.ini`:
- Test discovery patterns
- Markers (integration, slow, network)
- Environment variables

## Navigation

- [AGENTS.md](AGENTS.md) - Test file reference
- [../docs/TESTING.md](../docs/TESTING.md) - Testing guide
- [../pytest.ini](../pytest.ini) - Pytest configuration
