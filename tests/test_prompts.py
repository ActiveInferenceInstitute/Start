"""Tests for the prompts loader module."""

from __future__ import annotations

import pytest

from src.common.prompts import (
    list_prompt_templates,
    load_prompt_template,
    render_prompt,
    save_prompt_template,
    substitute_variables,
)


def test_save_and_load_prompt_template(tmp_path, monkeypatch):
    """Test saving and loading prompt templates."""
    # Mock data_root to use tmp_path
    def mock_data_root():
        return tmp_path
    
    import src.common.prompts
    monkeypatch.setattr(src.common.prompts, "data_root", mock_data_root)
    
    # Save a template
    template_content = "Hello {{name}}, welcome to {{place}}!"
    saved_path = save_prompt_template("test_template", template_content)
    
    assert saved_path.exists()
    assert saved_path.name == "test_template.md"
    
    # Load the template
    loaded_content = load_prompt_template("test_template")
    assert loaded_content == template_content


def test_load_nonexistent_template(tmp_path, monkeypatch):
    """Test loading a template that doesn't exist."""
    def mock_data_root():
        return tmp_path
    
    import src.common.prompts
    monkeypatch.setattr(src.common.prompts, "data_root", mock_data_root)
    
    with pytest.raises(FileNotFoundError):
        load_prompt_template("nonexistent")


def test_substitute_variables():
    """Test variable substitution in templates."""
    template = "Hello {{name}}, welcome to {{place}}! Your age is {{age}}."
    variables = {
        "name": "Alice",
        "place": "Wonderland",
        "age": 25
    }
    
    result = substitute_variables(template, variables)
    expected = "Hello Alice, welcome to Wonderland! Your age is 25."
    assert result == expected


def test_substitute_variables_missing():
    """Test variable substitution with missing variables."""
    template = "Hello {{name}}, welcome to {{place}}!"
    variables = {"name": "Alice"}  # missing "place"
    
    result = substitute_variables(template, variables)
    expected = "Hello Alice, welcome to {{place}}!"  # missing var unchanged
    assert result == expected


def test_substitute_variables_whitespace():
    """Test variable substitution with whitespace in placeholders."""
    template = "Hello {{ name }}, welcome to {{  place  }}!"
    variables = {"name": "Alice", "place": "Wonderland"}
    
    result = substitute_variables(template, variables)
    expected = "Hello Alice, welcome to Wonderland!"
    assert result == expected


def test_render_prompt(tmp_path, monkeypatch):
    """Test rendering a prompt with variables."""
    def mock_data_root():
        return tmp_path
    
    import src.common.prompts
    monkeypatch.setattr(src.common.prompts, "data_root", mock_data_root)
    
    # Save a template
    template_content = "Research Task: {{task}}\n\nData: {{data}}"
    save_prompt_template("research", template_content)
    
    # Render with variables
    variables = {"task": "Analyze domain", "data": "Sample data"}
    result = render_prompt("research", variables)
    expected = "Research Task: Analyze domain\n\nData: Sample data"
    assert result == expected


def test_render_prompt_no_variables(tmp_path, monkeypatch):
    """Test rendering a prompt without variables."""
    def mock_data_root():
        return tmp_path
    
    import src.common.prompts
    monkeypatch.setattr(src.common.prompts, "data_root", mock_data_root)
    
    # Save a template without variables
    template_content = "Static prompt content"
    save_prompt_template("static", template_content)
    
    # Render without variables
    result = render_prompt("static")
    assert result == template_content


def test_list_prompt_templates(tmp_path, monkeypatch):
    """Test listing available prompt templates."""
    def mock_data_root():
        return tmp_path
    
    import src.common.prompts
    monkeypatch.setattr(src.common.prompts, "data_root", mock_data_root)
    
    # Initially empty
    assert list_prompt_templates() == []
    
    # Add some templates
    save_prompt_template("template1", "Content 1")
    save_prompt_template("template2", "Content 2")
    save_prompt_template("template3", "Content 3")
    
    templates = list_prompt_templates()
    assert set(templates) == {"template1", "template2", "template3"}


def test_list_prompt_templates_no_dir(tmp_path, monkeypatch):
    """Test listing templates when prompts directory doesn't exist."""
    def mock_data_root():
        return tmp_path / "nonexistent"
    
    import src.common.prompts
    monkeypatch.setattr(src.common.prompts, "data_root", mock_data_root)
    
    assert list_prompt_templates() == []
