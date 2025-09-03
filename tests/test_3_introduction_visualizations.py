"""Tests for the curriculum visualization script."""

from __future__ import annotations

import json
import os
import importlib.util

import pytest
from unittest.mock import Mock, patch

# Load the module with hyphen in name
viz_script_path = os.path.join(
    os.path.dirname(__file__), '..', 'learning', 'curriculum_creation', 
    '3_Introduction_Visualizations.py'
)
spec = importlib.util.spec_from_file_location("visualizations", viz_script_path)
visualizations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visualizations)

# Add to sys.modules so patches work
import sys
sys.modules['visualizations'] = visualizations


class TestExtractCurriculumMetadata:
    """Test extract_curriculum_metadata function."""

    def test_extract_basic_metrics(self):
        """Test extraction of basic metrics from curriculum content."""
        content = """# Main Title

This is a paragraph with some content.

## Section 1
More content here.

## Learning Objectives
- Objective 1
- Objective 2
- Objective 3

```python
print("Hello world")
```

Math expression: $E = mc^2$
"""
        
        result = visualizations.extract_curriculum_metadata(content)
        
        assert result['section_count'] == 3  # Three headers (# Main Title, ## Section 1, ## Learning Objectives)
        assert result['objectives_count'] == 3  # Three bullet points
        assert result['code_block_count'] == 1  # One code block
        assert result['math_expressions_count'] == 1  # One math expression
        assert result['word_count'] > 0
        assert result['paragraph_count'] > 0
        assert result['words_per_section'] > 0
        assert result['words_per_paragraph'] > 0

    def test_extract_sections_list(self):
        """Test extraction of section names."""
        content = """# Main Title

## Introduction to Active Inference
Content here.

## Mathematical Framework
More content.

## Practical Applications
Application content.
"""
        
        result = visualizations.extract_curriculum_metadata(content)
        
        assert result['section_count'] == 4  # Four headers (# Main Title, ## Introduction, ## Mathematical Framework, ## Practical Applications)
        sections = result['sections']
        assert "Introduction to Active Inference" in sections
        assert "Mathematical Framework" in sections
        assert "Practical Applications" in sections

    def test_extract_empty_content(self):
        """Test extraction from empty content."""
        content = ""
        
        result = visualizations.extract_curriculum_metadata(content)
        
        assert result['word_count'] == 0
        assert result['section_count'] == 0
        assert result['objectives_count'] == 0
        assert result['code_block_count'] == 0
        assert result['math_expressions_count'] == 0

    def test_extract_complex_objectives(self):
        """Test extraction of learning objectives with various formats."""
        content = """
## Learning Objectives
- Learn about Active Inference
* Understand the Free Energy Principle
+ Apply concepts to real problems

## Goals
- Master the mathematical framework
- Implement practical solutions

## Other Section
No objectives here.
"""
        
        result = visualizations.extract_curriculum_metadata(content)
        
        # Should find objectives in both "Learning Objectives" and "Goals" sections
        assert result['objectives_count'] >= 5


