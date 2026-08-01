from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def find_repo_root(start: Optional[os.PathLike | str] = None) -> Path:
    """Find the project root from a path or the explicit environment override.

    An override is accepted only when it points at this project's required
    markers.  Returning an arbitrary current directory makes configuration and
    output writes silently target the wrong checkout, so an unresolved root is
    an error instead.
    """
    env_root = os.environ.get("START_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        if (p / "pyproject.toml").is_file() and (p / "src").is_dir():
            return p
        raise RuntimeError(f"START_REPO_ROOT is not a START project: {p}")
    path = Path(start or __file__).resolve()
    for candidate in [path] + list(path.parents):
        root = candidate if candidate.is_dir() else candidate.parent
        if (root / "pyproject.toml").is_file() and (root / "src").is_dir():
            return root
    raise RuntimeError(f"Unable to locate START project root from {path}")


def repo_root() -> Path:
    return find_repo_root()


def ensure_dir(path: os.PathLike | str) -> Path:
    # Reuse the hardened, symlink-aware implementation so there is a single
    # source of truth for directory creation guarantees.
    from src.common.io import ensure_directory

    return ensure_directory(path)


# Data directories (outputs)


def data_root() -> Path:
    return repo_root() / "data"


def data_written_curriculums_dir() -> Path:
    return data_root() / "written_curriculums"


def data_translated_curriculums_dir() -> Path:
    return data_root() / "translated_curriculums"


def data_visualizations_dir() -> Path:
    return data_root() / "visualizations"


def data_audience_research_dir() -> Path:
    return data_root() / "audience_research"


def data_domain_research_dir() -> Path:
    return data_root() / "domain_research"


def config_dir() -> Path:
    """Get path to configuration directory.

    Returns:
        Path to data/config directory
    """
    return data_root() / "config"
