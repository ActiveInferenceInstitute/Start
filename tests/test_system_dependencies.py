from __future__ import annotations

from src.system.dependencies import (
    check_python_package,
    get_required_python_packages,
    validate_api_keys,
)


def test_required_packages_are_derived_from_project_metadata() -> None:
    packages = get_required_python_packages()
    assert "dotenv" in packages
    assert "yaml" in packages
    assert "git" in packages
    assert "plotly" not in packages


def test_package_check_reports_real_imports() -> None:
    result = check_python_package("json")
    assert result.available is True
    assert result.name == "json"


def test_api_key_validation_is_presence_only(monkeypatch) -> None:
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "configured")
    assert validate_api_keys() == {"perplexity": False, "openrouter": True}
