# Source Code Technical Reference

## Overview

Technical documentation for all modules in the `src/` directory.

## Module Structure

### `common/`
**Purpose**: Shared utilities and helper functions

**Key Modules**:
- `io.py`: File I/O operations
- `paths.py`: Path management and directory resolution
- `logging_utils.py`: Logging configuration
- `env.py`: Environment variable management
- `config.py`: Configuration file loading
- `prompts.py`: Prompt template management

**See**: [common/AGENTS.md](common/AGENTS.md) for detailed function reference

### `config/`
**Purpose**: Configuration system for languages and script mappings

**Key Modules**:
- `languages.py`: Language configuration loading and validation

**See**: [config/AGENTS.md](config/AGENTS.md) for detailed function reference

### `perplexity/`
**Purpose**: LLM API integrations for research and content generation

**Key Modules**:
- `clients.py`: API client builders (Perplexity, OpenRouter)
- `domain.py`: Domain research and analysis
- `entity.py`: Entity/audience research
- `curriculum.py`: Curriculum generation and validation
- `translation.py`: Multilingual translation utilities

**See**: [perplexity/AGENTS.md](perplexity/AGENTS.md) for detailed function reference

### `repos/`
**Purpose**: Repository cloning and management

**Key Modules**:
- `manager.py`: High-level repository management interface
- `cloning.py`: Repository cloning operations
- `clone_repo.py`: Low-level git cloning utilities

**See**: [repos/AGENTS.md](repos/AGENTS.md) for detailed function reference

### `system/`
**Purpose**: System utilities, diagnostics, and environment management

**Key Modules**:
- `reporting.py`: System information gathering and reporting
- `dependencies.py`: Dependency checking and validation
- `environment.py`: Environment setup and validation

**See**: [system/AGENTS.md](system/AGENTS.md) for detailed function reference

### `terminal/`
**Purpose**: Terminal UI utilities and animations

**Key Modules**:
- `menu.py`: Interactive menu system
- `colors.py`: Color and styling utilities
- `animations.py`: Matrix-style animations and effects

**See**: [terminal/AGENTS.md](terminal/AGENTS.md) for detailed function reference

### `visualization/`
**Purpose**: Visualization and metrics generation

**Key Modules**:
- `runner.py`: Curriculum metrics collection and generation

**See**: [visualization/AGENTS.md](visualization/AGENTS.md) for detailed function reference

## Cross-References

- [README.md](README.md) - Module overview and usage
- [../README.md](../README.md) - Project overview
- [../docs/README.md](../docs/README.md) - Documentation hub
