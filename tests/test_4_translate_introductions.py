"""Tests for the curriculum translation script."""

from __future__ import annotations

import importlib.util
import os
import sys
from unittest.mock import Mock, patch


# Load the module with hyphen in name
spec = importlib.util.spec_from_file_location(
    "translation",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "learning",
        "curriculum_creation",
        "4_Translate_Introductions.py",
    ),
)
translation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(translation)

# Add to sys.modules so patches work
sys.modules["translation"] = translation


class TestValidateLanguages:
    """Test validate_languages function."""

    def test_validate_all_valid_languages(self):
        """Test validation when all requested languages are valid."""
        requested = ["Spanish", "French", "German"]
        available = ["English", "Spanish", "French", "German", "Chinese"]

        result = translation.validate_languages(requested, available)

        assert result == ["Spanish", "French", "German"]

    def test_validate_some_invalid_languages(self, capsys):
        """Test validation when some requested languages are invalid (now allows custom languages)."""
        requested = ["Spanish", "Klingon", "French", "Elvish"]
        available = ["English", "Spanish", "French", "German", "Chinese"]

        result = translation.validate_languages(requested, available)

        # New behavior: allows custom languages with warnings
        assert result == ["Spanish", "Klingon", "French", "Elvish"]

        # Check warning messages for custom languages
        captured = capsys.readouterr()
        assert "Language 'Klingon' not in config" in captured.out
        assert "Language 'Elvish' not in config" in captured.out

    def test_validate_no_requested_languages(self):
        """Test validation when no languages are requested (should return all available)."""
        requested = []
        available = ["English", "Spanish", "French"]

        result = translation.validate_languages(requested, available)

        assert result == available

    def test_validate_none_requested_languages(self):
        """Test validation when None is passed (should return all available)."""
        requested = None
        available = ["English", "Spanish", "French"]

        result = translation.validate_languages(requested, available)

        assert result == available

    def test_validate_all_invalid_languages(self, capsys):
        """Test validation when all requested languages are invalid (now allows custom languages)."""
        requested = ["Klingon", "Elvish", "Dothraki"]
        available = ["English", "Spanish", "French"]

        result = translation.validate_languages(requested, available)

        # New behavior: allows custom languages with warnings
        assert result == ["Klingon", "Elvish", "Dothraki"]

        # Check all warning messages appeared
        captured = capsys.readouterr()
        for lang in requested:
            assert f"Language '{lang}' not in config" in captured.out

    def test_validate_empty_available_languages(self, capsys):
        """Test validation when no languages are available (now allows custom languages)."""
        requested = ["Spanish", "French"]
        available = []

        result = translation.validate_languages(requested, available)

        # New behavior: allows custom languages with warnings
        assert result == ["Spanish", "French"]

        # Check warning messages for custom languages
        captured = capsys.readouterr()
        assert "Language 'Spanish' not in config" in captured.out
        assert "Language 'French' not in config" in captured.out


