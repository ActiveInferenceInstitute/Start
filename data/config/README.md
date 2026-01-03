# Configuration Files

YAML configuration files for domains, entities, and languages.

## Overview

This directory contains configuration files that define research targets, translation languages, and system settings.

## Files

### `domains.yaml`
Domain definitions for domain research:
- Domain names
- Categories
- Priority levels

### `entities.yaml`
Entity/audience definitions for audience research:
- Entity names
- Descriptions
- Categories
- Priority levels

### `languages.yaml`
Language configuration for translations:
- Target languages list
- Script mappings for different writing systems

## Usage

Configuration files are loaded by:
- `src/common/config.py::load_yaml_config()`
- `src/config/languages.py::load_languages_config()`

## Navigation

- [AGENTS.md](AGENTS.md) - Configuration schema reference
- [../README.md](../README.md) - Data directory overview
- [../../src/config/](../../src/config/) - Configuration system
