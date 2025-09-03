"""Environment setup and validation utilities.

This module provides functionality for setting up and validating the
project environment, including virtual environments, API keys, and
configuration files.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.common.env import load_project_env
from src.common.paths import repo_root


def setup_project_environment() -> Tuple[bool, List[str]]:
    """Set up the complete project environment.
    
    Returns:
        Tuple of (success, messages)
    """
    messages = []
    success = True
    
    # Check if we're in project root
    root = repo_root()
    if not (root / "pyproject.toml").exists():
        messages.append("❌ Not in project root directory")
        return False, messages
    
    messages.append(f"📁 Project root: {root}")
    
    # Check for uv
    if not shutil.which("uv"):
        messages.append("❌ uv not found - installing uv...")
        install_success = install_uv()
        if not install_success:
            messages.append("❌ Failed to install uv")
            return False, messages
        messages.append("✅ uv installed successfully")
    else:
        messages.append("✅ uv found")
    
    # Run uv sync
    messages.append("📦 Syncing dependencies with uv...")
    sync_success, sync_output = run_uv_sync()
    if not sync_success:
        messages.append(f"❌ uv sync failed: {sync_output}")
        success = False
    else:
        messages.append("✅ Dependencies synced successfully")
    
    # Check environment file
    env_file = root / ".env"
    if not env_file.exists():
        messages.append("⚠️  .env file not found - creating template...")
        create_env_template()
        messages.append("✅ Created .env template - please add your API keys")
    else:
        messages.append("✅ .env file exists")
    
    # Load and validate environment
    load_project_env()
    env_valid, env_messages = validate_environment()
    messages.extend(env_messages)
    
    if not env_valid:
        success = False
    
    return success, messages


def install_uv() -> bool:
    """Install uv package manager.
    
    Returns:
        True if installation successful, False otherwise
    """
    try:
        # Use the official uv installer
        curl_cmd = [
            "curl", "-LsSf", 
            "https://astral.sh/uv/install.sh"
        ]
        
        sh_cmd = ["sh"]
        
        # Run curl | sh
        curl_process = subprocess.Popen(curl_cmd, stdout=subprocess.PIPE)
        sh_process = subprocess.run(
            sh_cmd, 
            stdin=curl_process.stdout, 
            capture_output=True, 
            text=True,
            timeout=60,
        )
        
        curl_process.wait()
        
        if sh_process.returncode == 0:
            # Update PATH for current session
            cargo_bin = Path.home() / ".cargo" / "bin"
            if cargo_bin.exists() and str(cargo_bin) not in os.environ.get("PATH", ""):
                os.environ["PATH"] = f"{cargo_bin}:{os.environ.get('PATH', '')}"
            return True
        
        return False
        
    except Exception:
        return False


def run_uv_sync() -> Tuple[bool, str]:
    """Run uv sync to install dependencies.
    
    Returns:
        Tuple of (success, output)
    """
    try:
        root = repo_root()
        result = subprocess.run(
            ["uv", "sync", "--all-extras", "--dev"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )
        
        output = result.stdout + result.stderr
        return result.returncode == 0, output
        
    except subprocess.TimeoutExpired:
        return False, "uv sync timed out"
    except Exception as e:
        return False, str(e)


def create_env_template() -> Path:
    """Create a template .env file.
    
    Returns:
        Path to created .env file
    """
    root = repo_root()
    env_file = root / ".env"
    
    template_content = """# API Keys for Active Inference curriculum generation
# Get your keys from:
# - Perplexity: https://www.perplexity.ai/settings/api
# - OpenRouter: https://openrouter.ai/keys

