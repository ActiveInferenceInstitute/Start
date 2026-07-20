"""Dependency checking and validation utilities.

This module provides functionality to check for required system dependencies,
Python packages, and external tools needed by the project.
"""

from __future__ import annotations

import importlib
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from importlib import metadata as importlib_metadata
from typing import Any, Dict, List, Optional, Tuple

import tomllib

import src.common.paths as paths


@dataclass
class DependencyCheck:
    """Represents the result of a dependency check."""

    name: str
    required: bool
    available: bool
    version: Optional[str] = None
    error_message: Optional[str] = None
    install_hint: Optional[str] = None


@dataclass
class DependencyReport:
    """Complete dependency check report."""

    python_packages: List[DependencyCheck] = field(default_factory=list)
    system_tools: List[DependencyCheck] = field(default_factory=list)
    optional_tools: List[DependencyCheck] = field(default_factory=list)
    all_required_available: bool = False
    missing_required: List[str] = field(default_factory=list)


def check_python_package(
    package_name: str, required: bool = True, distribution_name: Optional[str] = None
) -> DependencyCheck:
    """Check if a Python package is available and get its version.

    Args:
        package_name: Name of the package to check
        required: Whether this package is required

    Returns:
        DependencyCheck result
    """
    check = DependencyCheck(name=package_name, required=required, available=False)

    try:
        module = importlib.import_module(package_name)
        check.available = True

        # Try to get version
        version_attrs = ["__version__", "VERSION", "version"]
        for attr in version_attrs:
            if hasattr(module, attr):
                check.version = str(getattr(module, attr))
                break

        if not check.version:
            # Try to get from distribution metadata (alias exposed on importlib)
            try:
                # Prefer importlib.metadata if present on importlib (easier to patch in tests)
                if hasattr(importlib, "metadata"):
                    # Access attribute via importlib to match patch('importlib.metadata.version')
                    check.version = importlib.metadata.version(  # type: ignore[attr-defined]
                        distribution_name or package_name
                    )
                else:
                    check.version = importlib_metadata.version(distribution_name or package_name)
            except Exception:
                check.version = "unknown"

    except ImportError as e:
        check.error_message = str(e)
        check.install_hint = f"pip install {package_name}"
    except Exception as e:
        check.error_message = f"Unexpected error: {e}"

    return check


