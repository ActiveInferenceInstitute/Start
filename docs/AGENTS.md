# Documentation Structure Technical Reference

## Overview

Technical documentation for the documentation directory structure and organization.

## Documentation files

- `README.md`, `index.md`, and `documentation-index.md` are the entry points.
- `guides/` contains installation, examples, clone workflows and learning guides.
- `architecture/` contains pipeline, methods, provenance and output contracts.
- `reference/` contains environment, configuration, API integration and FAQ.
- `development/` contains operations, verification, contribution and release guidance.
- `manuscript/` contains the numbered paper source and pinned Template render instructions.
- `other/` contains additional documentation resources.
- `_generated/` contains gate timings written by `uv run start-gate measure` and
  checked by `uv run start-gate numbers`.

## Documentation Build

Documentation is built using MkDocs:
- Configuration: `mkdocs.yml` (root)
- Build script: `run_docs.sh` (root)
- Output: `site/` directory (generated)

## Navigation Structure

Documentation follows hierarchical structure:
1. Hub pages (README.md, index.md)
2. Getting started guides
3. Technical references
4. Advanced topics

## Cross-References

- [README.md](README.md) - Documentation hub
- [../README.md](../README.md) - Project overview
- [../mkdocs.yml](../mkdocs.yml) - MkDocs configuration
