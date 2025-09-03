"""Tests for the path utilities module."""

from __future__ import annotations

from src.common.paths import (
    data_audience_research_dir,
    data_domain_research_dir,
    data_root,
    data_translated_curriculums_dir,
    data_visualizations_dir,
    data_written_curriculums_dir,
    domain_dir,
    domain_research_dir,
    ensure_dir,
    find_repo_root,
    inputs_and_outputs_root,
    languages_root,
    repo_root,
)


def test_find_repo_root_from_file():
    """Test finding repo root from current file location."""
    root = find_repo_root(__file__)
    assert root.exists()
    assert root.is_dir()
    # Should find either .git or README.md in the root
    assert (root / ".git").exists() or (root / "README.md").exists()


def test_find_repo_root_from_none():
    """Test finding repo root with None parameter (uses __file__)."""
    root = find_repo_root(None)
    assert root.exists()
    assert root.is_dir()


def test_repo_root():
    """Test getting the repository root."""
    root = repo_root()
    assert root.exists()
    assert root.is_dir()
    # Should be the same as find_repo_root
    assert root == find_repo_root()


def test_languages_root():
    """Test getting languages root path."""
    lang_root = languages_root()
    # Should be repo_root / "Languages"
    expected = repo_root() / "Languages"
    assert lang_root == expected


def test_inputs_and_outputs_root():
    """Test getting inputs and outputs root path."""
    io_root = inputs_and_outputs_root()
    # Should be languages_root / "Inputs_and_Outputs"
    expected = languages_root() / "Inputs_and_Outputs"
    assert io_root == expected


def test_domain_dir():
    """Test getting domain directory path."""
    domain = domain_dir()
    # Should be inputs_and_outputs_root / "Domain"
    expected = inputs_and_outputs_root() / "Domain"
    assert domain == expected


def test_domain_research_dir():
    """Test getting domain research directory path."""
    domain_research = domain_research_dir()
    # Should be inputs_and_outputs_root / "Domain_Research"
    expected = inputs_and_outputs_root() / "Domain_Research"
    assert domain_research == expected


def test_ensure_dir_new(tmp_path):
    """Test creating a new directory."""
    new_dir = tmp_path / "new_directory"
    assert not new_dir.exists()

    result = ensure_dir(new_dir)

    assert result.exists()
    assert result.is_dir()
    assert result.resolve() == new_dir.resolve()


def test_ensure_dir_existing(tmp_path):
    """Test ensuring an existing directory."""
    existing_dir = tmp_path / "existing"
    existing_dir.mkdir()

    result = ensure_dir(existing_dir)

    assert result.exists()
    assert result.is_dir()
    assert result.resolve() == existing_dir.resolve()


def test_ensure_dir_nested(tmp_path):
    """Test creating nested directories."""
    nested_dir = tmp_path / "level1" / "level2" / "level3"
    assert not nested_dir.exists()

    result = ensure_dir(nested_dir)

    assert result.exists()
    assert result.is_dir()
    assert result.resolve() == nested_dir.resolve()


def test_data_root():
    """Test getting data root path."""
    data = data_root()
    # Should be repo_root / "data"
    expected = repo_root() / "data"
    assert data == expected


def test_data_directories_structure():
    """Test that all data directory functions return correct paths."""
    root = data_root()

    # Test each data directory
    assert data_written_curriculums_dir() == root / "written_curriculums"
    assert data_translated_curriculums_dir() == root / "translated_curriculums"
    assert data_visualizations_dir() == root / "visualizations"
    assert data_audience_research_dir() == root / "audience_research"
    assert data_domain_research_dir() == root / "domain_research"


def test_data_directories_created():
    """Test that data directory functions actually create the directories."""
    # These functions should create directories if they don't exist
    dirs_to_check = [
        data_written_curriculums_dir(),
        data_translated_curriculums_dir(),
        data_visualizations_dir(),
        data_audience_research_dir(),
        data_domain_research_dir(),
    ]

    for directory in dirs_to_check:
        assert directory.exists(), f"Directory not created: {directory}"
        assert directory.is_dir(), f"Path is not a directory: {directory}"


def test_path_relationships():
    """Test that paths have correct parent-child relationships."""
    root = repo_root()

    # Test hierarchy
    assert languages_root().parent == root
    assert inputs_and_outputs_root().parent == languages_root()
    assert domain_dir().parent == inputs_and_outputs_root()
    assert domain_research_dir().parent == inputs_and_outputs_root()
    assert data_root().parent == root
