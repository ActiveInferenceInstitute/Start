"""Integration tests for the curriculum creation scripts.

These tests verify that the updated scripts work correctly together
and follow the expected patterns for data flow and error handling.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch


class TestScriptIntegration:
    """Integration tests for all curriculum scripts."""
    
    def test_script_imports(self):
        """Test that all scripts can be imported without errors."""
        import sys
        import importlib.util
        
        script_dir = Path(__file__).parent.parent / "learning" / "curriculum_creation"
        
        # Test each script can be imported
        scripts = [
            "1_Research_Domain.py",
            "1_Research_Entity.py", 
            "2_Write_Introduction.py",
            "3_Introduction_Visualizations.py",
            "4_Translate_Introductions.py"
        ]
        
        for script_name in scripts:
            script_path = script_dir / script_name
            assert script_path.exists(), f"Script {script_name} not found"
            
            # Load module
            module_name = script_name.replace("-", "_").replace(".py", "")
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            module = importlib.util.module_from_spec(spec)
            
            # Should be able to load without import errors
            try:
                spec.loader.exec_module(module)
                assert hasattr(module, 'main'), f"Script {script_name} missing main function"
            except ImportError as e:
                # Allow missing dependencies in testing environment
                if "matplotlib" in str(e) or "pandas" in str(e) or "seaborn" in str(e):
                    pass  # OK for testing environment
                else:
                    raise

    def test_data_paths_structure(self):
        """Test that data paths follow the expected structure."""
        from src.common.paths import (
            data_domain_research_dir,
            data_audience_research_dir,
            data_written_curriculums_dir,
            data_translated_curriculums_dir,
            data_visualizations_dir
        )
        
        # All data paths should be under the data/ directory
        data_dirs = [
            data_domain_research_dir(),
            data_audience_research_dir(),
            data_written_curriculums_dir(),
            data_translated_curriculums_dir(),
            data_visualizations_dir()
        ]
        
        for data_dir in data_dirs:
            assert "data/" in str(data_dir), f"Path {data_dir} not under data/ directory"
    
    def test_prompt_templates_exist(self):
        """Test that required prompt templates exist."""
        from src.common.prompts import list_prompt_templates
        
        templates = list_prompt_templates()
        
        required_templates = [
            "research_domain_analysis",
            "research_domain_curriculum", 
            "research_entity",
            "curriculum_section",
            "translation"
        ]
        
        for template in required_templates:
            assert template in templates, f"Required template {template} not found"

    def test_language_configuration(self):
        """Test that language configuration is properly loaded."""
        from src.config.languages import get_target_languages, get_script_mapping
        
        languages = get_target_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        
        # Test a few common languages have script mappings
        test_languages = ["Chinese", "Arabic", "Hindi"]
        for lang in test_languages:
            if lang in languages:
                script = get_script_mapping(lang)
                assert script != lang  # Should have a specific script mapping

    def test_client_configurations(self):
        """Test that client configurations are properly set up."""
        from src.perplexity.clients import PerplexityConfig, OpenRouterConfig
        
        # Test config dataclasses
        perplexity_config = PerplexityConfig(api_key="test")
        assert perplexity_config.api_key == "test"
        assert perplexity_config.base_url == "https://api.perplexity.ai"
        
        openrouter_config = OpenRouterConfig(api_key="test")
        assert openrouter_config.api_key == "test"
        assert openrouter_config.base_url == "https://openrouter.ai/api/v1"


def test_script_documentation():
    """Test that scripts have proper documentation."""
    import sys
    import importlib.util
    
    script_dir = Path(__file__).parent.parent / "learning" / "curriculum_creation"
    
    scripts = [
        "1_Research_Domain.py",
        "1_Research_Entity.py", 
        "2_Write_Introduction.py",
        "3_Introduction_Visualizations.py",
        "4_Translate_Introductions.py"
    ]
    
    for script_name in scripts:
        script_path = script_dir / script_name
        
        # Read script content
        content = script_path.read_text(encoding='utf-8')
        
        # Should have module docstring
        assert '"""' in content, f"Script {script_name} missing module docstring"
        
        # Should have main function
        assert "def main(" in content, f"Script {script_name} missing main function"
        
        # Main function should have docstring
        main_func_start = content.find("def main(")
        main_func_section = content[main_func_start:main_func_start + 500]
        assert '"""' in main_func_section, f"Main function in {script_name} missing docstring"


def test_error_handling_patterns():
    """Test that scripts follow consistent error handling patterns."""
    import sys
    import importlib.util
    
    script_dir = Path(__file__).parent.parent / "learning" / "curriculum_creation"
    
    scripts = [
        "1_Research_Domain.py",
        "1_Research_Entity.py", 
        "2_Write_Introduction.py",
        "4_Translate_Introductions.py"  # Skip visualization script due to matplotlib
    ]
    
    for script_name in scripts:
        script_path = script_dir / script_name
        content = script_path.read_text(encoding='utf-8')
        
        # Should have try/except in main function
        assert "try:" in content, f"Script {script_name} missing try/except blocks"
        assert "except Exception as e:" in content, f"Script {script_name} missing proper exception handling"
        
        # Should use logger
        assert "logger" in content, f"Script {script_name} not using logger"
        assert "logger.info" in content, f"Script {script_name} not logging info messages"
        assert "logger.error" in content, f"Script {script_name} not logging errors"


if __name__ == "__main__":
    # Simple test runner
    import traceback
    
    test_class = TestScriptIntegration()
    
    # Get all test methods
    test_methods = [
        method_name for method_name in dir(test_class)
        if method_name.startswith('test_')
    ]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            print(f"Running {method_name}...")
            method = getattr(test_class, method_name)
            method()
            print(f"✓ {method_name} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {method_name} failed: {e}")
            traceback.print_exc()
            failed += 1
    
    # Run standalone tests
    standalone_tests = [
        test_script_documentation,
        test_error_handling_patterns
    ]
    
    for test_func in standalone_tests:
        try:
            print(f"Running {test_func.__name__}...")
            test_func()
            print(f"✓ {test_func.__name__} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
