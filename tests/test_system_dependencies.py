"""Tests for system dependencies module."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import src.system.dependencies as deps
from src.system.dependencies import (
    DependencyCheck,
    DependencyReport,
    check_environment_variables,
    check_project_files,
    check_python_package,
    check_system_tool,
    check_uv_environment,
    format_dependency_report,
    get_installation_instructions,
    get_optional_python_packages,
    get_optional_system_tools,
    get_required_python_packages,
    get_required_system_tools,
    run_comprehensive_dependency_check,
    validate_api_keys,
)


class TestDependencyCheck:
    """Test DependencyCheck dataclass."""
    
    def test_dependency_check_creation(self):
        """Test DependencyCheck object creation."""
        check = DependencyCheck(name="test-package", required=True, available=False)
        
        assert check.name == "test-package"
        assert check.required is True
        assert check.available is False
        assert check.version is None
        assert check.error_message is None
        assert check.install_hint is None
    
    def test_dependency_check_complete(self):
        """Test DependencyCheck with all fields."""
        check = DependencyCheck(
            name="test-package",
            required=True,
            available=True,
            version="1.0.0",
            error_message=None,
            install_hint="pip install test-package",
        )
        
        assert check.name == "test-package"
        assert check.required is True
        assert check.available is True
        assert check.version == "1.0.0"
        assert check.install_hint == "pip install test-package"


class TestDependencyReport:
    """Test DependencyReport dataclass."""
    
    def test_dependency_report_creation(self):
        """Test DependencyReport object creation."""
        report = DependencyReport()
        
        assert isinstance(report.python_packages, list)
        assert isinstance(report.system_tools, list)
        assert isinstance(report.optional_tools, list)
        assert isinstance(report.missing_required, list)
        assert report.all_required_available is False
    
    def test_dependency_report_with_data(self):
        """Test DependencyReport with data."""
        check1 = DependencyCheck("pkg1", True, True)
        check2 = DependencyCheck("pkg2", True, False)
        
        report = DependencyReport(
            python_packages=[check1, check2],
            all_required_available=False,
            missing_required=["pkg2"],
        )
        
        assert len(report.python_packages) == 2
        assert report.all_required_available is False
        assert "pkg2" in report.missing_required


class TestCheckPythonPackage:
    """Test check_python_package function."""
    
    @patch('importlib.import_module')
    def test_check_python_package_available(self, mock_import):
        """Test checking available Python package."""
        # Mock successful import
        mock_module = Mock()
        mock_module.__version__ = "1.2.3"
        mock_import.return_value = mock_module
        
        check = check_python_package("test-package")
        
        assert check.name == "test-package"
        assert check.required is True
        assert check.available is True
        assert check.version == "1.2.3"
        assert check.error_message is None
    
    @patch('importlib.import_module', side_effect=ImportError("No module named 'test-package'"))
    def test_check_python_package_not_available(self, mock_import):
        """Test checking unavailable Python package."""
        check = check_python_package("test-package")
        
        assert check.name == "test-package"
        assert check.required is True
        assert check.available is False
        assert check.version is None
        assert "No module named 'test-package'" in check.error_message
        assert "pip install test-package" in check.install_hint
    
    @patch('importlib.import_module')
    def test_check_python_package_no_version(self, mock_import):
        """Test checking package without version attribute."""
        # Mock module without __version__
        mock_module = Mock(spec=[])  # No attributes
        mock_import.return_value = mock_module
        
        # Patch version on the module used by implementation avoiding resolve_name
        with patch.object(deps.importlib_metadata, 'version', return_value="2.0.0"):
            check = check_python_package("test-package")
        
        assert check.available is True
        assert check.version == "2.0.0"
    
    @patch('importlib.import_module')
    def test_check_python_package_version_fallback(self, mock_import):
        """Test checking package with version fallback."""
        mock_module = Mock(spec=[])  # No version attributes
        mock_import.return_value = mock_module
        
        # Patch version on the module used by implementation avoiding resolve_name
        with patch.object(deps.importlib_metadata, 'version', side_effect=Exception("No metadata")):
            check = check_python_package("test-package")
        
        assert check.available is True
        assert check.version == "unknown"
    
    def test_check_python_package_optional(self):
        """Test checking optional package."""
        with patch('importlib.import_module', side_effect=ImportError()):
            check = check_python_package("optional-package", required=False)
        
        assert check.required is False
        assert check.available is False


class TestCheckSystemTool:
    """Test check_system_tool function."""
    
    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('subprocess.run')
    def test_check_system_tool_available(self, mock_run, mock_which):
        """Test checking available system tool."""
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.30.0\n")
        
        check = check_system_tool("git")
        
        assert check.name == "git"
        assert check.required is True
        assert check.available is True
        assert check.version == "git version 2.30.0"
        assert check.error_message is None
    
    @patch('shutil.which', return_value=None)
    def test_check_system_tool_not_available(self, mock_which):
        """Test checking unavailable system tool."""
        check = check_system_tool("nonexistent-tool")
        
        assert check.name == "nonexistent-tool"
        assert check.required is True
        assert check.available is False
        assert check.version is None
        assert "not found in PATH" in check.error_message
        assert "Install nonexistent-tool" in check.install_hint
    
    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_check_system_tool_version_error(self, mock_run, mock_which):
        """Test checking tool with version command error."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Unknown option")
        
        check = check_system_tool("tool")
        
        assert check.available is True
        assert check.version == "Unknown option"
    
    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired("tool", 5))
    def test_check_system_tool_timeout(self, mock_run, mock_which):
        """Test checking tool that times out."""
        check = check_system_tool("slow-tool")
        
        assert check.available is True
        assert check.version == "timeout"
    
    def test_check_system_tool_optional(self):
        """Test checking optional system tool."""
        with patch('shutil.which', return_value=None):
            check = check_system_tool("optional-tool", required=False)
        
        assert check.required is False
        assert check.available is False


