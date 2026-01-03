# Configuration System

Configuration utilities for language settings and script mappings.

## Overview

This module provides functions to load and access language configuration data, including target languages for translation and script mappings for different writing systems.

## Configuration File

Language configuration is stored in `data/config/languages.yaml` (or `languages.md` with YAML frontmatter).

### Default Configuration

If no configuration file exists, the module uses a default configuration with:
- 11 target languages (Chinese, Spanish, Arabic, Hindi, French, Japanese, German, Russian, Portuguese, Swahili, Tagalog)
- Script mappings for various languages and writing systems

## Usage

```python
from src.config.languages import (
    load_languages_config,
    get_target_languages,
    get_script_mapping
)

# Load full configuration
config = load_languages_config()

# Get list of target languages
languages = get_target_languages()

# Get script mapping for a language
script = get_script_mapping("Chinese")  # Returns "Simplified Chinese"
```

## Configuration Structure

```yaml
target_languages:
  - Chinese
  - Spanish
  - Arabic
  # ... more languages

script_mappings:
  Arabic: "Modern Standard Arabic"
  Chinese: "Simplified Chinese"
  # ... more mappings
```

## Navigation

- [AGENTS.md](AGENTS.md) - Complete function reference
- [../README.md](../README.md) - Source code overview
- [../../data/config/](../../data/config/) - Configuration files
