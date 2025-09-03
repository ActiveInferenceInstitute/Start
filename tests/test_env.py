"""Tests for the environment utilities module."""

from __future__ import annotations

import os

import pytest

from src.common.env import load_project_env, require_env


def test_require_env_exists(monkeypatch):
    """Test requiring an environment variable that exists."""
    monkeypatch.setenv("TEST_ENV_VAR", "test_value")
    result = require_env("TEST_ENV_VAR")
    assert result == "test_value"


def test_require_env_missing():
    """Test requiring an environment variable that doesn't exist."""
    with pytest.raises(
        EnvironmentError, match="Missing required environment variable: MISSING_VAR"
    ):
        require_env("MISSING_VAR")


def test_load_project_env_with_explicit_path(tmp_path, monkeypatch):
    """Test loading environment from explicit path."""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_PROJECT_VAR=explicit_value\n", encoding="utf-8")

    # Clear any existing value
    if "TEST_PROJECT_VAR" in os.environ:
        del os.environ["TEST_PROJECT_VAR"]

    load_project_env(env_file)
    assert os.getenv("TEST_PROJECT_VAR") == "explicit_value"


def test_load_project_env_finds_dotenv(tmp_path, monkeypatch):
    """Test loading environment from automatically found .env file."""
    # Create .env file in tmp_path
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_AUTO_VAR=auto_value\n", encoding="utf-8")

    # Clear any existing value
    if "TEST_AUTO_VAR" in os.environ:
        del os.environ["TEST_AUTO_VAR"]

    # Change to tmp_path directory
    monkeypatch.chdir(tmp_path)

    load_project_env()
    assert os.getenv("TEST_AUTO_VAR") == "auto_value"


def test_load_project_env_no_file():
    """Test loading environment when no .env file exists."""
    # This should not raise an error, just do nothing
    original_env_size = len(os.environ)
    load_project_env("/nonexistent/path/.env")
    # Environment should be unchanged
    assert len(os.environ) == original_env_size


def test_load_project_env_override_false(tmp_path):
    """Test that load_project_env doesn't override existing environment variables."""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_OVERRIDE_VAR=from_file\n", encoding="utf-8")

    # Set environment variable before loading
    os.environ["TEST_OVERRIDE_VAR"] = "from_env"

    load_project_env(env_file)
    # Should keep the original value (override=False is default)
    assert os.getenv("TEST_OVERRIDE_VAR") == "from_env"

    # Clean up
    del os.environ["TEST_OVERRIDE_VAR"]