class TestRequiredPackages:
    """Test required package listing functions."""
    
    def test_get_required_python_packages(self):
        """Test getting required Python packages."""
        packages = get_required_python_packages()
        
        assert isinstance(packages, list)
        assert len(packages) > 0
        assert "openai" in packages
        assert "python-dotenv" in packages
        assert "pyyaml" in packages
    
    def test_get_optional_python_packages(self):
        """Test getting optional Python packages."""
        packages = get_optional_python_packages()
        
        assert isinstance(packages, list)
        assert len(packages) > 0
        assert "psutil" in packages
        assert "rich" in packages
    
    def test_get_required_system_tools(self):
        """Test getting required system tools."""
        tools = get_required_system_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert ("git", "--version") in tools
        assert ("python", "--version") in tools
    
    def test_get_optional_system_tools(self):
        """Test getting optional system tools."""
        tools = get_optional_system_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert ("uv", "--version") in tools
        assert ("make", "--version") in tools


class TestCheckUvEnvironment:
    """Test check_uv_environment function."""
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists', return_value=True)
    @patch('shutil.which', return_value='/usr/bin/uv')
    @patch('src.system.dependencies.sys.prefix', '/test/.venv')
    def test_check_uv_environment_success(self, *args):
        """Test successful uv environment check."""
        check = check_uv_environment()
        
        assert check.name == "uv-environment"
        assert check.required is False
        assert check.available is True
        assert "/test/.venv" in check.version
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists', return_value=False)
    def test_check_uv_environment_no_lock_file(self, mock_exists, mock_repo_root):
        """Test uv environment check without lock file."""
        check = check_uv_environment()
        
        assert check.available is False
        assert "uv.lock file not found" in check.error_message
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists', return_value=True)
    @patch('shutil.which', return_value=None)
    def test_check_uv_environment_no_uv_tool(self, mock_which, mock_exists, mock_repo_root):
        """Test uv environment check without uv tool."""
        check = check_uv_environment()
        
        assert check.available is False
        assert "uv tool not found" in check.error_message
        assert "Install uv:" in check.install_hint
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists', return_value=True)
    @patch('shutil.which', return_value='/usr/bin/uv')
    @patch('src.system.dependencies.sys.prefix', '/usr')
    def test_check_uv_environment_not_in_venv(self, *args):
        """Test uv environment check when not in venv."""
        check = check_uv_environment()
        
        assert check.available is False
        assert "Not running in uv-managed" in check.error_message


