from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so `Code` and `Languages` packages are importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set START_REPO_ROOT for all tests so path resolution always works
os.environ["START_REPO_ROOT"] = str(PROJECT_ROOT)


@pytest.fixture
def python_executable() -> str:
    """Return the current Python interpreter path for subprocess calls.
    
    This ensures subprocess tests use the same Python environment
    as the running test suite (e.g., uv run python).
    """
    return sys.executable


@pytest.fixture
def project_root() -> Path:
    """Return the project root path."""
    return PROJECT_ROOT


@pytest.fixture
def data_dir() -> Path:
    """Return the data directory path."""
    return PROJECT_ROOT / "data"


@pytest.fixture
def prompts_dir() -> Path:
    """Return the prompts directory path."""
    return PROJECT_ROOT / "data" / "prompts"
