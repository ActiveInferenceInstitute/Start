"""Tests for the curriculum introduction writing script."""

from __future__ import annotations

import importlib.util
import os
import sys
from unittest.mock import Mock, patch

import pytest

# Load the module with hyphen in name
spec = importlib.util.spec_from_file_location(
    "write_introduction",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "learning",
        "curriculum_creation",
        "2_Write_Introduction.py",
    ),
)
write_introduction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(write_introduction)

# Add to sys.modules so patches work
sys.modules["write_introduction"] = write_introduction


class TestGetResearchFiles:
    """Test get_research_files function."""

    def test_get_research_files_empty_dir(self, tmp_path):
        """Test get_research_files with empty directory."""
        result = write_introduction.get_research_files(tmp_path)
        assert result == []

    def test_get_research_files_no_json_files(self, tmp_path):
        """Test get_research_files with no JSON files."""
        # Create some non-JSON files
        (tmp_path / "test.txt").write_text("test content")
        (tmp_path / "test.md").write_text("# Test")

        result = write_introduction.get_research_files(tmp_path)
        assert result == []

    def test_get_research_files_with_valid_files(self, tmp_path):
        """Test get_research_files with valid research JSON files."""
        # Create test JSON files
        (tmp_path / "domain1_research_20240101_120000.json").write_text('{"test": "data"}')
        (tmp_path / "domain2_research_20240102_130000.json").write_text('{"test": "data2"}')
        (tmp_path / "other_file.json").write_text('{"other": "data"}')  # Should be excluded

        result = write_introduction.get_research_files(tmp_path)

        # Should only include research files
        assert len(result) == 2
        result_names = [f.name for f in result]
        assert "domain1_research_20240101_120000.json" in result_names
        assert "domain2_research_20240102_130000.json" in result_names
        assert "other_file.json" not in result_names

    def test_get_research_files_mixed_content(self, tmp_path):
        """Test get_research_files with mixed file types."""
        # Create various file types
        (tmp_path / "valid_research_20240101_120000.json").write_text('{"valid": true}')
        (tmp_path / "invalid_research.txt").write_text("Wrong extension")
        (tmp_path / "not_research_20240101_120000.json").write_text('{"not_research": true}')

        result = write_introduction.get_research_files(tmp_path)

        assert len(result) == 1
        assert result[0].name == "valid_research_20240101_120000.json"


class TestProcessResearchDirectory:
    """Test process_research_directory function."""

    @patch("write_introduction.get_research_files")
    def test_process_research_directory_empty(self, mock_get_files, tmp_path):
        """Test processing empty research directory."""
        mock_client = Mock()
        mock_get_files.return_value = []

        fep_file = tmp_path / "fep.md"
        fep_file.write_text("FEP content")

        success, errors = write_introduction.process_research_directory(
            mock_client, tmp_path, fep_file, tmp_path, "test"
        )

        assert success == 0
        assert errors == 0

    @patch("write_introduction.get_research_files")
    @patch("write_introduction.process_research_file")
    def test_process_research_directory_success(self, mock_process, mock_get_files, tmp_path):
        """Test successful processing of research directory."""
        mock_client = Mock()

        # Create test files
        research_files = [
            tmp_path / "domain1_research_20240101.json",
            tmp_path / "domain2_research_20240102.json",
        ]
        for rf in research_files:
            rf.write_text('{"test": "data"}')

        mock_get_files.return_value = research_files
        mock_process.return_value = tmp_path / "output.md"

        fep_file = tmp_path / "fep.md"
        fep_file.write_text("FEP content")

        success, errors = write_introduction.process_research_directory(
            mock_client, tmp_path, fep_file, tmp_path, "test"
        )

        assert success == 2
        assert errors == 0
        assert mock_process.call_count == 2

    @patch("write_introduction.get_research_files")
    @patch("write_introduction.process_research_file")
    def test_process_research_directory_with_errors(self, mock_process, mock_get_files, tmp_path):
        """Test processing with some errors."""
        mock_client = Mock()

        research_files = [
            tmp_path / "domain1_research_20240101.json",
            tmp_path / "domain2_research_20240102.json",
            tmp_path / "domain3_research_20240103.json",
        ]
        for rf in research_files:
            rf.write_text('{"test": "data"}')

        mock_get_files.return_value = research_files
        # First call succeeds, second fails, third succeeds
        mock_process.side_effect = [
            tmp_path / "output1.md",
            Exception("Processing failed"),
            tmp_path / "output3.md",
        ]

        fep_file = tmp_path / "fep.md"
        fep_file.write_text("FEP content")

        success, errors = write_introduction.process_research_directory(
            mock_client, tmp_path, fep_file, tmp_path, "test"
        )

        assert success == 2
        assert errors == 1