class TestCheckProjectFiles:
    """Test check_project_files function."""
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_check_project_files_all_exist(self, mock_stat, mock_exists, mock_repo_root):
        """Test checking project files when all exist."""
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1024)
        
        checks = check_project_files()
        
        assert len(checks) > 0
        assert all(check.available for check in checks)
        assert all("Size: 1024 bytes" in check.version for check in checks)
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists', return_value=False)
    def test_check_project_files_missing(self, mock_exists, mock_repo_root):
        """Test checking project files when some are missing."""
        checks = check_project_files()
        
        assert len(checks) > 0
        assert all(not check.available for check in checks)
        assert all("Required file not found" in check.error_message for check in checks)


class TestCheckEnvironmentVariables:
    """Test check_environment_variables function."""
    
    @patch.dict('os.environ', {
        'PERPLEXITY_API_KEY': 'test-key-123',
        'OPENROUTER_API_KEY': 'another-key-456',
    })
    def test_check_environment_variables_all_set(self):
        """Test checking environment variables when all are set."""
        checks = check_environment_variables()
        
        required_checks = [c for c in checks if c.required]
        optional_checks = [c for c in checks if not c.required]
        
        assert len(required_checks) >= 2
        assert all(check.available for check in required_checks)
        assert all("Set (" in check.version for check in required_checks)
    
    @patch.dict('os.environ', {}, clear=True)
    def test_check_environment_variables_none_set(self):
        """Test checking environment variables when none are set."""
        checks = check_environment_variables()
        
        required_checks = [c for c in checks if c.required]
        
        assert len(required_checks) >= 2
        assert all(not check.available for check in required_checks)
        assert all("Required environment variable not set" in check.error_message for check in required_checks)
    
    @patch.dict('os.environ', {'PERPLEXITY_MODEL': 'custom-model'})
    def test_check_environment_variables_optional_set(self):
        """Test checking optional environment variables."""
        checks = check_environment_variables()
        
        optional_checks = [c for c in checks if not c.required and c.name == "env.PERPLEXITY_MODEL"]
        
        assert len(optional_checks) == 1
        assert optional_checks[0].available is True
        assert optional_checks[0].version == "custom-model"


