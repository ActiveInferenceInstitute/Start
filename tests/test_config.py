"""Tests for the config loader module."""

from __future__ import annotations

import pytest
import yaml

from src.common.config import (
    load_config,
    load_markdown_config,
    load_yaml_config,
    save_yaml_config,
)


def test_save_and_load_yaml_config(tmp_path, monkeypatch):
    """Test saving and loading YAML configuration."""

    def mock_data_root():
        return tmp_path

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    # Save config
    config_data = {
        "target_languages": ["English", "Spanish", "French"],
        "script_mappings": {"Arabic": "Modern Standard Arabic"},
    }

    saved_path = save_yaml_config("test_config", config_data)
    assert saved_path.exists()
    assert saved_path.name == "test_config.yaml"

    # Load config
    loaded_data = load_yaml_config("test_config")
    assert loaded_data == config_data


def test_load_nonexistent_yaml_config(tmp_path, monkeypatch):
    """Test loading a YAML config that doesn't exist."""

    def mock_data_root():
        return tmp_path

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    with pytest.raises(FileNotFoundError):
        load_yaml_config("nonexistent")


def test_load_markdown_config(tmp_path, monkeypatch):
    """Test loading Markdown config with YAML frontmatter."""

    def mock_data_root():
        return tmp_path

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    # Create config directory and file
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)

    config_content = """---
target_languages:
  - English
  - Spanish
  - French
script_mappings:
  Arabic: "Modern Standard Arabic"
---

# Configuration Documentation

This is the configuration for languages.
"""

    config_file = config_dir / "test_config.md"
    config_file.write_text(config_content, encoding="utf-8")

    # Load config
    loaded_data = load_markdown_config("test_config")
    expected = {
        "target_languages": ["English", "Spanish", "French"],
        "script_mappings": {"Arabic": "Modern Standard Arabic"},
    }
    assert loaded_data == expected


def test_load_markdown_config_no_frontmatter(tmp_path, monkeypatch):
    """Test loading Markdown config without YAML frontmatter."""

    def mock_data_root():
        return tmp_path

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    # Create config directory and file without frontmatter
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)

    config_content = "# Just a regular markdown file\n\nNo frontmatter here."
    config_file = config_dir / "test_config.md"
    config_file.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="No YAML frontmatter found"):
        load_markdown_config("test_config")


def test_load_markdown_config_invalid_yaml(tmp_path, monkeypatch):
    """Test loading Markdown config with invalid YAML frontmatter."""

    def mock_data_root():
        return tmp_path

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    # Create config directory and file with invalid YAML
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)

    config_content = """---
invalid: yaml: content: [
---

# Configuration
"""

    config_file = config_dir / "test_config.md"
    config_file.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid YAML frontmatter"):
        load_markdown_config("test_config")


def test_load_config_prefer_yaml(tmp_path, monkeypatch):
    """Test load_config preferring YAML over Markdown."""

    def mock_data_root():
        return tmp_path

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    # Create both YAML and Markdown configs
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)

    yaml_data = {"source": "yaml", "value": 1}
    md_data = {"source": "markdown", "value": 2}

    # Save YAML config
    yaml_file = config_dir / "test_config.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(yaml_data, f)

    # Save Markdown config
    md_content = f"---\n{yaml.safe_dump(md_data)}---\n\n# Config"
    md_file = config_dir / "test_config.md"
    md_file.write_text(md_content, encoding="utf-8")

    # Should prefer YAML by default
    loaded_data = load_config("test_config")
    assert loaded_data == yaml_data

    # Should prefer Markdown when specified
    loaded_data = load_config("test_config", prefer_yaml=False)
    assert loaded_data == md_data


def test_load_config_fallback_to_markdown(tmp_path, monkeypatch):
    """Test load_config falling back to Markdown when YAML doesn't exist."""

    def mock_data_root():
        return tmp_path

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    # Create only Markdown config
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)

    md_data = {"source": "markdown", "value": 2}
    md_content = f"---\n{yaml.safe_dump(md_data)}---\n\n# Config"
    md_file = config_dir / "test_config.md"
    md_file.write_text(md_content, encoding="utf-8")

    # Should fallback to Markdown
    loaded_data = load_config("test_config")
    assert loaded_data == md_data


def test_load_config_no_files(tmp_path, monkeypatch):
    """Test load_config when neither YAML nor Markdown exists."""

    def mock_data_root():
        return tmp_path

    import src.common.config

    monkeypatch.setattr(src.common.config, "data_root", mock_data_root)

    with pytest.raises(FileNotFoundError, match="No config file found"):
        load_config("nonexistent")
