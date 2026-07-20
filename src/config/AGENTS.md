# Configuration System Technical Reference

## Overview

Technical documentation for configuration system functions.

## Module: `languages.py`

### Functions

#### `load_languages_config() -> Dict[str, Any]`
Loads languages configuration from `data/config/languages.yaml`.

**Returns**: Dictionary containing languages configuration

**Behavior**: Raises `FileNotFoundError` when the required configuration is absent.

**Raises**: `FileNotFoundError` or `ValueError` for invalid configuration.

#### `get_target_languages(config: Optional[Dict[str, Any]] = None) -> List[str]`
Gets the list of target languages for translation.

**Parameters**:
- `config`: Optional config dictionary. If None, loads from file.

**Returns**: List of target language names

**Validation**: Requires a non-empty configured target language list.

#### `get_script_mapping(language: str, config: Optional[Dict[str, Any]] = None) -> str`
Gets the script mapping for a language.

**Parameters**:
- `language`: Language name (e.g., "Chinese", "Arabic")
- `config`: Optional config dictionary. If None, loads from file.

**Returns**: Script name for the language, or the language name itself if no mapping exists

**Examples**:
- `get_script_mapping("Chinese")` → `"Simplified Chinese"`
- `get_script_mapping("Arabic")` → `"Modern Standard Arabic"`
- `get_script_mapping("Unknown")` → `"Unknown"` (no mapping, returns input)

## Cross-References

- [README.md](README.md) - Module overview and usage
- [../common/config.py](../common/config.py) - Base configuration loading utilities
- [../../data/config/](../../data/config/) - Configuration files location