class TestComprehensiveDependencyCheck:
    """Test run_comprehensive_dependency_check function."""
    
    @patch('src.system.dependencies.get_required_python_packages', return_value=['test-pkg'])
    @patch('src.system.dependencies.get_optional_python_packages', return_value=['opt-pkg'])
    @patch('src.system.dependencies.get_required_system_tools', return_value=[('git', '--version')])
    @patch('src.system.dependencies.get_optional_system_tools', return_value=[('make', '--version')])
    @patch('src.system.dependencies.check_python_package')
    @patch('src.system.dependencies.check_system_tool')
    @patch('src.system.dependencies.check_uv_environment')
    @patch('src.system.dependencies.check_project_files')
    @patch('src.system.dependencies.check_environment_variables')
    def test_comprehensive_check_all_available(self, mock_env, mock_files, mock_uv, mock_sys_tool, mock_py_pkg, *args):
        """Test comprehensive dependency check when all are available."""
        # Mock all checks to return available
        mock_py_pkg.return_value = DependencyCheck("test-pkg", True, True)
        mock_sys_tool.return_value = DependencyCheck("git", True, True)
        mock_uv.return_value = DependencyCheck("uv-environment", False, True)
        mock_files.return_value = [DependencyCheck("pyproject.toml", True, True)]
        mock_env.return_value = [DependencyCheck("env.PERPLEXITY_API_KEY", True, True)]
        
        report = run_comprehensive_dependency_check()
        
        assert isinstance(report, DependencyReport)
        assert report.all_required_available is True
        assert len(report.missing_required) == 0
        assert len(report.python_packages) >= 1
        assert len(report.system_tools) >= 1
        assert len(report.optional_tools) >= 1
    
    @patch('src.system.dependencies.get_required_python_packages', return_value=['missing-pkg'])
    @patch('src.system.dependencies.check_python_package')
    def test_comprehensive_check_missing_required(self, mock_py_pkg, *args):
        """Test comprehensive dependency check with missing required packages."""
        mock_py_pkg.return_value = DependencyCheck("missing-pkg", True, False)
        
        with patch('src.system.dependencies.get_optional_python_packages', return_value=[]):
            with patch('src.system.dependencies.get_required_system_tools', return_value=[]):
                with patch('src.system.dependencies.get_optional_system_tools', return_value=[]):
                    with patch('src.system.dependencies.check_uv_environment') as mock_uv:
                        with patch('src.system.dependencies.check_project_files', return_value=[]):
                            with patch('src.system.dependencies.check_environment_variables', return_value=[]):
                                mock_uv.return_value = DependencyCheck("uv", False, True)
                                
                                report = run_comprehensive_dependency_check()
        
        assert report.all_required_available is False
        assert "python:missing-pkg" in report.missing_required


class TestFormatDependencyReport:
    """Test format_dependency_report function."""
    
    def test_format_dependency_report_basic(self):
        """Test formatting basic dependency report."""
        report = DependencyReport(
            python_packages=[
                DependencyCheck("available-pkg", True, True, version="1.0.0"),
                DependencyCheck("missing-pkg", True, False, error_message="Not found"),
            ],
            system_tools=[
                DependencyCheck("git", True, True, version="git 2.30.0"),
            ],
            all_required_available=False,
            missing_required=["python:missing-pkg"],
        )
        
        formatted = format_dependency_report(report)
        
        assert "DEPENDENCY CHECK REPORT" in formatted
        assert "MISSING REQUIRED DEPENDENCIES" in formatted
        assert "available-pkg" in formatted
        assert "missing-pkg" in formatted
        assert "git" in formatted
        assert "1.0.0" in formatted
        assert "Not found" in formatted
    
    def test_format_dependency_report_all_available(self):
        """Test formatting dependency report when all are available."""
        report = DependencyReport(
            python_packages=[DependencyCheck("pkg", True, True, version="1.0.0")],
            all_required_available=True,
            missing_required=[],
        )
        
        formatted = format_dependency_report(report)
        
        assert "ALL REQUIRED DEPENDENCIES AVAILABLE" in formatted
        assert "✅" in formatted
    
    def test_format_dependency_report_with_optional(self):
        """Test formatting dependency report with optional tools."""
        report = DependencyReport(
            optional_tools=[
                DependencyCheck("optional-tool", False, True, version="1.0"),
                DependencyCheck("missing-optional", False, False, install_hint="Install it"),
            ]
        )
        
        formatted = format_dependency_report(report, show_optional=True)
        
        assert "OPTIONAL TOOLS" in formatted
        assert "optional-tool" in formatted
        assert "missing-optional" in formatted
        assert "Install it" in formatted
    
    def test_format_dependency_report_no_optional(self):
        """Test formatting dependency report without showing optional."""
        report = DependencyReport(
            optional_tools=[DependencyCheck("optional", False, False)]
        )
        
        formatted = format_dependency_report(report, show_optional=False)
        
        assert "OPTIONAL TOOLS" not in formatted


class TestGetInstallationInstructions:
    """Test get_installation_instructions function."""
    
    def test_get_installation_instructions(self):
        """Test getting installation instructions."""
        instructions = get_installation_instructions()
        
        assert isinstance(instructions, str)
        assert "INSTALLATION INSTRUCTIONS" in instructions
        assert "uv sync" in instructions
        assert "PERPLEXITY_API_KEY" in instructions
        assert "OPENROUTER_API_KEY" in instructions
        assert ".env" in instructions


