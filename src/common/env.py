from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def load_project_env(env_path: Optional[os.PathLike | str] = None) -> None:
    # Load from provided path, or try repo root
    if env_path:
        load_dotenv(dotenv_path=Path(env_path).expanduser(), override=False)
        return
    # Walk up to find .env near repo root
    candidates = [Path.cwd()] + list(Path.cwd().parents)
    for base in candidates:
        env_file = base / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)
            return


def require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value



