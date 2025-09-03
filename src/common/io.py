from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional


def ensure_parent_dir(file_path: Path) -> None:
    parent = Path(file_path).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


def read_text(file_path: os.PathLike | str) -> str:
    path = Path(file_path).expanduser()
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_text(file_path: os.PathLike | str, content: str) -> Path:
    path = Path(file_path).expanduser()
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path.resolve()


def read_json(file_path: os.PathLike | str) -> Any:
    path = Path(file_path).expanduser()
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(file_path: os.PathLike | str, data: Any, indent: int = 2) -> Path:
    path = Path(file_path).expanduser()
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=indent, ensure_ascii=False)
    return path.resolve()


def list_files(
    directory: os.PathLike | str, patterns: Optional[Iterable[str]] = None
) -> list[Path]:
    base = Path(directory).expanduser()
    if not base.exists():
        return []
    if not patterns:
        return sorted(p for p in base.iterdir() if p.is_file())
    results: list[Path] = []
    for pattern in patterns:
        results.extend(base.glob(pattern))
    # unique and sorted
    unique_sorted = sorted({p.resolve() for p in results if p.is_file()})
    return unique_sorted


def load_key_from_file(key_file_path: os.PathLike | str, key_name: str) -> str:
    path = Path(key_file_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Key file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]
    key_pairs = dict(pair.split("=", 1) for pair in lines if "=" in pair)
    value = key_pairs.get(key_name)
    if not value:
        raise ValueError(f"{key_name} not found in {path}")
    return value


def list_domain_markdown_files(
    domain_dir: os.PathLike | str, exclude_stems: Optional[Iterable[str]] = None
) -> list[Path]:
    base = Path(domain_dir).expanduser()
    if not base.exists():
        return []
    excludes = {Path(stem).stem for stem in (exclude_stems or [])}
    files = [p for p in base.glob("*.md") if p.stem not in excludes]
    return sorted(p.resolve() for p in files)
