"""Tests for the domain research script."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
import os
import importlib.util

# Load the module with hyphen in name
spec = importlib.util.spec_from_file_location(
    "research_domain", 
    os.path.join(os.path.dirname(__file__), '..', 'learning', 'curriculum_creation', '1_Research_Domain.py')
)
research_domain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research_domain)

# Add to sys.modules so patches work
sys.modules['research_domain'] = research_domain


class TestGetDomainFiles:
    """Test get_domain_files function."""

    def test_get_domain_files_empty_dir(self, tmp_path):
        """Test get_domain_files with empty directory."""
        result = research_domain.get_domain_files(tmp_path)
        assert result == []

    def test_get_domain_files_nonexistent_dir(self):
        """Test get_domain_files with non-existent directory."""
        non_existent = Path("/non/existent/path")
        result = research_domain.get_domain_files(non_existent)
        assert result == []

    def test_get_domain_files_with_valid_files(self, tmp_path):
        """Test get_domain_files with valid domain files."""
        # Create test files
        (tmp_path / "Synthetic_Domain1.md").write_text("Domain 1 content")
        (tmp_path / "Synthetic_Domain2.md").write_text("Domain 2 content")
        (tmp_path / "Synthetic_FEP-ActInf.md").write_text("FEP content")  # Should be excluded
        (tmp_path / "Other_File.md").write_text("Other content")  # Should be excluded

        result = research_domain.get_domain_files(tmp_path)
        
        # Should only include domain files, not FEP-ActInf
        assert len(result) == 2
        result_names = [f.name for f in result]
        assert "Synthetic_Domain1.md" in result_names
        assert "Synthetic_Domain2.md" in result_names
        assert "Synthetic_FEP-ActInf.md" not in result_names
        assert "Other_File.md" not in result_names

    def test_get_domain_files_mixed_content(self, tmp_path):
        """Test get_domain_files with mixed file types."""
        # Create various file types
        (tmp_path / "Synthetic_ValidDomain.md").write_text("Valid domain")
        (tmp_path / "Synthetic_Another.txt").write_text("Wrong extension")  # Should be excluded
        (tmp_path / "NotSynthetic.md").write_text("Wrong prefix")  # Should be excluded

        result = research_domain.get_domain_files(tmp_path)
        
        assert len(result) == 1
        assert result[0].name == "Synthetic_ValidDomain.md"


class TestMainFunction:
    """Test main function integration."""

    @patch('research_domain.common_setup_logging')
    @patch('research_domain.inputs_and_outputs_root')
    @patch('research_domain.data_domain_research_dir')
    @patch('research_domain.build_perplexity_client')
    @patch('research_domain.analyze_domain')
    def test_main_successful_execution(
        self,
        mock_analyze_domain,
        mock_build_client,
        mock_output_dir,
        mock_io_root,
        mock_logging,
        tmp_path
    ):
        """Test main function with successful execution."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_io_root.return_value = tmp_path
        mock_output_dir.return_value = tmp_path / "output"
        mock_client = Mock()
        mock_build_client.return_value = mock_client

        # Create test files
        domain_dir = tmp_path / "Domain"
        domain_dir.mkdir()
        (domain_dir / "Synthetic_TestDomain.md").write_text("Test domain content")
        (domain_dir / "Synthetic_FEP-ActInf.md").write_text("FEP content")

        # Run main function
        research_domain.main()

        # Verify calls
        mock_analyze_domain.assert_called_once()
        call_args = mock_analyze_domain.call_args[0]
        assert call_args[0] == mock_client  # client
        assert "Synthetic_TestDomain.md" in call_args[1]  # domain_file
        assert "Synthetic_FEP-ActInf.md" in call_args[2]  # fep_actinf_file

    @patch('research_domain.common_setup_logging')
    @patch('research_domain.inputs_and_outputs_root')
    def test_main_missing_fep_file(
        self,
        mock_io_root,
        mock_logging,
        tmp_path
    ):
        """Test main function when FEP-ActInf file is missing."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_io_root.return_value = tmp_path

        # Create domain directory but no FEP file
        domain_dir = tmp_path / "Domain"
        domain_dir.mkdir()

        # Run main function
        research_domain.main()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "FEP-ActInf file not found" in mock_logger.error.call_args[0][0]

    @patch('research_domain.common_setup_logging')
    @patch('research_domain.inputs_and_outputs_root')
    @patch('research_domain.data_domain_research_dir')
    @patch('research_domain.build_perplexity_client')
    def test_main_no_domain_files(
        self,
        mock_build_client,
        mock_output_dir,
        mock_io_root,
        mock_logging,
        tmp_path
    ):
        """Test main function when no domain files are found."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_io_root.return_value = tmp_path
        mock_output_dir.return_value = tmp_path / "output"

        # Create domain directory with only FEP file
        domain_dir = tmp_path / "Domain"
        domain_dir.mkdir()
        (domain_dir / "Synthetic_FEP-ActInf.md").write_text("FEP content")

        # Run main function
        research_domain.main()

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        assert "No domain files found" in mock_logger.warning.call_args[0][0]

    @patch('research_domain.common_setup_logging')
    @patch('research_domain.build_perplexity_client')
    def test_main_client_initialization_error(
        self,
        mock_build_client,
        mock_logging,
        tmp_path
    ):
        """Test main function when client initialization fails."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_build_client.side_effect = Exception("API key not found")

        # Run main function and expect exception
        with pytest.raises(Exception, match="API key not found"):
            research_domain.main()

        mock_logger.error.assert_called()
        assert "Fatal error in domain research" in mock_logger.error.call_args[0][0]
