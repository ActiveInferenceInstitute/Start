from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def find_repo_root(start: Optional[os.PathLike | str] = None) -> Path:
    # Allow environment override for test/workflow control
    env_root = os.environ.get("START_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        if p.exists():
            return p
    path = Path(start or __file__).resolve()
    for candidate in [path] + list(path.parents):
        # Avoid relying on Path.stat when tests patch it with incompatible mocks
        try:
            root = candidate if candidate.is_dir() else candidate.parent
        except Exception:
            root = candidate.parent
        if Path.exists(root / ".git") or Path.exists(root / "README.md"):
            return root
    # Fallback to current working directory
    return Path.cwd().resolve()


def repo_root() -> Path:
    return find_repo_root()


def languages_root() -> Path:
    return repo_root() / "Languages"


def inputs_and_outputs_root() -> Path:
    return languages_root() / "Inputs_and_Outputs"


def domain_dir() -> Path:
    return inputs_and_outputs_root() / "Domain"


def domain_research_dir() -> Path:
    return inputs_and_outputs_root() / "Domain_Research"


def ensure_dir(path: os.PathLike | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p.resolve()


# Data directories (outputs)


def data_root() -> Path:
    return repo_root() / "data"


def data_written_curriculums_dir() -> Path:
    return ensure_dir(data_root() / "written_curriculums")


def data_translated_curriculums_dir() -> Path:
    return ensure_dir(data_root() / "translated_curriculums")


def data_visualizations_dir() -> Path:
    return ensure_dir(data_root() / "visualizations")


def data_audience_research_dir() -> Path:
    return ensure_dir(data_root() / "audience_research")


def data_domain_research_dir() -> Path:
    return ensure_dir(data_root() / "domain_research")


def config_dir() -> Path:
    """Get path to configuration directory.

    Returns:
        Path to data/config directory
    """
    return ensure_dir(data_root() / "config")