class TestMainFunction:
    """Test main function integration."""

    @patch("write_introduction.common_setup_logging")
    @patch("write_introduction.inputs_and_outputs_root")
    @patch("write_introduction.data_written_curriculums_dir")
    @patch("write_introduction.data_domain_research_dir")
    @patch("write_introduction.data_audience_research_dir")
    @patch("write_introduction.build_openrouter_client")
    @patch("write_introduction.process_research_directory")
    def test_main_successful_execution(
        self,
        mock_process_dir,
        mock_build_client,
        mock_audience_dir,
        mock_domain_dir,
        mock_output_dir,
        mock_inputs_root,
        mock_logging,
        tmp_path,
    ):
        """Test main function with successful execution."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_inputs_root.return_value = tmp_path / "inputs"
        mock_output_dir.return_value = tmp_path / "output"
        mock_domain_dir.return_value = tmp_path / "domain"
        mock_audience_dir.return_value = tmp_path / "audience"

        # Create required directories and files
        (tmp_path / "inputs").mkdir()
        (tmp_path / "output").mkdir()
        (tmp_path / "domain").mkdir()
        (tmp_path / "audience").mkdir()
        (tmp_path / "inputs" / "Synthetic_FEP-ActInf.md").write_text("FEP content")

        mock_client = Mock()
        mock_build_client.return_value = mock_client
        mock_process_dir.return_value = (5, 1)  # 5 success, 1 error

        # Mock sys.argv
        with patch("sys.argv", ["script_name"]):
            write_introduction.main()

        # Verify client was built
        mock_build_client.assert_called_once()

        # Verify directories were processed
        assert mock_process_dir.call_count == 2  # domain and audience research

    @patch("write_introduction.common_setup_logging")
    @patch("write_introduction.inputs_and_outputs_root")
    def test_main_missing_fep_file(self, mock_inputs_root, mock_logging, tmp_path):
        """Test main function when FEP-ActInf file is missing."""
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_inputs_root.return_value = tmp_path / "inputs"

        # Create inputs directory but no FEP file
        (tmp_path / "inputs").mkdir()

        # Mock sys.argv
        with patch("sys.argv", ["script_name"]):
            write_introduction.main()

        # Verify error was logged
        mock_logger.error.assert_called()
        error_msg = mock_logger.error.call_args[0][0]
        assert "FEP-ActInf file not found" in error_msg

    @patch("write_introduction.common_setup_logging")
    @patch("write_introduction.inputs_and_outputs_root")
    @patch("write_introduction.data_written_curriculums_dir")
    @patch("write_introduction.data_domain_research_dir")
    @patch("write_introduction.data_audience_research_dir")
    @patch("write_introduction.build_openrouter_client")
    def test_main_client_initialization_error(
        self,
        mock_build_client,
        mock_audience_dir,
        mock_domain_dir,
        mock_output_dir,
        mock_inputs_root,
        mock_logging,
        tmp_path,
    ):
        """Test main function when client initialization fails."""
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_inputs_root.return_value = tmp_path / "inputs"
        mock_output_dir.return_value = tmp_path / "output"
        mock_domain_dir.return_value = tmp_path / "domain"
        mock_audience_dir.return_value = tmp_path / "audience"

        # Create required directories and files
        (tmp_path / "inputs").mkdir()
        (tmp_path / "output").mkdir()
        (tmp_path / "domain").mkdir()
        (tmp_path / "audience").mkdir()
        (tmp_path / "inputs" / "Synthetic_FEP-ActInf.md").write_text("FEP content")

        mock_build_client.side_effect = Exception("API key not found")

        # Mock sys.argv
        with patch("sys.argv", ["script_name"]):
            write_introduction.main()

        # Verify error was logged
        mock_logger.error.assert_called()


class TestIntegration:
    """Integration tests for the curriculum introduction writing pipeline."""

    @pytest.mark.integration
    def test_realistic_workflow(self, tmp_path):
        """Test a realistic workflow with actual file operations."""
        # Create directory structure
        inputs_dir = tmp_path / "inputs"
        domain_dir = tmp_path / "domain"
        output_dir = tmp_path / "output"

        inputs_dir.mkdir()
        domain_dir.mkdir()
        output_dir.mkdir()

        # Create FEP-ActInf file
        fep_file = inputs_dir / "Synthetic_FEP-ActInf.md"
        fep_file.write_text(
            """# Free Energy Principle and Active Inference

## Overview
The Free Energy Principle is a theoretical framework...

## Mathematical Framework
The principle is based on variational inference...
"""
        )

        # Create sample research file
        research_file = domain_dir / "biochemistry_research_20240101_120000.json"
        research_file.write_text(
            """{
            "domain_name": "biochemistry",
            "analysis": "Biochemistry is the study of chemical processes...",
            "key_concepts": ["enzymes", "metabolic pathways", "protein structure"],
            "applications": ["drug discovery", "biotechnology"]
        }"""
        )

        # Test get_research_files
        research_files = write_introduction.get_research_files(domain_dir)
        assert len(research_files) == 1
        assert research_files[0].name == "biochemistry_research_20240101_120000.json"

        # Verify FEP file processing would work
        assert fep_file.exists()
        fep_content = fep_file.read_text()
        assert "Free Energy Principle" in fep_content