PERPLEXITY_API_KEY=your_perplexity_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Override default models
# PERPLEXITY_MODEL=llama-3.1-sonar-small-128k-online
# OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Optional: Enable debug logging
# DEBUG=true
"""
    
    with open(env_file, 'w') as f:
        f.write(template_content)
    
    return env_file


def validate_environment() -> Tuple[bool, List[str]]:
    """Validate the current environment setup.
    
    Returns:
        Tuple of (is_valid, messages)
    """
    messages = []
    is_valid = True
    
    # Check Python version
    if sys.version_info < (3, 8):
        messages.append("❌ Python 3.8+ required")
        is_valid = False
    else:
        messages.append(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        messages.append(f"✅ Virtual environment active: {sys.prefix}")
    else:
        messages.append("⚠️  No virtual environment detected")
    
    # Check API keys
    api_keys = {
        "PERPLEXITY_API_KEY": "Perplexity API",
        "OPENROUTER_API_KEY": "OpenRouter API",
    }
    
    for key, name in api_keys.items():
        value = os.environ.get(key)
        if value and value != f"your_{key.lower()}_here":
            messages.append(f"✅ {name} key configured")
        else:
            messages.append(f"❌ {name} key missing or template value")
            is_valid = False
    
    # Check required directories exist
    root = repo_root()
    required_dirs = [
        "src",
        "data", 
        "data/config",
        "data/prompts",
        "tests",
    ]
    
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if dir_path.exists():
            messages.append(f"✅ Directory exists: {dir_name}")
        else:
            messages.append(f"❌ Missing directory: {dir_name}")
            is_valid = False
    
    return is_valid, messages


def get_environment_info() -> Dict[str, any]:
    """Get detailed environment information.
    
    Returns:
        Dictionary containing environment details
    """
    info = {}
    
    # Python environment
    info["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    info["python_executable"] = sys.executable
    info["virtual_env"] = getattr(sys, 'prefix', None)
    
    # Project paths
    root = repo_root()
    info["project_root"] = str(root)
    info["src_path"] = str(root / "src")
    info["data_path"] = str(root / "data")
    
    # Environment variables
    env_vars = {}
    for key in ["PERPLEXITY_API_KEY", "OPENROUTER_API_KEY", "PERPLEXITY_MODEL", "OPENROUTER_MODEL"]:
        value = os.environ.get(key)
        if value:
            # Don't expose actual API keys
            if "API_KEY" in key:
                env_vars[key] = f"<set, {len(value)} characters>"
            else:
                env_vars[key] = value
        else:
            env_vars[key] = "<not set>"
    
    info["environment_variables"] = env_vars
    
    # Check if uv is available
    info["uv_available"] = shutil.which("uv") is not None
    
    # Check for uv.lock
    info["uv_lock_exists"] = (root / "uv.lock").exists()
    
    return info


def fix_common_issues() -> List[str]:
    """Attempt to fix common environment issues.
    
    Returns:
        List of messages describing what was fixed
    """
    messages = []
    root = repo_root()
    
    # Create missing directories
    required_dirs = [
        "data/config",
        "data/prompts", 
        "data/domain_research",
        "data/audience_research",
        "data/written_curriculums",
        "data/translated_curriculums",
        "data/visualizations",
    ]
    
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            messages.append(f"✅ Created directory: {dir_name}")
    
    # Check for and create missing config files
    config_dir = root / "data" / "config"
    
    # Create basic domains.yaml if missing
    domains_file = config_dir / "domains.yaml"
    if not domains_file.exists():
        create_default_domains_config(domains_file)
        messages.append("✅ Created default domains.yaml")
    
    # Create basic entities.yaml if missing
    entities_file = config_dir / "entities.yaml"
    if not entities_file.exists():
        create_default_entities_config(entities_file)
        messages.append("✅ Created default entities.yaml")
    
    # Create basic languages.yaml if missing
    languages_file = config_dir / "languages.yaml"
    if not languages_file.exists():
        create_default_languages_config(languages_file)
        messages.append("✅ Created default languages.yaml")
    
    return messages


def create_default_domains_config(file_path: Path) -> None:
    """Create a default domains configuration file.
    
    Args:
        file_path: Path where to create the config file
    """
    config_content = """domains:
  - name: biochemistry
    description: Molecular processes and chemical reactions in living systems
    category: life_sciences
    keywords: [enzymes, metabolism, proteins, DNA, RNA]
    priority: high
    
  - name: neuroscience
    description: Structure and function of the nervous system
    category: life_sciences
    keywords: [brain, neurons, cognition, neural networks]
    priority: high
    
  - name: artificial_intelligence
    description: Machine learning and computational intelligence
    category: technology
    keywords: [AI, machine learning, neural networks, algorithms]
    priority: high
    
  - name: psychology
    description: Human behavior and mental processes
    category: behavioral_sciences
    keywords: [cognition, behavior, mind, consciousness]
    priority: medium
    
  - name: physics
    description: Fundamental principles of matter and energy
    category: physical_sciences
    keywords: [quantum, thermodynamics, relativity, particles]
    priority: medium
