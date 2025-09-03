"""Tests for the visualization runner module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.visualization.runner import (
    collect_curriculum_files,
    generate_curriculum_metrics,
    run,
)


def test_collect_curriculum_files_empty_directory(tmp_path):
    """Test collecting curriculum files from empty directory."""
    files = collect_curriculum_files(str(tmp_path))
    assert files == []


def test_collect_curriculum_files_with_files(tmp_path):
    """Test collecting curriculum files from directory with curriculum files."""
    # Create directory structure with curriculum files
    entity1_dir = tmp_path / "entity1"
    entity1_dir.mkdir()
    (entity1_dir / "complete_curriculum_20240101_120000.md").write_text(
        "Entity 1 curriculum", encoding="utf-8"
    )

    entity2_dir = tmp_path / "entity2"
    entity2_dir.mkdir()
    (entity2_dir / "complete_curriculum_20240102_130000.md").write_text(
        "Entity 2 curriculum", encoding="utf-8"
    )

    # Add non-matching file that should be ignored
    (entity1_dir / "other_file.md").write_text("Not a curriculum", encoding="utf-8")

    files = collect_curriculum_files(str(tmp_path))

    # Should find 2 curriculum files
    assert len(files) == 2

    # Check file structure (entity_name, file_path)
    entity_names = [f[0] for f in files]
    file_paths = [f[1] for f in files]

    assert "entity1" in entity_names
    assert "entity2" in entity_names

    # Check file paths
    assert any("entity1" in path for path in file_paths)
    assert any("entity2" in path for path in file_paths)
    assert all("complete_curriculum_" in path for path in file_paths)


def test_collect_curriculum_files_nested_structure(tmp_path):
    """Test collecting curriculum files from nested directory structure."""
    # Create deeper nested structure
    deep_dir = tmp_path / "level1" / "level2" / "entity_deep"
    deep_dir.mkdir(parents=True)
    (deep_dir / "complete_curriculum_20240103_140000.md").write_text(
        "Deep curriculum", encoding="utf-8"
    )

    files = collect_curriculum_files(str(tmp_path))

    assert len(files) == 1
    assert files[0][0] == "entity_deep"
    assert "complete_curriculum_20240103_140000.md" in files[0][1]


def test_generate_curriculum_metrics_basic():
    """Test generating basic curriculum metrics."""
    curriculum_docs = [
        "# Title 1\n\nParagraph 1\n\nParagraph 2\n\n## Section A\nContent A",
        "# Title 2\n\nParagraph 1\n\n## Section B\nContent B\n\n## Section C\nContent C",
    ]
    entity_labels = ["Entity1", "Entity2"]

    # Create temporary directory for output
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        generate_curriculum_metrics(curriculum_docs, entity_labels, tmp_dir)

        # Check that CSV file was created
        csv_path = Path(tmp_dir) / "curriculum_metrics.csv"
        assert csv_path.exists()

        # Read and check CSV content
        df = pd.read_csv(csv_path)

        assert len(df) == 2
        assert list(df.columns) == [
            "Entity",
            "Total Words",
            "Sections",
            "Paragraphs",
            "Words per Section",
            "Words per Paragraph",
        ]

        # Check data types and basic values
        assert df["Entity"].tolist() == ["Entity1", "Entity2"]
        assert all(df["Total Words"] > 0)
        assert all(df["Sections"] > 0)
        assert all(df["Paragraphs"] > 0)
        assert all(df["Words per Section"] > 0)
        assert all(df["Words per Paragraph"] > 0)


def test_generate_curriculum_metrics_empty():
    """Test generating metrics with empty curricula."""
    curriculum_docs = ["", "   \n  \n   "]
    entity_labels = ["Empty1", "Empty2"]

    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        generate_curriculum_metrics(curriculum_docs, entity_labels, tmp_dir)

        csv_path = Path(tmp_dir) / "curriculum_metrics.csv"
        assert csv_path.exists()

        df = pd.read_csv(csv_path)
        assert len(df) == 2
        assert list(df["Entity"]) == ["Empty1", "Empty2"]


def test_generate_curriculum_metrics_word_counting():
    """Test that word counting works correctly."""
    curriculum_docs = [
        "One two three four five",  # 5 words
        "Six seven eight nine ten eleven twelve",  # 7 words
    ]
    entity_labels = ["Test1", "Test2"]

    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        generate_curriculum_metrics(curriculum_docs, entity_labels, tmp_dir)

        csv_path = Path(tmp_dir) / "curriculum_metrics.csv"
        df = pd.read_csv(csv_path)

        # Check word counts
        assert df[df["Entity"] == "Test1"]["Total Words"].iloc[0] == 5
        assert df[df["Entity"] == "Test2"]["Total Words"].iloc[0] == 7


def test_run_function_no_files(tmp_path, monkeypatch):
    """Test run function when no curriculum files exist."""

    # Mock inputs_and_outputs_root to return tmp_path
    def mock_inputs_and_outputs_root():
        return tmp_path

    # Patch the function that gets imported inside run()
    monkeypatch.setattr("src.common.paths.inputs_and_outputs_root", mock_inputs_and_outputs_root)

    # Run function
    output_dir = str(tmp_path / "output")
    run("input_root", output_dir)

    # Should not create any files when no curricula found
    output_path = Path(output_dir)
    if output_path.exists():
        assert len(list(output_path.glob("*"))) == 0


def test_run_function_with_files(tmp_path, monkeypatch):
    """Test run function with actual curriculum files."""

    # Mock inputs_and_outputs_root to return tmp_path
    def mock_inputs_and_outputs_root():
        return tmp_path

    # Patch the function that gets imported inside run()
    monkeypatch.setattr("src.common.paths.inputs_and_outputs_root", mock_inputs_and_outputs_root)

    # Create Written_Curriculums directory with files
    written_dir = tmp_path / "Written_Curriculums"
    written_dir.mkdir()

    entity_dir = written_dir / "test_entity"
    entity_dir.mkdir()
    curriculum_file = entity_dir / "complete_curriculum_20240101_120000.md"
    curriculum_file.write_text(
        "# Test Curriculum\n\nTest content\n\n## Section 1\nSection content", encoding="utf-8"
    )

    # Run function
    output_dir = str(tmp_path / "output")
    run("input_root", output_dir)

    # Check that metrics file was created
    metrics_file = Path(output_dir) / "metrics" / "curriculum_metrics.csv"
    assert metrics_file.exists()

    # Check content
    df = pd.read_csv(metrics_file)
    assert len(df) == 1
    assert df["Entity"].iloc[0] == "test_entity"
    assert df["Total Words"].iloc[0] > 0