class TestMermaidDiagramGeneration:
    """Test Mermaid diagram generation functions."""

    def test_create_curriculum_flow_mermaid(self):
        """Test creation of curriculum flow diagram."""
        sections = [
            "Introduction",
            "Core Concepts",
            "Mathematical Framework",
            "Applications"
        ]
        entity_name = "Data Scientist"
        
        result = visualizations.create_curriculum_flow_mermaid(sections, entity_name)
        
        assert "flowchart TD" in result
        assert entity_name in result
        assert "Introduction" in result
        assert "Core Concepts" in result
        assert "Mathematical Framework" in result
        assert "Applications" in result
        assert "Mastery Achieved" in result

    def test_create_curriculum_flow_empty_sections(self):
        """Test flow diagram with empty sections."""
        sections = []
        entity_name = "Test Entity"
        
        result = visualizations.create_curriculum_flow_mermaid(sections, entity_name)
        
        assert "flowchart TD" in result
        assert entity_name in result
        assert "Foundation" in result
        assert "Mastery Achieved" in result

    def test_create_curriculum_structure_mermaid(self):
        """Test creation of overall curriculum structure diagram."""
        curricula_data = [
            {
                'entity_name': 'Data Scientist',
                'sections': ['Intro', 'Core', 'Advanced']
            },
            {
                'entity_name': 'Neuroscientist',
                'sections': ['Foundations', 'Theory', 'Practice', 'Research']
            }
        ]
        
        result = visualizations.create_curriculum_structure_mermaid(curricula_data)
        
        assert "graph TB" in result
        assert "Active Inference Curricula" in result
        assert "Data Scientist" in result
        assert "Neuroscientist" in result
        assert "(3 sections)" in result
        assert "(4 sections)" in result

    def test_create_structure_long_section_names(self):
        """Test structure diagram with very long section names."""
        curricula_data = [
            {
                'entity_name': 'Test Entity',
                'sections': [
                    'This is a very long section name that should be truncated for display'
                ]
            }
        ]
        
        result = visualizations.create_curriculum_structure_mermaid(curricula_data)
        
        # Should truncate long section names
        assert "This is a very long" in result
        matching_lines = [line for line in result.split('\n') if 'This is a very long' in line]
        assert len(matching_lines[0]) < 100


class TestCollectCurriculumData:
    """Test curriculum data collection."""

    def test_collect_curriculum_data_valid_files(self, tmp_path):
        """Test collecting data from valid curriculum files."""
        # Create test curriculum structure
        entity1_dir = tmp_path / "entity1"
        entity1_dir.mkdir()
        curriculum_content = """# Entity1 Curriculum

## Introduction
Welcome to the curriculum.

## Learning Objectives
- Concept 1
- Concept 2

```python
print("test")
```

Math: $x = y + z$
"""
        (entity1_dir / "complete_curriculum_20240101_120000.md").write_text(curriculum_content)
        
        entity2_dir = tmp_path / "entity2"
        entity2_dir.mkdir()
        (entity2_dir / "complete_curriculum_20240102_130000.md").write_text("# Entity2\n\n## Section 1\nContent here.")
        
        result = visualizations.collect_curriculum_data(tmp_path)
        
        assert len(result) == 2
        
        # Check first curriculum
        entity1_data = next(d for d in result if d['entity_name'] == 'entity1')
        assert entity1_data['section_count'] == 3  # Three headers (# Entity1 Curriculum, ## Introduction, ## Learning Objectives)
        assert entity1_data['objectives_count'] == 2
        assert entity1_data['code_block_count'] == 1
        assert entity1_data['math_expressions_count'] == 1
        
        # Check second curriculum
        entity2_data = next(d for d in result if d['entity_name'] == 'entity2')
        assert entity2_data['section_count'] == 2  # Two headers (# Entity2, ## Section 1)

    def test_collect_curriculum_data_empty_dir(self, tmp_path):
        """Test collecting data from empty directory."""
        result = visualizations.collect_curriculum_data(tmp_path)
        assert result == []

    def test_collect_curriculum_data_no_curriculum_files(self, tmp_path):
        """Test collecting data when no curriculum files exist."""
        # Create entity directory but no curriculum files
        entity_dir = tmp_path / "entity1"
        entity_dir.mkdir()
        (entity_dir / "other_file.md").write_text("Not a curriculum file")
        
        result = visualizations.collect_curriculum_data(tmp_path)
        assert result == []


class TestMainFunction:
    """Test main function integration."""

    @patch('visualizations.create_curriculum_metrics_chart')
    @patch('visualizations.create_curriculum_structure_mermaid')
    @patch('visualizations.create_curriculum_flow_mermaid')
    @patch('visualizations.write_text')
    @patch('visualizations.common_setup_logging')
    def test_main_successful_execution(
        self,
        mock_logging,
        mock_write_text,
        mock_flow_mermaid,
        mock_structure_mermaid,
        mock_metrics_chart,
        tmp_path
    ):
        """Test main function with successful execution."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_structure_mermaid.return_value = "graph TB..."
        mock_flow_mermaid.return_value = "flowchart TD..."
        
        # Create test curriculum data
        entity_dir = tmp_path / "test_entity"
        entity_dir.mkdir()
        curriculum_content = """# Test Curriculum
