from __future__ import annotations

import pytest

from src.common.prompts import (
    list_prompt_templates,
    render_prompt,
    save_prompt_template,
    substitute_variables,
    validate_prompt_template,
)


def test_prompt_templates_are_loadable() -> None:
    names = list_prompt_templates()
    assert names
    assert render_prompt(names[0])


def test_prompt_substitution_and_strict_validation() -> None:
    assert substitute_variables("Hello {{ name }}", {"name": "Ada"}) == "Hello Ada"
    with pytest.raises(ValueError, match="Missing"):
        substitute_variables("{{missing}}", {}, strict=True)
    assert validate_prompt_template("Hello {{name}}")["valid"] is True


def test_prompt_paths_and_persistence(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("src.common.prompts.data_root", lambda: tmp_path)
    saved = save_prompt_template("local", "Hello {{name}}")
    assert saved.read_text(encoding="utf-8") == "Hello {{name}}"
    assert render_prompt("local", {"name": "reader"}) == "Hello reader"
    with pytest.raises(ValueError, match="Invalid prompt"):
        save_prompt_template("../unsafe", "text")