class TestMainFunction:
    """Test main function integration."""

    @patch("translation.common_setup_logging")
    @patch("translation.data_written_curriculums_dir")
    @patch("translation.data_translated_curriculums_dir")
    @patch("translation.build_openrouter_client")
    @patch("translation.get_target_languages")
    @patch("translation.process_translations")
    def test_main_successful_execution(
        self,
        mock_process_translations,
        mock_get_languages,
        mock_build_client,
        mock_output_dir,
        mock_input_dir,
        mock_logging,
        tmp_path,
    ):
        """Test main function with successful execution."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_input_dir.return_value = tmp_path / "input"
        mock_output_dir.return_value = tmp_path / "output"
        mock_get_languages.return_value = ["Spanish", "French", "German"]
        mock_client = Mock()
        mock_build_client.return_value = mock_client
        mock_process_translations.return_value = (5, 1)  # 5 success, 1 failed

        # Create input directory with curriculum files
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create entity subdirectory with curriculum file
        entity_dir = input_dir / "test_entity"
        entity_dir.mkdir()
        (entity_dir / "complete_curriculum_20240101_120000.md").write_text(
            "# Test Curriculum\n\n## Introduction\nTest content."
        )

        # Mock sys.argv to avoid argparse issues
        with patch("sys.argv", ["script_name"]):
            translation.main()

        # Verify calls
        mock_process_translations.assert_called_once()
        call_args = mock_process_translations.call_args
        assert call_args[0][0] == mock_client  # client
        assert call_args[0][3] == ["Spanish", "French", "German"]  # target languages

        # Verify logging
        mock_logger.info.assert_called()
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Successful translations: 5" in msg for msg in info_calls)
        assert any("Failed translations: 1" in msg for msg in info_calls)

    @patch("translation.common_setup_logging")
    @patch("translation.data_written_curriculums_dir")
    def test_main_input_directory_not_exists(self, mock_input_dir, mock_logging, tmp_path):
        """Test main function when input directory doesn't exist."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_input_dir.return_value = tmp_path / "nonexistent"

        # Mock sys.argv
        with patch("sys.argv", ["script_name"]):
            translation.main()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "Input directory does not exist" in mock_logger.error.call_args[0][0]

    @patch("translation.common_setup_logging")
    @patch("translation.data_written_curriculums_dir")
    @patch("translation.data_translated_curriculums_dir")
    @patch("translation.get_target_languages")
    def test_main_no_valid_languages(
        self, mock_get_languages, mock_output_dir, mock_input_dir, mock_logging, tmp_path
    ):
        """Test main function when no valid target languages are available."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_input_dir.return_value = tmp_path / "input"
        mock_output_dir.return_value = tmp_path / "output"
        mock_get_languages.return_value = []

        # Create input directory
        (tmp_path / "input").mkdir()

        # Mock sys.argv
        with patch("sys.argv", ["script_name"]):
            translation.main()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "No valid target languages specified" in mock_logger.error.call_args[0][0]

    @patch("translation.common_setup_logging")
    @patch("translation.data_written_curriculums_dir")
    @patch("translation.data_translated_curriculums_dir")
    @patch("translation.build_openrouter_client")
    @patch("translation.get_target_languages")
    def test_main_client_initialization_error(
        self,
        mock_get_languages,
        mock_build_client,
        mock_output_dir,
        mock_input_dir,
        mock_logging,
        tmp_path,
    ):
        """Test main function when client initialization fails."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_input_dir.return_value = tmp_path / "input"
        mock_output_dir.return_value = tmp_path / "output"
        mock_get_languages.return_value = ["Spanish"]
        mock_build_client.side_effect = Exception("API key not found")

        # Create input directory with curriculum files
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create entity subdirectory with curriculum file
        entity_dir = input_dir / "test_entity"
        entity_dir.mkdir()
        (entity_dir / "complete_curriculum_20240101_120000.md").write_text(
            "# Test Curriculum\n\n## Introduction\nTest content."
        )

        # Mock sys.argv - no exception expected since error is caught and logged
        with patch("sys.argv", ["script_name"]):
            translation.main()

        # Verify error was logged instead of raised
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed to initialize OpenRouter client" in error_call

    @patch("translation.common_setup_logging")
    @patch("translation.data_written_curriculums_dir")
    @patch("translation.data_translated_curriculums_dir")
    @patch("translation.build_openrouter_client")
    @patch("translation.get_target_languages")
    @patch("translation.process_translations")
    def test_main_with_command_line_args(
        self,
        mock_process_translations,
        mock_get_languages,
        mock_build_client,
        mock_output_dir,
        mock_input_dir,
        mock_logging,
        tmp_path,
    ):
        """Test main function with command line arguments."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_get_languages.return_value = ["Spanish", "French", "German", "Chinese"]
        mock_client = Mock()
        mock_build_client.return_value = mock_client
        mock_process_translations.return_value = (3, 0)

        # Create test directories with curriculum files
        input_dir = tmp_path / "custom_input"
        output_dir = tmp_path / "custom_output"
        input_dir.mkdir()

        # Create entity subdirectory with curriculum file
        entity_dir = input_dir / "test_entity"
        entity_dir.mkdir()
        (entity_dir / "complete_curriculum_20240101_120000.md").write_text(
            "# Test Curriculum\n\n## Introduction\nTest content."
        )

        # Mock sys.argv with custom arguments
        test_argv = [
            "script_name",
            "--input",
            str(input_dir),
            "--output",
            str(output_dir),
            "--languages",
            "Spanish",
            "German",
        ]

        with patch("sys.argv", test_argv):
            translation.main()

        # Verify process_translations was called with correct arguments
        mock_process_translations.assert_called_once()
        call_args = mock_process_translations.call_args
        assert call_args[0][1] == str(input_dir)  # input_dir
        assert call_args[0][2] == str(output_dir)  # output_dir
        assert call_args[0][3] == ["Spanish", "German"]  # target languages

    @patch("translation.common_setup_logging")
    @patch("translation.data_written_curriculums_dir")
    @patch("translation.data_translated_curriculums_dir")
    @patch("translation.build_openrouter_client")
    @patch("translation.get_target_languages")
    @patch("translation.process_translations")
    def test_main_no_successful_translations(
        self,
        mock_process_translations,
        mock_get_languages,
        mock_build_client,
        mock_output_dir,
        mock_input_dir,
        mock_logging,
        tmp_path,
    ):
        """Test main function when no translations succeed."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_input_dir.return_value = tmp_path / "input"
        mock_output_dir.return_value = tmp_path / "output"
        mock_get_languages.return_value = ["Spanish", "French"]
        mock_client = Mock()
        mock_build_client.return_value = mock_client
        mock_process_translations.return_value = (0, 5)  # 0 success, 5 failed

        # Create input directory with curriculum files
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create entity subdirectory with curriculum file
        entity_dir = input_dir / "test_entity"
        entity_dir.mkdir()
        (entity_dir / "complete_curriculum_20240101_120000.md").write_text(
            "# Test Curriculum\n\n## Introduction\nTest content."
        )

        # Mock sys.argv
        with patch("sys.argv", ["script_name"]):
            translation.main()

        # Verify warning about failed translations
        mock_logger.warning.assert_called_once()
        assert "5 translations failed" in mock_logger.warning.call_args[0][0]

    @patch("translation.common_setup_logging")
    @patch("translation.data_written_curriculums_dir")
    @patch("translation.data_translated_curriculums_dir")
    @patch("translation.build_openrouter_client")
    @patch("translation.get_target_languages")
    @patch("translation.process_translations")
    def test_main_mixed_translation_results(
        self,
        mock_process_translations,
        mock_get_languages,
        mock_build_client,
        mock_output_dir,
        mock_input_dir,
        mock_logging,
        tmp_path,
    ):
        """Test main function with mixed translation results."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_input_dir.return_value = tmp_path / "input"
        mock_output_dir.return_value = tmp_path / "output"
        mock_get_languages.return_value = ["Spanish", "French", "German"]
        mock_client = Mock()
        mock_build_client.return_value = mock_client
        mock_process_translations.return_value = (2, 1)  # 2 success, 1 failed

        # Create input directory with curriculum files
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create entity subdirectory with curriculum file
        entity_dir = input_dir / "test_entity"
        entity_dir.mkdir()
        (entity_dir / "complete_curriculum_20240101_120000.md").write_text(
            "# Test Curriculum\n\n## Introduction\nTest content."
        )

        # Mock sys.argv
        with patch("sys.argv", ["script_name"]):
            translation.main()

        # Verify both success and failure messages
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]

        assert any("Successful translations: 2" in msg for msg in info_calls)
        assert any("Failed translations: 1" in msg for msg in info_calls)
        assert any("Translated curricula saved to" in msg for msg in info_calls)
        assert any("1 translations failed" in msg for msg in warning_calls)


class TestArgumentParsing:
    """Test command line argument parsing."""

    def test_default_arguments(self):
        """Test parsing with default arguments."""
        # This test would require more complex mocking of argparse
        # For now, we test the main function behavior which includes argument parsing
        pass

    def test_custom_arguments(self):
        """Test parsing with custom arguments."""
        # Similar to above - tested through main function integration tests
        pass


class TestIntegration:
    """Integration tests with realistic scenarios."""

    @patch("translation.build_openrouter_client")
    @patch("translation.process_translations")
    def test_realistic_workflow(self, mock_process_translations, mock_build_client, tmp_path):
        """Test realistic translation workflow."""
        # Setup realistic test data
        input_dir = tmp_path / "written_curriculums"
        output_dir = tmp_path / "translated_curriculums"

        # Create curriculum structure
        entity_dir = input_dir / "data_scientist"
        entity_dir.mkdir(parents=True)
        curriculum_content = """# Active Inference for Data Scientists