class TestValidateApiKeys:
    """Test validate_api_keys function."""
    
    @patch('src.perplexity.clients.build_perplexity_client')
    @patch('src.perplexity.clients.build_openrouter_client')
    def test_validate_api_keys_success(self, mock_openrouter, mock_perplexity):
        """Test successful API key validation."""
        # Mock successful API calls
        mock_perplexity_client = Mock()
        mock_perplexity_response = Mock()
        mock_perplexity_response.choices = ["response"]
        mock_perplexity_client.chat.completions.create.return_value = mock_perplexity_response
        mock_perplexity.return_value = mock_perplexity_client
        
        mock_openrouter_client = Mock()
        mock_openrouter_response = Mock()
        mock_openrouter_response.choices = ["response"]
        mock_openrouter_client.chat.completions.create.return_value = mock_openrouter_response
        mock_openrouter.return_value = mock_openrouter_client
        
        results = validate_api_keys()
        
        assert results["perplexity"] is True
        assert results["openrouter"] is True
    
    @patch('src.perplexity.clients.build_perplexity_client', side_effect=Exception("API error"))
    @patch('src.perplexity.clients.build_openrouter_client', side_effect=Exception("API error"))
    def test_validate_api_keys_failure(self, mock_openrouter, mock_perplexity):
        """Test API key validation failures."""
        results = validate_api_keys()
        
        assert results["perplexity"] is False
        assert results["openrouter"] is False
    
    @patch('src.perplexity.clients.build_perplexity_client')
    @patch('src.perplexity.clients.build_openrouter_client')
    def test_validate_api_keys_empty_response(self, mock_openrouter, mock_perplexity):
        """Test API key validation with empty responses."""
        # Mock empty responses
        mock_perplexity_client = Mock()
        mock_perplexity_response = Mock()
        mock_perplexity_response.choices = []
        mock_perplexity_client.chat.completions.create.return_value = mock_perplexity_response
        mock_perplexity.return_value = mock_perplexity_client
        
        mock_openrouter_client = Mock()
        mock_openrouter_response = Mock()
        mock_openrouter_response.choices = []
        mock_openrouter_client.chat.completions.create.return_value = mock_openrouter_response
        mock_openrouter.return_value = mock_openrouter_client
        
        results = validate_api_keys()
        
        assert results["perplexity"] is False
        assert results["openrouter"] is False


@pytest.mark.integration
class TestDependenciesIntegration:
    """Integration tests for dependencies module."""
    
    def test_real_python_package_check(self):
        """Test checking a real Python package."""
        # Test with a package that should be available (pytest is used in tests)
        check = check_python_package("pytest", required=False)
        
        assert check.name == "pytest"
        assert check.available is True
        assert check.version is not None
        assert "pytest" in check.version.lower() or check.version != "unknown"
    
    def test_real_system_tool_check(self):
        """Test checking a real system tool."""
        # Test with Python which should be available
        check = check_system_tool("python", required=True)
        
        assert check.name == "python"
        assert check.available is True
        assert check.version is not None
        assert "python" in check.version.lower() or "Python" in check.version
    
    def test_comprehensive_check_performance(self):
        """Test that comprehensive check completes in reasonable time."""
        import time
        
        start_time = time.time()
        report = run_comprehensive_dependency_check()
        elapsed = time.time() - start_time
        
        assert isinstance(report, DependencyReport)
        assert elapsed < 30.0  # Should complete within 30 seconds
        assert len(report.python_packages) > 0
        assert len(report.system_tools) > 0
    
    @pytest.mark.skipif(not shutil.which("git"), reason="git not available")
    def test_git_available_in_real_environment(self):
        """Test that git is detected as available in real environment."""
        check = check_system_tool("git")
        
        assert check.available is True
        assert "git" in check.version.lower()
