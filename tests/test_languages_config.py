"""Tests for the languages configuration module."""

from __future__ import annotations

from src.config.languages import (
    DEFAULT_LANGUAGES_CONFIG,
    get_script_mapping,
    get_target_languages,
    load_languages_config,
)


def test_load_languages_config_defaults(tmp_path, monkeypatch):
    """Test loading default languages config when no file exists."""

    def mock_data_root():
        return tmp_path / "nonexistent"

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    config = load_languages_config()
    assert config == DEFAULT_LANGUAGES_CONFIG


def test_load_languages_config_from_yaml(tmp_path, monkeypatch):
    """Test loading languages config from YAML file."""

    def mock_data_root():
        return tmp_path

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    # Create config directory and YAML file
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)

    yaml_content = """target_languages:
  - English
  - Spanish
  - French
script_mappings:
  Spanish: "Latin Script"
  French: "Latin Script"
"""

    yaml_file = config_dir / "languages.yaml"
    yaml_file.write_text(yaml_content, encoding="utf-8")

    config = load_languages_config()
    expected = {
        "target_languages": ["English", "Spanish", "French"],
        "script_mappings": {"Spanish": "Latin Script", "French": "Latin Script"},
    }
    assert config == expected


def test_get_target_languages_default():
    """Test getting target languages from default config."""
    languages = get_target_languages()
    assert isinstance(languages, list)
    assert "Chinese" in languages
    assert "Spanish" in languages
    assert len(languages) == len(DEFAULT_LANGUAGES_CONFIG["target_languages"])


def test_get_target_languages_custom():
    """Test getting target languages from custom config."""
    custom_config = {"target_languages": ["English", "French", "German"]}
    languages = get_target_languages(custom_config)
    assert languages == ["English", "French", "German"]


def test_get_target_languages_missing_key():
    """Test getting target languages when key is missing."""
    custom_config = {"other_key": "value"}
    languages = get_target_languages(custom_config)
    assert languages == DEFAULT_LANGUAGES_CONFIG["target_languages"]


def test_get_script_mapping_default():
    """Test getting script mapping from default config."""
    assert get_script_mapping("Chinese") == "Simplified Chinese"
    assert get_script_mapping("Arabic") == "Modern Standard Arabic"
    assert get_script_mapping("English") == "English"  # Not in mapping, returns itself


def test_get_script_mapping_custom():
    """Test getting script mapping from custom config."""
    custom_config = {
        "script_mappings": {"Spanish": "Latin Script", "Chinese": "Traditional Chinese"}
    }
    assert get_script_mapping("Spanish", custom_config) == "Latin Script"
    assert get_script_mapping("Chinese", custom_config) == "Traditional Chinese"
    assert get_script_mapping("English", custom_config) == "English"  # Not in mapping


def test_get_script_mapping_missing_key():
    """Test getting script mapping when key is missing."""
    custom_config = {"other_key": "value"}
    # Should fall back to default behavior
    assert get_script_mapping("Chinese", custom_config) == "Chinese"  # No script_mappings key
