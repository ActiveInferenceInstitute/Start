"""Languages configuration loader using YAML/Markdown config files."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.common.config import load_config

DEFAULT_LANGUAGES_CONFIG = {
    "target_languages": [
        "Chinese", "Spanish", "Arabic", "Hindi", "French", "Japanese", "German",
        "Russian", "Portuguese", "Swahili", "Tagalog"
    ],
    "script_mappings": {
        "Arabic": "Modern Standard Arabic",
        "Chinese": "Simplified Chinese",
        "Kurdish": "Sorani",
        "Mongolian": "Cyrillic",
        "Persian": "Farsi",
        "Serbian": "Latin",
        "Chinese_Traditional": "Traditional Chinese",
        "Japanese": "Standard Japanese",
        "Korean": "Hangul",
        "Urdu": "Nastaliq",
        "Hindi": "Devanagari",
        "Bengali": "Bengali Script",
        "Thai": "Thai Script",
        "Hebrew": "Hebrew Script",
        "Georgian": "Mkhedruli",
        "Armenian": "Armenian Script",
        "Greek": "Greek Script",
        "Khmer": "Khmer Script",
        "Lao": "Lao Script",
        "Myanmar": "Myanmar Script",
        "Sinhala": "Sinhala Script",
        "Tamil": "Tamil Script",
        "Telugu": "Telugu Script",
        "Gujarati": "Gujarati Script",
        "Kannada": "Kannada Script",
        "Malayalam": "Malayalam Script",
        "Tibetan": "Tibetan Script",
        "Yiddish": "Hebrew Script",
        "Sanskrit": "Devanagari"
    }
}


def load_languages_config() -> Dict[str, Any]:
    """Load languages configuration from data/config/languages.yaml or .md.
    
    Returns:
        Dictionary containing the languages configuration
    """
    try:
        return load_config("languages")
    except FileNotFoundError:
        return DEFAULT_LANGUAGES_CONFIG


def get_target_languages(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """Get the list of target languages for translation.
    
    Args:
        config: Optional config dict, loads from file if not provided
        
    Returns:
        List of target language names
    """
    cfg = config or load_languages_config()
    return cfg.get("target_languages", DEFAULT_LANGUAGES_CONFIG["target_languages"])


def get_script_mapping(language: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Get the script mapping for a language.
    
    Args:
        language: Language name
        config: Optional config dict, loads from file if not provided
        
    Returns:
        Script name for the language, or the language name if no mapping exists
    """
    cfg = config or load_languages_config()
    return cfg.get("script_mappings", {}).get(language, language)