"""
    
    with open(file_path, 'w') as f:
        f.write(config_content)


def create_default_entities_config(file_path: Path) -> None:
    """Create a default entities configuration file.
    
    Args:
        file_path: Path where to create the config file
    """
    config_content = """entities:
  - name: karl_friston
    description: Theoretical neuroscientist and pioneer of Active Inference
    category: researcher
    priority: high
    
  - name: tulsi_gabbard
    description: Former U.S. Representative and political figure
    category: politician
    priority: medium
    
  - name: elon_musk
    description: Entrepreneur and business magnate
    category: entrepreneur
    priority: medium
    
  - name: undergraduate_students
    description: University students in STEM fields
    category: academic
    priority: high
"""
    
    with open(file_path, 'w') as f:
        f.write(config_content)


def create_default_languages_config(file_path: Path) -> None:
    """Create a default languages configuration file.
    
    Args:
        file_path: Path where to create the config file
    """
    config_content = """target_languages:
  - Chinese
  - Spanish
  - Arabic
  - Hindi
  - French
  - Japanese
  - German
  - Russian
  - Portuguese
  - Italian

script_mappings:
  Arabic: "Modern Standard Arabic"
  Chinese: "Simplified Chinese"
  Japanese: "Standard Japanese"
  Hindi: "Devanagari"
  Russian: "Cyrillic"
"""
    
    with open(file_path, 'w') as f:
        f.write(config_content)


def run_health_check() -> Tuple[bool, Dict[str, any]]:
    """Run a comprehensive health check of the environment.
    
    Returns:
        Tuple of (overall_healthy, detailed_results)
    """
    results = {
        "python_environment": {},
        "dependencies": {},
        "configuration": {},
        "api_connectivity": {},
        "file_system": {},
    }
    
    overall_healthy = True
    
    # Check Python environment
    try:
        results["python_environment"] = {
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "executable": sys.executable,
            "virtual_env": hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix),
            "healthy": sys.version_info >= (3, 8),
        }
        if not results["python_environment"]["healthy"]:
            overall_healthy = False
    except Exception as e:
        results["python_environment"]["error"] = str(e)
        overall_healthy = False
    
    # Check dependencies
    try:
        from .dependencies import run_comprehensive_dependency_check
        dep_report = run_comprehensive_dependency_check()
        results["dependencies"] = {
            "all_required_available": dep_report.all_required_available,
            "missing_count": len(dep_report.missing_required),
            "missing_items": dep_report.missing_required,
            "healthy": dep_report.all_required_available,
        }
        if not results["dependencies"]["healthy"]:
            overall_healthy = False
    except Exception as e:
        results["dependencies"]["error"] = str(e)
        overall_healthy = False
    
    # Check configuration files
    try:
        root = repo_root()
        config_files = ["domains.yaml", "entities.yaml", "languages.yaml"]
        config_status = {}
        
        for config_file in config_files:
            config_path = root / "data" / "config" / config_file
            config_status[config_file] = config_path.exists()
        
        results["configuration"] = {
            "files": config_status,
            "all_present": all(config_status.values()),
            "healthy": all(config_status.values()),
        }
        
        if not results["configuration"]["healthy"]:
            overall_healthy = False
            
    except Exception as e:
        results["configuration"]["error"] = str(e)
        overall_healthy = False
    
    # Check API connectivity
    try:
        from .dependencies import validate_api_keys
        api_results = validate_api_keys()
        results["api_connectivity"] = {
            "perplexity": api_results.get("perplexity", False),
            "openrouter": api_results.get("openrouter", False),
            "healthy": all(api_results.values()),
        }
        
        # API connectivity is not required for overall health
        # but we'll note any issues
        
    except Exception as e:
        results["api_connectivity"]["error"] = str(e)
        results["api_connectivity"]["healthy"] = False
    
    # Check file system
    try:
        root = repo_root()
        required_files = [
            "pyproject.toml",
            "src/__init__.py",
            "data/domain_research/Synthetic_FEP-ActInf.md",
        ]
        
        file_status = {}
        for req_file in required_files:
            file_path = root / req_file
            file_status[req_file] = file_path.exists()
        
        results["file_system"] = {
            "files": file_status,
            "all_present": all(file_status.values()),
            "healthy": all(file_status.values()),
        }
        
        if not results["file_system"]["healthy"]:
            overall_healthy = False
            
    except Exception as e:
        results["file_system"]["error"] = str(e)
        overall_healthy = False
    
    return overall_healthy, results
