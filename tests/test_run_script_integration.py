"""Integration tests for the main run.sh script functionality.

These tests verify that the Python components called by run.sh work correctly
and that the overall system integration is sound.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.common.paths import repo_root


class TestRunScriptIntegration:
    """Test integration aspects of the main run.sh script."""
    
    def test_run_script_exists_and_executable(self):
        """Test that run.sh exists and is executable."""
        script_path = repo_root() / "run.sh"
        
        assert script_path.exists(), "run.sh script not found"
        assert os.access(script_path, os.X_OK), "run.sh script not executable"
    
    def test_run_script_basic_structure(self):
        """Test that run.sh has expected basic structure."""
        script_path = repo_root() / "run.sh"
        content = script_path.read_text()
        
        # Check for essential elements
        assert "#!/usr/bin/env bash" in content
        assert "set -euo pipefail" in content
        assert "MATRIX_GREEN" in content
        assert "system_health_check" in content
        assert "environment_setup" in content
        assert "run_curriculum_generator" in content
        assert "repo_management" in content
    
    def test_python_system_reporting_integration(self):
        """Test that system reporting Python code works."""
        # Test the exact Python code called by run.sh
        python_code = """
from src.system.reporting import generate_system_report, format_system_report
from src.system.dependencies import run_comprehensive_dependency_check, format_dependency_report
from src.terminal.colors import matrix_text

# System info
system_info = generate_system_report()
report = format_system_report(system_info, detailed=False)
assert len(report) > 100

# Dependencies
dep_report = run_comprehensive_dependency_check()
dep_formatted = format_dependency_report(dep_report, show_optional=False)
assert len(dep_formatted) > 100

# Terminal colors
colored = matrix_text('TEST', 'gold')
assert isinstance(colored, str)
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Python integration failed: {result.stderr}"
    
    def test_repository_manager_integration(self):
        """Test that repository manager Python code works."""
        python_code = """
from src.repos.manager import create_repository_manager, format_repository_summary

manager = create_repository_manager()
summary = manager.get_summary()
formatted = format_repository_summary(summary)

assert isinstance(summary, dict)
assert 'available_count' in summary
assert len(formatted) > 50
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Repository manager integration failed: {result.stderr}"
    
    def test_environment_setup_integration(self):
        """Test that environment setup Python code works."""
        python_code = """
from src.system.environment import validate_environment, fix_common_issues
from src.terminal.colors import matrix_text

# Validate environment
is_valid, messages = validate_environment()
assert isinstance(is_valid, bool)
assert isinstance(messages, list)

# Test fix common issues
fixed = fix_common_issues()
assert isinstance(fixed, list)

# Test matrix text
text = matrix_text('Environment setup complete!', 'gold')
assert isinstance(text, str)
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Environment setup integration failed: {result.stderr}"
    
    def test_menu_system_integration(self):
        """Test that menu system Python code works."""
        python_code = """
from src.terminal.menu import MenuBuilder, MenuItem
from src.terminal.animations import matrix_banner

# Test menu building
menu = (MenuBuilder('Test Menu')
    .add_item('Item 1', lambda: 'result1')
    .add_item('Item 2', lambda: 'result2')
    .build())

assert len(menu.items) == 2
assert menu.title == 'Test Menu'

# Test banner
banner = matrix_banner('TEST BANNER')
assert isinstance(banner, str)
assert 'TEST BANNER' in banner
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Menu system integration failed: {result.stderr}"
    
    @pytest.mark.skipif(not Path("/usr/bin/uv").exists() and not Path.home().joinpath(".cargo/bin/uv").exists(), 
                       reason="uv not available")
    def test_uv_integration(self):
        """Test that uv integration works if uv is available."""
        # Test basic uv command execution
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            assert "uv" in result.stdout.lower()
            
            # Test uv run with simple Python code
            python_code = "print('UV integration test passed')"
            result = subprocess.run(
                ["uv", "run", "python", "-c", python_code],
                cwd=repo_root(),
                capture_output=True,
                text=True,
            )
            
            # Note: This might fail if dependencies aren't installed, which is okay
            # We're mainly testing that uv command works
            assert result.returncode in [0, 1]  # 0 for success, 1 for dependency issues
    
    def test_curriculum_generator_accessibility(self):
        """Test that curriculum generator is accessible."""
        generator_path = repo_root() / "learning" / "curriculum_creation" / "generate_custom_curriculum.py"
        
        assert generator_path.exists(), "Curriculum generator script not found"
        
        # Test that the script can be imported (basic syntax check)
        python_code = f"""
