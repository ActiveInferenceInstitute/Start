# Testing Guide

This document defines the testing policy and workflows for the START project.

## Core Principles

- Real I/O, local protocol servers, and local Git repositories in tests
- No external provider or network dependency by default
- Deterministic, portable, and fast

Flow
- Developer runs `uv run pytest -q`
- Local HTTP and filesystem integration tests run in every environment
- Live provider probes require explicit credentials and an explicit invocation

## Test Structure

### Unit Tests

- Common utilities: `test_common_*.py`
- Core modules: `test_domain.py`, `test_entity.py`
- Configuration: `test_config.py`, `test_languages_config.py`
- System components: `test_system_*.py`

### Script & Integration Tests

- Curriculum entry points: `test_curriculum_entrypoints.py`
- Hardening and transactional behavior: `test_core_hardening.py`
- Full source execution coverage: `test_remaining_source.py`
- GUI behavior: `test_generate_curriculum_gui.py`
- Repository management: `test_repos_*.py`

## Running Tests

Use the gate rather than retyping a command: `uv run start-gate <arm>` runs
exactly what CI runs. See [Gate entry point](gate.md) for the arm list and
generated numbers.

```bash
# Default arm: tests not marked slow, network, or integration
uv run start-gate

# One arm at a time (each is also a CI step)
uv run start-gate fast
uv run start-gate full
uv run start-gate docs
uv run start-gate gnn
uv run start-gate artifacts

# Every arm with its exact argv
uv run start-gate --list

# Focused local runs (not gate arms)
uv run pytest -k "domain"
uv run pytest tests/test_domain.py
```

### Markers

- `@pytest.mark.integration`: end-to-end or cross-module behavior
- `@pytest.mark.slow`: long-running
- `@pytest.mark.network`: reserved for explicitly invoked external connectivity checks

## Offline-First Testing

- Use real files, temporary repositories, and local HTTP endpoints
- Prefer `tmp_path` for writable temp dirs
- Store canonical inputs/outputs under `data/domain_research`, `data/audience_research`, and the output directories

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

# Optional: keys for an explicitly invoked live provider probe
export PERPLEXITY_API_KEY="..."
export OPENROUTER_API_KEY="..."
```

## Coverage

The `full` arm enforces the 80% branch-aware working baseline and is the only
coverage pass in CI; the measurement is recorded in
[`_generated/gate-timings.md`](_generated/gate-timings.md). The manual release
workflow is fail-closed at the 90% branch-aware floor and adds the publication
output gate. Linux runs cover Python 3.11–3.12 (`fast` on 3.11, `full` on 3.12);
the macOS smoke job uses the locked Python 3.12 environment and runs the
`smoke-macos` arm.

## Repository Validation

```bash
uv run start-gate docs      # strict MkDocs build + repository validation
uv run start-gate numbers   # generated gate numbers match scripts/gate.py
```

The repository validator parses tracked JSON/YAML/TOML files, rejects duplicate
YAML keys, checks authored Markdown links, rejects references to retired
language-layout paths, and blocks project-authored terminology that would imply
non-real provider or test behavior. Generated curriculum/research snapshots and
vendored third-party artifacts are excluded from authored-text terminology
checks while remaining subject to structural config parsing when applicable.

## Best Practices

- Isolate tests; keep them small and readable
- Assert on behavior and artifacts (files, return values)
- Keep runtime low; mark slow cases with `@pytest.mark.slow`
- Avoid brittle coupling to implementation details
