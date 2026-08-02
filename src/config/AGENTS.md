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

## Module: `schemas.py`

Typed configuration validation and the stable-identifier policy.

### Functions

#### `stable_identifier(value: str) -> str`
Normalizes a display name into a stable identifier (lowercase, spaces and
punctuation collapsed to underscores).

#### `validate_domains_config(config, *, require_provenance=False) -> list[DomainConfig]`
Validates the `domains` list and returns typed records with stable IDs.
Duplicate IDs are rejected. With `require_provenance=True`, every domain must
carry `source_urls` and an ISO `verification_date` (publication mode).

#### `validate_entities_config(config, *, require_provenance=False) -> list[EntityConfig]`
Validates the `entities` list with the same contract as domains.

#### `add_stable_ids(config, name) -> dict`
Adds stable IDs to raw config entries before further processing.

## Module: `catalog.py`

Configuration catalogs used by the CLI, GUI, and pipeline.

### Functions

#### `load_domains_config() -> dict`
Loads and validates `data/config/domains.yaml`, returning display-name-keyed
entries with stable IDs.

#### `load_entities_config() -> dict`
Loads and validates `data/config/entities.yaml`, returning display-name-keyed
entries with stable IDs.

#### `domains_to_process(...)` / `entities_to_process(...)`
Filters configured items by priority/category for staged processing.

#### `output_exists(...)`
Checks whether an output already exists for an item without raising on odd
display names.

## Cross-References

- [README.md](README.md) - Module overview and usage
- [../common/config.py](../common/config.py) - Base configuration loading utilities
- [../../data/config/](../../data/config/) - Configuration files location
