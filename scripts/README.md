# scripts/

Repository-level maintenance and validation entry points. These modules are
installed as console scripts (see `[project.scripts]` in `pyproject.toml`), so
each can be run through the locked environment without editing `sys.path`.

## Contents

| File | Console command | Purpose |
| --- | --- | --- |
| `validate_repository.py` | `uv run python scripts/validate_repository.py` | Validate tracked config files (JSON/YAML/TOML), authored terminology, stale paths, and Markdown links. This is the CI repository gate. |
| `validate_outputs.py` | `start-validate-outputs` | Validate generated research, curriculum, translation, and manifest outputs and their contracts. |
| `audit_artifacts.py` | `start-audit-artifacts` | Non-destructive inventory of generated artifacts; reports provenance gaps and duplicate-content groups. |
| `curate_artifacts.py` | `start-curate-artifacts` | Plan-first, allow-list-based curation of generated artifacts; re-verifies hashes before any mutation. |
| `regenerate_offline_fixtures.py` | `start-regenerate-offline` | Regenerate deterministic, explicitly synthetic pipeline fixtures. |
| `run_history.py` | `start-run-history` | Inspect and conservatively prune filesystem-backed run history. |
| `__init__.py` | — | Marks `scripts/` as a package for the hatch wheel. |

## Usage

```bash
# Repository configuration and link gate (CI)
uv run python scripts/validate_repository.py

# Installed console entry points (equivalents above)
uv run start-validate-outputs --check
uv run start-audit-artifacts --check --baseline data/artifact-manifests/current.json
uv run start-regenerate-offline --output-dir /tmp/start-fixtures --json
uv run start-run-history --help
```

All scripts are read-only unless a curation/prune subcommand explicitly opts in;
see each module's docstring and the root [AGENTS.md](../AGENTS.md) stable-commands
list. Backlog items that touch these scripts live in [`../TODO.md`](../TODO.md).
