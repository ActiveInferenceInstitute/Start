"""Configuration loaders for YAML and Markdown config files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from src.common.io import read_text
from src.common.paths import data_root


def config_dir() -> Path:
    """Return the config directory under data/."""
    return data_root() / "config"


def load_yaml_config(name: str) -> Dict[str, Any]:
    """Load a YAML configuration file from data/config/{name}.yaml.

    Args:
        name: Name of the config file (without .yaml extension)

    Returns:
        Dictionary containing the configuration data

    Raises:
        FileNotFoundError: If the config file doesn't exist
        yaml.YAMLError: If the YAML is invalid
    """
    config_path = config_dir() / f"{name}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    content = read_text(config_path)
    return yaml.safe_load(content)


def load_markdown_config(name: str) -> Dict[str, Any]:
    """Load a Markdown configuration file from data/config/{name}.md.

    Expects YAML frontmatter between --- delimiters at the start of the file.

    Args:
        name: Name of the config file (without .md extension)

    Returns:
        Dictionary containing the configuration data from frontmatter

    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If no valid YAML frontmatter is found
    """
    config_path = config_dir() / f"{name}.md"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    content = read_text(config_path)

    # Extract YAML frontmatter
    if not content.startswith("---\n"):
        raise ValueError(f"No YAML frontmatter found in {config_path}")

    try:
        # Find the closing ---
        end_marker = content.find("\n---\n", 4)
        if end_marker == -1:
            raise ValueError(f"No closing --- found in YAML frontmatter in {config_path}")

        frontmatter = content[4:end_marker]
        return yaml.safe_load(frontmatter)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter in {config_path}: {e}")


def validate_config_data(data: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Validate loaded configuration data.

    Args:
        data: Configuration data to validate
        name: Configuration name for error messages

    Returns:
        Validated configuration data

    Raises:
        ValueError: If configuration is invalid
    """
    if not isinstance(data, dict):
        raise ValueError(f"Configuration '{name}' must be a dictionary, got {type(data)}")

    if not data:
        raise ValueError(f"Configuration '{name}' is empty")

    # Check for common configuration issues
    for key, value in data.items():
        if not isinstance(key, str):
            raise ValueError(f"Configuration key must be string, got {type(key)}: {key}")

        # Warn about None values in configuration
        if value is None:
            print(f"Warning: Configuration '{name}' has None value for key: {key}")

    return data


def load_config(name: str, prefer_yaml: bool = True, validate: bool = True) -> Dict[str, Any]:
    """Load configuration, trying YAML first, then Markdown fallback.

    Args:
        name: Name of the config file (without extension)
        prefer_yaml: If True, try YAML first, then Markdown. If False, reverse order.
        validate: If True, validate the loaded configuration

    Returns:
        Dictionary containing the configuration data

    Raises:
        FileNotFoundError: If neither YAML nor Markdown config exists
        ValueError: If configuration is invalid and validate=True
    """
    if not name or not name.strip():
        raise ValueError("Configuration name cannot be empty")

    name = name.strip()
    loaders = [load_yaml_config, load_markdown_config]
    if not prefer_yaml:
        loaders.reverse()

    last_error = None
    for loader in loaders:
        try:
            config_data = loader(name)
            if validate:
                config_data = validate_config_data(config_data, name)
            return config_data
        except FileNotFoundError as e:
            last_error = e
            continue
        except Exception as e:
            # If we get a parsing/validation error, try the next loader
            last_error = e
            continue

    # If we get here, no configuration could be loaded
    config_path = config_dir()
    if isinstance(last_error, FileNotFoundError):
        raise FileNotFoundError(
            f"No config file found for '{name}' in {config_path} "
            f"(tried {name}.yaml and {name}.md)"
        )
    else:
        raise ValueError(
            f"Failed to load configuration '{name}': {str(last_error)}"
        ) from last_error


def save_yaml_config(name: str, data: Dict[str, Any]) -> Path:
    """Save configuration data as YAML to data/config/{name}.yaml.

    Args:
        name: Name of the config file (without .yaml extension)
        data: Configuration data to save

    Returns:
        Path to the saved config file
    """
    config_dir().mkdir(parents=True, exist_ok=True)
    config_path = config_dir() / f"{name}.yaml"

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    return config_path