def check_system_tool(
    tool_name: str, required: bool = True, version_flag: str = "--version"
) -> DependencyCheck:
    """Check if a system tool is available in PATH.

    Args:
        tool_name: Name of the tool to check
        required: Whether this tool is required
        version_flag: Flag to get version information

    Returns:
        DependencyCheck result
    """
    check = DependencyCheck(name=tool_name, required=required, available=False)

    # Check if tool is in PATH
    tool_path = shutil.which(tool_name)
    if not tool_path:
        check.error_message = f"{tool_name} not found in PATH"
        check.install_hint = f"Install {tool_name} and ensure it's in your PATH"
        return check

    check.available = True

    # Try to get version
    try:
        result = subprocess.run(
            [tool_name, version_flag],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Extract version from output (usually first line)
            version_line = result.stdout.strip().split("\n")[0]
            check.version = version_line
        else:
            # Try stderr for version
            version_line = result.stderr.strip().split("\n")[0]
            check.version = version_line if version_line else "unknown"
    except subprocess.TimeoutExpired:
        check.version = "timeout"
    except Exception as e:
        check.version = f"error: {e}"

    return check


def get_required_python_packages() -> List[str]:
    """Get list of required Python packages.

    Returns:
        List of required package names
    """
    return [import_name for import_name, _ in _required_python_package_specs()]


def _required_python_package_specs() -> list[tuple[str, str]]:
    """Read declared dependencies as ``(import_name, distribution_name)`` pairs."""
    root = paths.repo_root()
    with (root / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)
    distributions = project.get("project", {}).get("dependencies", [])
    if not isinstance(distributions, list):
        raise ValueError("project.dependencies must be a list")

    distribution_to_import = {
        "gitpython": "git",
        "python-dotenv": "dotenv",
        "pyyaml": "yaml",
        "scikit-learn": "sklearn",
        "adjusttext": "adjustText",
        "pillow": "PIL",
    }
    specs: list[tuple[str, str]] = []
    for requirement in distributions:
        if not isinstance(requirement, str) or not requirement.strip():
            raise ValueError(f"Invalid dependency declaration: {requirement!r}")
        distribution = re.split(r"[\[<>=!~;@\s]", requirement, maxsplit=1)[0].strip()
        if not distribution:
            raise ValueError(f"Invalid dependency declaration: {requirement!r}")
        import_name = distribution_to_import.get(distribution.casefold(), distribution)
        specs.append((import_name, distribution))
    return specs


def get_optional_python_packages() -> List[str]:
    """Get list of optional Python packages that enhance functionality.

    Returns:
        List of optional package names
    """
    optional_packages = [
        "psutil",  # For enhanced system monitoring
        "rich",  # For enhanced terminal output
        "tqdm",  # For progress bars
        "jupyter",  # For notebook support
        "ipython",  # For enhanced REPL
    ]

    return optional_packages


def get_required_system_tools() -> List[Tuple[str, str]]:
    """Get list of required system tools with version flags.

    Returns:
        List of (tool_name, version_flag) tuples
    """
    required_tools = [
        ("git", "--version"),
        ("python", "--version"),
    ]

    return required_tools


def get_optional_system_tools() -> List[Tuple[str, str]]:
    """Get list of optional system tools that enhance functionality.

    Returns:
        List of (tool_name, version_flag) tuples
    """
    optional_tools = [
        ("uv", "--version"),  # Python package manager
        ("make", "--version"),  # Build tool
        ("curl", "--version"),  # HTTP client
        ("jq", "--version"),  # JSON processor
        ("docker", "--version"),  # Container platform
    ]

    return optional_tools


def check_uv_environment() -> DependencyCheck:
    """Check if running in a uv-managed environment.

    Returns:
        DependencyCheck for uv environment
    """
    check = DependencyCheck(name="uv-environment", required=False, available=False)

    # Check for uv lock file
    uv_lock = paths.repo_root() / "uv.lock"
    if not uv_lock.exists():
        check.error_message = "uv.lock file not found"
        return check

    # Check if uv is available
    if not shutil.which("uv"):
        check.error_message = "uv tool not found in PATH"
        check.install_hint = (
            "Install uv from https://docs.astral.sh/uv/getting-started/installation/"
        )
        return check

    # Check if we're in a uv-managed virtual environment
    virtual_env = sys.prefix
    if virtual_env and ("uv" in virtual_env.lower() or ".venv" in virtual_env):
        check.available = True
        check.version = f"Virtual env: {virtual_env}"
    else:
        check.error_message = "Not running in uv-managed virtual environment"
        check.install_hint = "Run: uv sync && source .venv/bin/activate"

    return check


def check_project_files() -> List[DependencyCheck]:
    """Check for required project files.

    Returns:
        List of DependencyCheck results for project files
    """
    checks = []
    root = paths.repo_root()

    required_files = [
        "pyproject.toml",
        "uv.lock",
        "README.md",
        "src/__init__.py",
        "data/domain_research/Synthetic_FEP-ActInf.md",
    ]

    for file_path in required_files:
        check = DependencyCheck(name=file_path, required=True, available=False)

        full_path = root / file_path
        if full_path.exists():
            check.available = True
            check.version = f"Size: {full_path.stat().st_size} bytes"
        else:
            check.error_message = f"Required file not found: {full_path}"

        checks.append(check)

    return checks


def check_environment_variables() -> List[DependencyCheck]:
    """Check for required environment variables.

    Returns:
        List of DependencyCheck results for environment variables
    """
    checks = []

    required_env_vars = [
        ("PERPLEXITY_API_KEY", "Perplexity API access"),
        ("OPENROUTER_API_KEY", "OpenRouter API access"),
    ]

    optional_env_vars = [
        ("PERPLEXITY_MODEL", "Custom Perplexity model"),
        ("OPENROUTER_MODEL", "Custom OpenRouter model"),
    ]

    # Check required variables
    for var_name, _description in required_env_vars:
        check = DependencyCheck(name=f"env.{var_name}", required=True, available=False)

        value = os.environ.get(var_name)
        if value:
            check.available = True
            # Don't show actual API key values for security
            check.version = f"Set ({len(value)} chars)"
        else:
            check.error_message = f"Required environment variable not set: {var_name}"
            check.install_hint = f"Set {var_name} in your .env file"

        checks.append(check)

    # Check optional variables
    for var_name, _description in optional_env_vars:
        check = DependencyCheck(name=f"env.{var_name}", required=False, available=False)

        value = os.environ.get(var_name)
        if value:
            check.available = True
            check.version = value
        else:
            check.error_message = "Optional environment variable not set"
            check.install_hint = f"Set {var_name} in your .env file if desired"

        checks.append(check)

    return checks


def run_comprehensive_dependency_check() -> DependencyReport:
    """Run a comprehensive check of all dependencies.

    Returns:
        Complete dependency report
    """
    report = DependencyReport()

    # Check required Python packages
    for package, distribution in _required_python_package_specs():
        check = check_python_package(package, required=True, distribution_name=distribution)
        report.python_packages.append(check)
        if check.required and not check.available:
            report.missing_required.append(f"python:{distribution}")

    # Check optional Python packages
    for package in get_optional_python_packages():
        check = check_python_package(package, required=False)
        report.python_packages.append(check)

    # Check required system tools
    for tool_name, version_flag in get_required_system_tools():
        check = check_system_tool(tool_name, required=True, version_flag=version_flag)
        report.system_tools.append(check)
        if check.required and not check.available:
            report.missing_required.append(f"system:{tool_name}")

    # Check optional system tools
    for tool_name, version_flag in get_optional_system_tools():
        check = check_system_tool(tool_name, required=False, version_flag=version_flag)
        report.optional_tools.append(check)

    # Check uv environment
    uv_check = check_uv_environment()
    report.optional_tools.append(uv_check)

    # Check project files
    project_checks = check_project_files()
    for check in project_checks:
        if check.required and not check.available:
            report.missing_required.append(f"file:{check.name}")
    report.system_tools.extend(project_checks)

    # Check environment variables
    env_checks = check_environment_variables()
    for check in env_checks:
        if check.required and not check.available:
            report.missing_required.append(f"env:{check.name}")
    report.system_tools.extend(env_checks)

    # Determine overall status
    report.all_required_available = len(report.missing_required) == 0

    return report


def format_dependency_report(report: DependencyReport, show_optional: bool = True) -> str:
    """Format dependency report as readable text.

    Args:
        report: Dependency report to format
        show_optional: Whether to show optional dependencies

    Returns:
        Formatted report string
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("DEPENDENCY CHECK REPORT")
    lines.append("=" * 60)

    # Overall status
    status = (
        "✅ ALL REQUIRED DEPENDENCIES AVAILABLE"
        if report.all_required_available
        else "❌ MISSING REQUIRED DEPENDENCIES"
    )
    lines.append(f"\nStatus: {status}")

    if report.missing_required:
        lines.append(f"Missing required: {len(report.missing_required)}")
        for missing in report.missing_required:
            lines.append(f"  - {missing}")

    # Python packages
    lines.append("\n🐍 PYTHON PACKAGES")
    for check in report.python_packages:
        status_icon = "✅" if check.available else "❌"
        required_text = " (REQUIRED)" if check.required else " (optional)"

        if check.available:
            lines.append(
                f"{status_icon} {check.name}{required_text} - {check.version or 'available'}"
            )
        else:
            lines.append(f"{status_icon} {check.name}{required_text} - {check.error_message}")
            if check.install_hint:
                lines.append(f"    💡 {check.install_hint}")

    # System tools and project files
    lines.append("\n🔧 SYSTEM TOOLS & PROJECT FILES")
    for check in report.system_tools:
        status_icon = "✅" if check.available else "❌"
        required_text = " (REQUIRED)" if check.required else " (optional)"

        if check.available:
            lines.append(
                f"{status_icon} {check.name}{required_text} - {check.version or 'available'}"
            )
        else:
            lines.append(f"{status_icon} {check.name}{required_text} - {check.error_message}")
            if check.install_hint:
                lines.append(f"    💡 {check.install_hint}")

    # Optional tools
    if show_optional and report.optional_tools:
        lines.append("\n🔧 OPTIONAL TOOLS")
        for check in report.optional_tools:
            status_icon = "✅" if check.available else "⚠️"

            if check.available:
                lines.append(f"{status_icon} {check.name} - {check.version or 'available'}")
            else:
                lines.append(f"{status_icon} {check.name} - not available")
                if check.install_hint:
                    lines.append(f"    💡 {check.install_hint}")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)


def get_installation_instructions() -> str:
    """Get installation instructions for missing dependencies.

    Returns:
        Installation instructions text
    """
    instructions = [
        "INSTALLATION INSTRUCTIONS",
        "=" * 30,
        "",
        "1. Install uv (Python package manager):",
        "   Install uv from https://docs.astral.sh/uv/getting-started/installation/",
        "",
        "2. Set up project environment:",
        "   uv sync --all-extras --dev",
        "",
        "3. Activate virtual environment:",
        "   source .venv/bin/activate  # Linux/Mac",
        "   # or",
        "   .venv\\Scripts\\activate     # Windows",
        "",
        "4. Create .env file with API keys:",
        "   cp .env.example .env  # if .env.example exists",
        "   # Edit .env and add your API keys:",
        "   # PERPLEXITY_API_KEY=your_key_here",
        "   # OPENROUTER_API_KEY=your_key_here",
        "",
        "5. Test installation:",
        "   uv run python -c 'import src; print(\"SUCCESS\")'",
        "",
    ]

    return "\n".join(instructions)


def validate_api_keys() -> Dict[str, bool]:
    """Check credential presence without making a provider request.

    Returns:
        Dictionary of API key validation results
    """
    return {
        "perplexity": bool(os.environ.get("PERPLEXITY_API_KEY", "").strip()),
        "openrouter": bool(os.environ.get("OPENROUTER_API_KEY", "").strip()),
    }


def probe_api_connectivity(timeout: float = 10.0) -> Dict[str, Any]:
    """Perform explicit live provider probes with labeled failure details.

    This function is intentionally separate from health checks because it can
    make paid provider requests.
    """
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    results: Dict[str, Any] = {
        "perplexity": False,
        "openrouter": False,
        "errors": {},
    }
    provider_models = {
        "perplexity": os.environ.get("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
        "openrouter": os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
    }
    for provider, builder in (
        ("perplexity", "build_perplexity_client"),
        ("openrouter", "build_openrouter_client"),
    ):
        try:
            from src.perplexity import clients

            client = getattr(clients, builder)()
            response = client.chat.completions.create(
                model=provider_models[provider],
                messages=[{"role": "user", "content": "Connectivity probe"}],
                max_tokens=8,
                timeout=timeout,
            )
            results[provider] = bool(response.choices)
        except Exception as exc:
            results[provider] = False
            results["errors"][provider] = f"{type(exc).__name__}: {exc}"
    return results
