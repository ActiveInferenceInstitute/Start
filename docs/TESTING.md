# Testing Guide

This document defines the testing policy and workflows for the START project.

## Core Principles

- Real I/O, no stubs or fakes in tests
- No network by default; allow network only if CI=true
- Deterministic, portable, and fast

```mermaid
sequenceDiagram
  participant Dev as Developer
  participant Py as pytest
  participant Off as Offline tests
  participant Net as Network tests
  Dev->>Py: uv run pytest -q
  Py->>Off: Run (always)
  alt CI=true and network enabled
    Py->>Net: Run @network tests
  else
    Py-->>Dev: Skip @network tests
  end
```

## Test Structure

### Unit Tests

- Common utilities: `test_common_*.py`
- Core modules: `test_domain.py`, `test_entity.py`
- Configuration: `test_config.py`, `test_languages_config.py`
- System components: `test_system_*.py`

### Script & Integration Tests

- Research scripts: `test_1_research_domain.py`, `test_2_write_introduction.py`
- Visualization scripts: `test_3_introduction_visualizations.py`
- Translation scripts: `test_4_translate_introductions.py`
- End-to-end: `test_integration.py`
- Repo management: `test_repos_*.py`

## Running Tests

```bash
# Full suite
uv run pytest -q

# Verbose / coverage
uv run pytest -v
uv run pytest --cov=src --cov-report=html

# Focused runs
uv run pytest -k "domain"
uv run pytest tests/test_domain.py
```

### Markers

- `@pytest.mark.integration`: end-to-end or cross-module behavior
- `@pytest.mark.slow`: long-running
- `@pytest.mark.network`: requires external network/APIs

Gate network tests behind CI:

```python
import os
import pytest

RUN_NETWORK = os.getenv("CI") == "true"


network = pytest.mark.network


def skip_network_if_disallowed():
    if not RUN_NETWORK:
        pytest.skip("Network tests disabled outside CI")


@network
def test_network_feature():
    skip_network_if_disallowed()
    # real network call here
```

## Offline-First Testing

- Use real files and fixtures; avoid mocks
- Prefer `tmp_path` for writable temp dirs
- Store canonical inputs/outputs under `data/Languages/Inputs_and_Outputs/**` as allowed by policy

```python
def test_file_processing(tmp_path):
    source = tmp_path / "input.json"
    source.write_text('{"a": 1}')
    result = process_file(source)
    assert result["a"] == 1
```

## Environment Setup for Tests

```bash
# Non-GUI matplotlib backend
export MPLBACKEND=Agg

# Optional: keys for CI network tests
export PERPLEXITY_API_KEY="..."
export OPENROUTER_API_KEY="..."
```

## Coverage

```bash
uv run pytest --cov=src --cov-report=html
```

## Best Practices

- Isolate tests; keep them small and readable
- Assert on behavior and artifacts (files, return values)
- Keep runtime low; mark slow cases with `@pytest.mark.slow`
- Avoid brittle coupling to implementation details