## Introduction
Welcome to this comprehensive curriculum on Active Inference.

## Core Concepts
Learn the fundamental principles.

## Applications
Apply the concepts to real-world problems.
"""
        (entity_dir / "complete_curriculum_20240101_120000.md").write_text(curriculum_content)

        # Mock successful translation
        mock_client = Mock()
        mock_build_client.return_value = mock_client
        mock_process_translations.return_value = (3, 0)  # 3 languages, all successful

        # Run translation with realistic arguments
        test_argv = [
            "script_name",
            "--input",
            str(input_dir),
            "--output",
            str(output_dir),
            "--languages",
            "Spanish",
            "French",
            "German",
        ]

        with patch("sys.argv", test_argv):
            with patch("translation.common_setup_logging") as mock_logging:
                mock_logger = Mock()
                mock_logging.return_value = mock_logger

                translation.main()

        # Verify the process worked
        mock_process_translations.assert_called_once()
        call_args = mock_process_translations.call_args
        assert call_args[0][0] == mock_client
        assert call_args[0][1] == str(input_dir)
        assert call_args[0][2] == str(output_dir)
        assert call_args[0][3] == ["Spanish", "French", "German"]

        # Verify success was logged
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Successful translations: 3" in msg for msg in info_calls)
        assert any("Failed translations: 0" in msg for msg in info_calls)
