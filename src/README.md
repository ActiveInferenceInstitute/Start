# Core System Modules

This directory contains the core system implementation modules for the START project.

## Module Organization

### `common/`
Shared utilities used across the entire project:
- File I/O operations (JSON, text)
- Path management and repository root detection
- Logging configuration
- Environment variable loading
- Configuration file loading (YAML, Markdown)
- Prompt template management

### `config/`
Configuration loading, stable-identifier policy, and validation:
- `catalog.py`: Domain/entity/language catalogs with stable IDs
- `schemas.py`: Typed validation and stable-identifier normalization
- `languages.py`: Language configuration loading

### `pipeline/`
Canonical orchestration layer — the typed, resumable runner behind the
`start-curriculum` entry point:
- `runner.py`: acquire → prepare → process → parse → render orchestrator
- `stages.py`, `contracts.py`: stage/item contracts with transactional
  failure reporting and early-stop semantics
- `manifest.py`, `artifacts.py`, `provenance.py`: run manifests, published
  artifact records, and evidence-status metadata
- `quality.py`, `parsers.py`, `usage.py`, `history.py`, `schemas.py`:
  quality gates, fence-aware parsing, usage/cost normalization, run history,
  and pipeline schemas

### `perplexity/`
LLM API integration modules:
- **Perplexity API**: Real-time research and domain analysis
- **OpenRouter API**: Content generation, curriculum creation, and translation
- Client builders and configuration
- Domain and entity research functions
- Curriculum generation and validation
- Translation utilities

### `repos/`
Repository cloning and management:
- Repository information and status tracking
- Cloning operations with progress tracking
- Repository manager interface
- Cleanup utilities

### `system/`
System utilities and diagnostics:
- System information reporting
- Dependency checking and validation
- Environment setup and validation
- Health checks

### `terminal/`
Terminal UI utilities:
- Matrix-style animations and effects
- Interactive menu system
- Color and styling utilities
- Dialog functions

### `visualization/`
Visualization utilities:
- Curriculum metrics collection
- Chart and diagram generation
- Data analysis functions

## Usage

Import modules using the `src.` prefix:

```python
from src.common.io import read_text, write_json
from src.common.paths import repo_root, data_root
from src.perplexity.clients import build_perplexity_client
from src.system.reporting import generate_system_report
```

## Dependencies

All modules depend on `src/common/` for shared utilities. External dependencies are managed via `pyproject.toml` and `uv.lock`.

## Navigation

- [AGENTS.md](AGENTS.md) - Technical reference for all modules
- [common/README.md](common/README.md) - Shared utilities
- [config/README.md](config/README.md) - Configuration system
- [perplexity/README.md](perplexity/README.md) - LLM API integrations
- [repos/README.md](repos/README.md) - Repository management
- [system/README.md](system/README.md) - System utilities
- [terminal/README.md](terminal/README.md) - Terminal UI
- [visualization/README.md](visualization/README.md) - Visualization utilities