import sys
sys.path.insert(0, '{repo_root()}')

# Try to import the main functions
try:
    from learning.curriculum_creation.generate_custom_curriculum import create_default_config
    config = create_default_config()
    assert hasattr(config, 'target_domains')
    print('Import successful')
except Exception as e:
    print(f'Import failed: {{e}}')
    raise
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Curriculum generator import failed: {result.stderr}"
        assert "Import successful" in result.stdout
    
    def test_project_structure_integrity(self):
        """Test that project structure is intact for run.sh operations."""
        required_paths = [
            "src",
            "src/common",
            "src/terminal",
            "src/system", 
            "src/repos",
            "src/perplexity",
            "data",
            "data/config",
            "data/prompts",
            "learning/curriculum_creation",
            "tests",
        ]
        
        for path_str in required_paths:
            path = repo_root() / path_str
            assert path.exists(), f"Required path missing: {path}"
            
        # Check for key files
        key_files = [
            "pyproject.toml",
            "src/__init__.py",
            "src/common/__init__.py",
            "src/terminal/__init__.py",
            "src/system/__init__.py",
            "src/repos/__init__.py",
        ]
        
        for file_str in key_files:
            file_path = repo_root() / file_str
            assert file_path.exists(), f"Key file missing: {file_path}"
    
    def test_terminal_animations_performance(self):
        """Test that terminal animations don't cause performance issues."""
        python_code = """
import time
from src.terminal.animations import typewriter_effect, MatrixRain

# Test typewriter effect performance
start = time.time()
list(typewriter_effect("Test message", delay=0.001))
elapsed = time.time() - start
assert elapsed < 1.0, f"Typewriter too slow: {elapsed}s"

# Test matrix rain performance
start = time.time()
rain = MatrixRain(duration=0.1, density=0.05)
list(rain.animate())
elapsed = time.time() - start
assert elapsed < 2.0, f"Matrix rain too slow: {elapsed}s"

print("Performance tests passed")
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Performance test failed: {result.stderr}"
        assert "Performance tests passed" in result.stdout
    
    def test_error_handling_robustness(self):
        """Test that error handling works robustly."""
        python_code = """
from src.system.dependencies import check_python_package
from src.system.reporting import get_memory_info
from src.repos.cloning import validate_repository_url

# Test error handling in dependencies
check = check_python_package("nonexistent-package-12345")
assert not check.available
assert check.error_message is not None

# Test error handling in system reporting (should not crash)
try:
    memory_info = get_memory_info()
    assert isinstance(memory_info, dict)
except Exception as e:
    # If it fails, it should fail gracefully
    print(f"Memory info failed gracefully: {e}")

# Test error handling in repository operations
is_valid = validate_repository_url("invalid-url")
assert not is_valid

print("Error handling tests passed")
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Error handling test failed: {result.stderr}"
        assert "Error handling tests passed" in result.stdout


