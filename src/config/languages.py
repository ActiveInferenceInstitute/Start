"""Languages configuration loader using YAML/Markdown config files."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.common.config import load_config
from src.config.schemas import validate_languages_config


def load_languages_config() -> Dict[str, Any]:
    """Load languages configuration from data/config/languages.yaml or .md.

    Returns:
        Dictionary containing the languages configuration
    """
    config = load_config("languages")
    validate_languages_config(config)
    return config


def get_target_languages(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """Get the list of target languages for translation.

    Args:
        config: Optional config dict, loads from file if not provided

    Returns:
        List of target language names
    """
    cfg = load_languages_config() if config is None else config
    # Use the typed schema as the single source of truth. It accepts both the
    # scalar form and the richer {name, script} form while this helper returns
    # display names.
    return [language.name for language in validate_languages_config(cfg)]


def get_script_mapping(language: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Get the script mapping for a language.

    Args:
        language: Language name
        config: Optional config dict, loads from file if not provided

    Returns:
        Script name for the language, or the language name if no mapping exists
    """
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a non-empty string")
    cfg = load_languages_config() if config is None else config
    mappings = cfg.get("script_mappings", {})
    if not isinstance(mappings, dict):
        raise ValueError("Language script_mappings must be a mapping")
    return mappings.get(language, language)
