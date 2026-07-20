from __future__ import annotations

import pytest

from src.config.languages import get_script_mapping, get_target_languages


def test_configured_languages_are_loaded() -> None:
    languages = get_target_languages()
    assert languages
    assert "Spanish" in languages
    assert get_script_mapping("Arabic") == "Modern Standard Arabic"


def test_empty_language_configuration_is_invalid() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        get_target_languages({"target_languages": []})


def test_language_configuration_rejects_duplicates_and_bad_mappings() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        get_target_languages({"target_languages": ["Spanish", "spanish"]})
    with pytest.raises(ValueError, match="mapping"):
        get_script_mapping("Spanish", {"target_languages": ["Spanish"], "script_mappings": []})