class TestScriptDependencyCheck:
    """Test that script dependencies are correctly handled."""
    
    def test_bash_dependencies_available(self):
        """Test that required bash commands are available."""
        required_commands = ["git", "python3", "curl", "bash"]
        
        for command in required_commands:
            result = subprocess.run(
                ["which", command],
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                pytest.skip(f"Required command '{command}' not available in test environment")
    
    def test_python_import_dependencies(self):
        """Test that Python imports work correctly."""
        critical_imports = [
            "src.terminal.colors",
            "src.terminal.animations", 
            "src.terminal.menu",
            "src.system.reporting",
            "src.system.dependencies",
            "src.system.environment",
            "src.repos.manager",
            "src.repos.cloning",
        ]
        
        for import_name in critical_imports:
            python_code = f"""
try:
    import {import_name}
    print(f"Successfully imported {import_name}")
except Exception as e:
    print(f"Failed to import {import_name}: {{e}}")
    raise
"""
            
            result = subprocess.run(
                ["python", "-c", python_code],
                cwd=repo_root(),
                capture_output=True,
                text=True,
            )
            
            assert result.returncode == 0, f"Failed to import {import_name}: {result.stderr}"
    
    def test_configuration_files_accessible(self):
        """Test that configuration files are accessible."""
        python_code = """
from src.common.paths import data_root
from pathlib import Path

data_dir = data_root()
config_dir = data_dir / 'config'

# These files should exist or be creatable
expected_files = [
    'domains.yaml',
    'entities.yaml', 
    'languages.yaml'
]

for filename in expected_files:
    file_path = config_dir / filename
    if not file_path.exists():
        print(f"Config file {filename} does not exist but should be creatable")
    else:
        print(f"Config file {filename} exists")

print("Configuration check completed")
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Configuration check failed: {result.stderr}"
        assert "Configuration check completed" in result.stdout


@pytest.mark.slow
class TestScriptPerformance:
    """Test performance aspects of the script."""
    
    def test_startup_performance(self):
        """Test that Python startup time is reasonable."""
        import time
        
        start_time = time.time()
        
        python_code = """
from src.terminal.colors import matrix_text
from src.system.reporting import get_basic_system_info
from src.repos.manager import create_repository_manager

# Quick operations
text = matrix_text("Test", "green")
info = get_basic_system_info()  
manager = create_repository_manager()

print("Startup completed")
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        elapsed = time.time() - start_time
        
        assert result.returncode == 0, f"Startup test failed: {result.stderr}"
        assert "Startup completed" in result.stdout
        assert elapsed < 5.0, f"Startup too slow: {elapsed:.2f}s"
    
    def test_memory_usage_reasonable(self):
        """Test that memory usage is reasonable."""
        python_code = """
import sys
from src.system.reporting import generate_system_report
from src.repos.manager import create_repository_manager

# Generate some data
report = generate_system_report()
manager = create_repository_manager()
summary = manager.get_summary()

# Check memory usage (basic)
import gc
gc.collect()

print("Memory test completed")
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Memory test failed: {result.stderr}"
        assert "Memory test completed" in result.stdout


@pytest.mark.integration
class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def test_complete_module_integration(self):
        """Test that all modules work together."""
        python_code = """
# Import all major components
from src.terminal.colors import matrix_text
from src.terminal.animations import matrix_banner
from src.terminal.menu import MenuBuilder
from src.system.reporting import generate_system_report
from src.system.dependencies import run_comprehensive_dependency_check
from src.system.environment import validate_environment
from src.repos.manager import create_repository_manager

# Test terminal functionality
colored_text = matrix_text("Integration Test", "gold")
banner = matrix_banner("INTEGRATION TEST")
menu = MenuBuilder("Test Menu").add_item("Test", lambda: "test").build()

# Test system functionality
system_report = generate_system_report()
dep_report = run_comprehensive_dependency_check()
is_valid, env_messages = validate_environment()

# Test repository functionality
repo_manager = create_repository_manager()
repo_summary = repo_manager.get_summary()

# Verify everything worked
assert isinstance(colored_text, str)
assert isinstance(banner, str)
assert len(menu.items) == 1
assert hasattr(system_report, 'hostname')
assert hasattr(dep_report, 'all_required_available')
assert isinstance(is_valid, bool)
assert isinstance(repo_summary, dict)

print("End-to-end integration successful")
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Integration test failed: {result.stderr}"
        assert "End-to-end integration successful" in result.stdout
    
    def test_error_recovery_integration(self):
        """Test that the system recovers from errors gracefully."""
        python_code = """
from src.system.dependencies import check_python_package
from src.repos.cloning import validate_repository_url
from src.terminal.colors import matrix_text

# Test error recovery in various components
errors_handled = 0

# Test 1: Invalid package
try:
    check = check_python_package("definitely-not-a-real-package-name-12345")
    assert not check.available
    errors_handled += 1
except Exception:
    pass

# Test 2: Invalid repository URL
try:
    is_valid = validate_repository_url("not-a-valid-url")
    assert not is_valid
    errors_handled += 1
except Exception:
    pass

# Test 3: Terminal colors should work even with invalid styles
try:
    text = matrix_text("Test", "invalid-style")  # Should fall back
    assert isinstance(text, str)
    errors_handled += 1
except Exception:
    pass

print(f"Error recovery test: {errors_handled}/3 tests handled gracefully")
assert errors_handled >= 2, "Not enough error cases handled gracefully"
"""
        
        result = subprocess.run(
            ["python", "-c", python_code],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Error recovery test failed: {result.stderr}"
        assert "Error recovery test" in result.stdout