## Section 1
Content here.
## Section 2
More content.
"""
        (entity_dir / "complete_curriculum_20240101_120000.md").write_text(curriculum_content)
        
        # Run main function
        visualizations.main(str(tmp_path), str(tmp_path / "output"))
        
        # Verify calls
        mock_metrics_chart.assert_called_once()
        mock_structure_mermaid.assert_called_once()
        mock_flow_mermaid.assert_called_once()
        assert mock_write_text.call_count >= 2  # At least structure diagram + one flow diagram

    @patch('visualizations.common_setup_logging')
    def test_main_no_curriculum_files(
        self,
        mock_logging,
        tmp_path
    ):
        """Test main function when no curriculum files are found."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        
        # Run main function with empty directory
        visualizations.main(str(tmp_path), str(tmp_path / "output"))
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        assert "No curriculum files found" in mock_logger.warning.call_args[0][0]

    @patch('visualizations.collect_curriculum_data')
    @patch('visualizations.common_setup_logging')
    def test_main_data_collection_error(
        self,
        mock_logging,
        mock_collect_data,
        tmp_path
    ):
        """Test main function when data collection fails."""
        # Setup mocks
        mock_logger = Mock()
        mock_logging.return_value = mock_logger
        mock_collect_data.side_effect = Exception("Data collection failed")
        
        # Run main function and expect exception
        with pytest.raises(Exception, match="Data collection failed"):
            visualizations.main(str(tmp_path), str(tmp_path / "output"))
        
        mock_logger.error.assert_called()
        assert "Error generating visualizations" in mock_logger.error.call_args[0][0]


@pytest.fixture
def sample_curriculum_content():
    """Fixture providing sample curriculum content."""
    return """# Active Inference for Data Scientists

## Learning Objectives
- Understand the Free Energy Principle
- Apply Active Inference to machine learning
- Implement basic algorithms

## Introduction
Active Inference is a powerful framework...

## Mathematical Framework
The mathematical foundation involves:

```python
import numpy as np

def free_energy(beliefs, observations):
    return np.sum(beliefs * np.log(beliefs / observations))
```

Mathematical expressions: $F = \\mathbb{E}[\\log q(x)] - \\mathbb{E}[\\log p(x,y)]$

## Applications
- Robotics
- Cognitive modeling  
- Machine learning

## Advanced Topics
Research directions and future work.
"""


class TestIntegration:
    """Integration tests using realistic data."""

    def test_end_to_end_processing(self, tmp_path, sample_curriculum_content):
        """Test complete processing pipeline."""
        # Setup test data
        entity_dir = tmp_path / "data_scientist"
        entity_dir.mkdir()
        (entity_dir / "complete_curriculum_20240101_120000.md").write_text(sample_curriculum_content)
        
        output_dir = tmp_path / "output"
        
        # Run main function
        with patch('visualizations.common_setup_logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.return_value = mock_logger
            
            visualizations.main(str(tmp_path), str(output_dir))
        
        # Verify outputs were created
        assert (output_dir / "curriculum_metrics.png").exists()
        assert (output_dir / "curriculum_structure.mmd").exists()
        assert (output_dir / "data_scientist_flow.mmd").exists()
        assert (output_dir / "curriculum_metrics.json").exists()
        
        # Verify JSON content
        with open(output_dir / "curriculum_metrics.json", 'r') as f:
            metrics_data = json.load(f)
        
        assert len(metrics_data) == 1
        assert metrics_data[0]['entity_name'] == 'data_scientist'
        assert metrics_data[0]['section_count'] == 4  # Excluding the main title
        assert metrics_data[0]['objectives_count'] == 3
        assert metrics_data[0]['code_block_count'] == 1
        assert metrics_data[0]['math_expressions_count'] == 1
