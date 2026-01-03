# Configuration System Technical Reference

## Overview

Technical documentation for configuration system functions.

## Module: `languages.py`

### Constants

#### `DEFAULT_LANGUAGES_CONFIG: Dict[str, Any]`
Default language configuration used when config file is not found.

**Structure**:
- `target_languages`: List of language names
- `script_mappings`: Dictionary mapping language names to script names

### Functions

#### `load_languages_config() -> Dict[str, Any]`
Loads languages configuration from `data/config/languages.yaml` or `.md`.

**Returns**: Dictionary containing languages configuration

**Behavior**: Returns `DEFAULT_LANGUAGES_CONFIG` if config file not found

**Raises**: None (falls back to defaults)

#### `get_target_languages(config: Optional[Dict[str, Any]] = None) -> List[str]`
Gets the list of target languages for translation.

**Parameters**:
- `config`: Optional config dictionary. If None, loads from file.

**Returns**: List of target language names

**Default**: Returns default languages if config not provided and file not found

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
