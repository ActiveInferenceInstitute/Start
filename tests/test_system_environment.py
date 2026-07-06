"""Tests for the environment setup and validation module.

Uses tmp_path for filesystem operations and monkeypatch for env vars.
No mocks, no network — purely deterministic tests.
"""

from __future__ import annotations

import sys

from src.system.environment import (
    create_default_domains_config,
    create_default_entities_config,
    create_default_languages_config,
    create_env_template,
    fix_common_issues,
    get_environment_info,
    validate_environment,
)


class TestCreateEnvTemplate:
    """Tests for create_env_template function."""

    def test_creates_file(self, tmp_path, monkeypatch):
        """Test that .env template file is created."""
        monkeypatch.setattr("src.system.environment.repo_root", lambda: tmp_path)
        result = create_env_template()
        assert result == tmp_path / ".env"
        assert result.exists()
        content = result.read_text()
        assert "PERPLEXITY_API_KEY" in content
        assert "OPENROUTER_API_KEY" in content

    def test_contains_api_keys(self, tmp_path, monkeypatch):
        """Test that .env template contains API key sections."""
        monkeypatch.setattr("src.system.environment.repo_root", lambda: tmp_path)
        result = create_env_template()
        content = result.read_text()
        assert "your_perplexity_api_key_here" in content
        assert "your_openrouter_api_key_here" in content


class TestCreateDefaultConfigs:
    """Tests for default config creation functions."""

    def test_create_default_domains_config(self, tmp_path):
        """Test creating default domains config."""
        file_path = tmp_path / "domains.yaml"
        create_default_domains_config(file_path)
        assert file_path.exists()
        content = file_path.read_text()
        assert "biochemistry" in content
        assert "neuroscience" in content
        assert "artificial_intelligence" in content

    def test_create_default_entities_config(self, tmp_path):
        """Test creating default entities config."""
        file_path = tmp_path / "entities.yaml"
        create_default_entities_config(file_path)
        assert file_path.exists()
        content = file_path.read_text()
        assert "karl_friston" in content
        assert "tulsi_gabbard" in content

    def test_create_default_languages_config(self, tmp_path):
        """Test creating default languages config."""
        file_path = tmp_path / "languages.yaml"
        create_default_languages_config(file_path)
        assert file_path.exists()
        content = file_path.read_text()
        assert "Chinese" in content
        assert "Spanish" in content
        assert "Arabic" in content


class TestValidateEnvironment:
    """Tests for validate_environment function."""

    def test_missing_directories(self, tmp_path, monkeypatch):
        """Test validation catches missing directories."""
        monkeypatch.setattr("src.system.environment.repo_root", lambda: tmp_path)

        # Simulate virtual environment by making sys.base_prefix != sys.prefix
        original_prefix = sys.prefix
        monkeypatch.setattr(sys, "prefix", original_prefix + "/venv")

        # Set API keys
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test_key_12345")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_key_67890")

        # With empty tmp_path, src/ dir doesn't exist
        is_valid, messages = validate_environment()
        assert not is_valid
        msgs = "\n".join(messages)
        assert "Missing directory" in msgs
        assert "src" in msgs

    def test_valid_environment(self, tmp_path, monkeypatch):
        """Test validation passes with complete environment."""
        monkeypatch.setattr("src.system.environment.repo_root", lambda: tmp_path)

        # Set up virtual environment
        monkeypatch.setattr(sys, "prefix", "/tmp/fake_venv")
        monkeypatch.setattr(sys, "base_prefix", "/usr")

        # Set API keys
        monkeypatch.setenv("PERPLEXITY_API_KEY", "real_key_1234567890")
        monkeypatch.setenv("OPENROUTER_API_KEY", "real_key_1234567890")

        # Create required directories
        (tmp_path / "src").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "data/config").mkdir()
        (tmp_path / "data/prompts").mkdir()
        (tmp_path / "tests").mkdir()

        is_valid, messages = validate_environment()
        assert is_valid
        msgs = "\n".join(messages)
        assert all(keyword not in msgs for keyword in ["Missing directory", "Python 3.8+"])
        assert "Virtual environment active" in msgs


class TestGetEnvironmentInfo:
    """Tests for get_environment_info function."""

    def test_basic_structure(self, monkeypatch, tmp_path):
        """Test get_environment_info returns expected structure."""
        monkeypatch.setattr("src.system.environment.repo_root", lambda: tmp_path)
        (tmp_path / "uv.lock").write_text("")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test_key_123")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_key_456")

        info = get_environment_info()

        assert "python_version" in info
        assert "project_root" in info
        assert "src_path" in info
        assert "data_path" in info
        assert "environment_variables" in info
        assert "uv_available" in info
        assert "uv_lock_exists" in info

        assert info["project_root"] == str(tmp_path)
        assert info["uv_lock_exists"] is True

    def test_env_vars_redacted(self, monkeypatch, tmp_path):
        """Test API key values are redacted."""
        monkeypatch.setattr("src.system.environment.repo_root", lambda: tmp_path)
        monkeypatch.setenv("PERPLEXITY_API_KEY", "super_secret_key_12345")
        monkeypatch.setenv("OPENROUTER_API_KEY", "another_secret_key_67890")

        info = get_environment_info()
        env_vars = info["environment_variables"]
        for key in ["PERPLEXITY_API_KEY", "OPENROUTER_API_KEY"]:
            val = env_vars.get(key, "")
            assert "super_secret" not in val
            assert "characters" in val or "<set" in val


class TestFixCommonIssues:
    """Tests for fix_common_issues function."""

    def test_creates_missing_directories(self, tmp_path, monkeypatch):
        """Test fix_common_issues creates required directories."""
        monkeypatch.setattr("src.system.environment.repo_root", lambda: tmp_path)

        messages = fix_common_issues()

        assert any("Created" in m for m in messages)
        dirs_to_check = [
            "data/config",
            "data/prompts",
            "data/domain_research",
            "data/audience_research",
            "data/written_curriculums",
            "data/translated_curriculums",
            "data/visualizations",
        ]
        for d in dirs_to_check:
            assert (tmp_path / d).exists()

    def test_no_issues_when_dirs_exist(self, tmp_path, monkeypatch):
        """Test fix_common_issues is a no-op when everything exists."""
        monkeypatch.setattr("src.system.environment.repo_root", lambda: tmp_path)

        # Create all directories and config files
        dirs = [
            "data/config",
            "data/prompts",
            "data/domain_research",
            "data/audience_research",
            "data/written_curriculums",
            "data/translated_curriculums",
            "data/visualizations",
        ]
        for d in dirs:
            (tmp_path / d).mkdir(parents=True)
        # Create actual config files so they aren't regenerated
        (tmp_path / "data/config/domains.yaml").write_text("domains: []")
        (tmp_path / "data/config/entities.yaml").write_text("entities: []")
        (tmp_path / "data/config/languages.yaml").write_text("target_languages: []")

        messages = fix_common_issues()

        # Should NOT include 'Created' messages since everything exists
        assert not any("Created" in m for m in messages)
