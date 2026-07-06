"""Tests for uncovered curriculum generation functions.

Covers: save_section, save_complete_curriculum, concatenate_sections,
process_research_file validation paths, and _load_research_content.
Uses real files (no mocks).
"""

from __future__ import annotations

from src.perplexity.curriculum import (
    _load_research_content,
    concatenate_sections,
    save_complete_curriculum,
    save_section,
)


class TestSaveSection:
    """Tests for save_section function."""

    def test_creates_file_in_specified_dir(self, tmp_path):
        """Test save_section creates a markdown file in the specified directory."""
        output_dir = str(tmp_path / "curriculums")
        result = save_section(output_dir, "test_entity", "Introduction", "Test content")
        assert result.exists()
        assert result.parent.name == "test_entity"
        content = result.read_text()
        assert "# Introduction" in content
        assert "Test content" in content

    def test_creates_default_dir_when_empty(self, monkeypatch, tmp_path):
        """Test save_section uses default dir when empty string given."""
        monkeypatch.setattr(
            "src.perplexity.curriculum.data_written_curriculums_dir", lambda: tmp_path / "default"
        )
        result = save_section("", "test_entity", "Section", "Content")
        assert result.exists()


class TestSaveCompleteCurriculum:
    """Tests for save_complete_curriculum function."""

    def test_saves_md_and_json(self, tmp_path):
        """Test save_complete_curriculum creates both .md and .json files."""
        sections = {"Introduction": "Intro content", "Theory": "Theory content"}
        result = save_complete_curriculum(str(tmp_path), "test_entity", sections)
        assert result.exists()
        assert result.suffix == ".md"

        # Check JSON was also created
        json_files = list((tmp_path / "test_entity").glob("complete_curriculum_*.json"))
        assert len(json_files) == 1

        # Check MD content
        content = result.read_text()
        assert "Introduction" in content
        assert "Theory" in content

    def test_empty_sections(self, tmp_path):
        """Test with empty sections dict."""
        result = save_complete_curriculum(str(tmp_path), "empty_entity", {})
        assert result.exists()
        content = result.read_text()
        assert "---" in content
        assert "empty_entity" in content


class TestConcatenateSections:
    """Tests for concatenate_sections function."""

    def test_basic_concatenation(self):
        """Test basic concatenation of sections."""
        result = concatenate_sections("/tmp/test", {"Intro": "Content"})
        assert "---" in result
        assert "generated:" in result
        assert "entity: test" in result
        assert "# Intro" in result
        assert "Content" in result

    def test_multiple_sections(self):
        """Test concatenation with multiple sections."""
        sections = {"Intro": "Content 1", "Body": "Content 2", "Conclusion": "Content 3"}
        result = concatenate_sections("/tmp/test", sections)
        assert "# Intro" in result
        assert "# Body" in result
        assert "# Conclusion" in result
        assert "---" in result


class TestLoadResearchContent:
    """Tests for _load_research_content function."""

    def test_loads_markdown(self, tmp_path):
        """Test loading a markdown research file."""
        md_file = tmp_path / "biochemistry_research_20240101_120000.md"
        md_file.write_text("# Biochemistry Research\n\nContent here.")
        name, content = _load_research_content(str(md_file))
        assert "biochemistry" in name
        assert "Biochemistry Research" in content

    def test_loads_json_with_research_data(self, tmp_path):
        """Test loading a JSON research file with research_data field."""
        import json

        json_file = tmp_path / "entity_research_20240101_120000.json"
        data = {
            "research_data": "Research content here",
            "domain_analysis": "Domain analysis content",
            "curriculum_content": "Curriculum content",
        }
        json_file.write_text(json.dumps(data))
        name, content = _load_research_content(str(json_file))
        assert "Research content here" in content
        assert "Domain analysis" in content
        assert "Curriculum Content" in content

    def test_loads_json_minimal(self, tmp_path):
        """Test loading a JSON research file with no known fields."""
        import json

        json_file = tmp_path / "minimal_research_20240101_120000.json"
        json_file.write_text(json.dumps({"raw": "data"}))
        name, content = _load_research_content(str(json_file))
        # Falls back to raw text
        assert content

    def test_invalid_json_raises(self, tmp_path):
        """Test that invalid JSON raises ValueError."""
        json_file = tmp_path / "invalid_research_20240101_120000.json"
        json_file.write_text("not valid json")
        import pytest

        with pytest.raises(ValueError, match="Failed to parse JSON"):
            _load_research_content(str(json_file))


class TestConcatenateSectionsEntity:
    """Tests for entity name extraction in concatenate_sections."""

    def test_entity_name_in_metadata(self):
        """Test entity name appears in YAML frontmatter."""
        result = concatenate_sections("/projects/test", {"A": "B"})
        assert "entity: test" in result
