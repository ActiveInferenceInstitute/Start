from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Iterable, Optional


def safe_name(value: str, *, fallback: str = "item", max_length: int = 120) -> str:
    """Return a filesystem-safe single path component.

    Names are intentionally normalized instead of interpreted as paths.  This
    keeps user-provided entities, sections, and languages inside their chosen
    output directory.
    """
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip()).strip("._")
    normalized = normalized[:max_length].strip("._")
    return normalized or fallback


def path_within(path: os.PathLike | str, root: os.PathLike | str) -> bool:
    """Return whether *path* resolves below *root* (or equals root)."""
    candidate = Path(path).expanduser().resolve()
    base = Path(root).expanduser().resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return False
    return True


def _reject_symlink_components(path: Path) -> None:
    """Reject symlink destinations and parent boundaries before writing."""

    expanded = path.expanduser()
    if expanded.is_symlink():
        raise ValueError(f"Refusing to write through symlink: {expanded}")
    for parent in expanded.parents:
        if parent.exists() and parent.is_symlink():
            raise ValueError(f"Refusing to write through symlink parent: {parent}")


def _reject_symlink_target(path: Path) -> None:
    """Reject reading a file that is itself a symlink.

    Parent symlinks are deliberately allowed so the repository can live under
    a symlinked install location, but the final target must be a real file so
    an attacker-supplied symlink cannot redirect a config/env/prompt read.
    """

    if path.is_symlink():
        raise ValueError(f"Refusing to read through symlink: {path}")


def next_available_path(path: os.PathLike | str) -> Path:
    """Choose a collision-safe path without overwriting an existing artifact."""
    candidate = Path(path).expanduser()
    _reject_symlink_components(candidate.parent)
    if not os.path.lexists(candidate):
        return candidate
    for index in range(1, 10_000):
        alternate = candidate.with_name(f"{candidate.stem}_{index}{candidate.suffix}")
        if not os.path.lexists(alternate):
            return alternate
    raise FileExistsError(f"Unable to find an available output name for {candidate}")


def next_available_bundle(
    directory: os.PathLike | str, stem: str, suffixes: Sequence[str]
) -> list[Path]:
    """Return a shared collision-free stem for a group of output files.

    Every suffix must be absent before the stem is accepted.  Callers can then
    publish the returned paths together with :func:`write_text_bundle`.
    """
    if not stem or not stem.strip():
        raise ValueError("stem cannot be empty")
    if not suffixes:
        raise ValueError("suffixes cannot be empty")
    normalized_suffixes = [
        suffix if suffix.startswith(".") else f".{suffix}" for suffix in suffixes
    ]
    raw_base = Path(directory).expanduser()
    _reject_symlink_components(raw_base)
    base = raw_base.resolve()
    for index in range(10_000):
        candidate_stem = stem if index == 0 else f"{stem}_{index}"
        candidates = [base / f"{candidate_stem}{suffix}" for suffix in normalized_suffixes]
        if all(not os.path.lexists(candidate) for candidate in candidates):
            return candidates
    raise FileExistsError(f"Unable to find an available bundle name for {base / stem}")


def ensure_parent_dir(file_path: Path) -> None:
    path = Path(file_path).expanduser()
    _reject_symlink_components(path)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)


def ensure_directory(directory: os.PathLike | str) -> Path:
    """Create a directory without following symlinked path boundaries."""

    path = Path(directory).expanduser()
    _reject_symlink_components(path)
    if path.exists() and not path.is_dir():
        raise ValueError(f"Expected a directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(path)
    return path.resolve()


def read_text(file_path: os.PathLike | str) -> str:
    path = Path(file_path).expanduser()
    _reject_symlink_target(path)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_text(file_path: os.PathLike | str, content: str) -> Path:
    """Atomically replace one UTF-8 text file."""
    if not isinstance(content, str):
        raise TypeError("content must be a string")
    path = Path(file_path).expanduser()
    ensure_parent_dir(path)
    resolved = path.resolve()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=resolved.parent,
            prefix=f".{resolved.name}.",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, resolved)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise
    return resolved


def write_text_bundle(files: Mapping[os.PathLike | str, str]) -> list[Path]:
    """Publish several text files as one in-process transaction.

    All destinations are validated before any destination is replaced.  If a
    later replacement fails, files already published by this call are removed
    and temporary files are cleaned up.  Destinations must not already exist;
    callers should reserve names with :func:`next_available_bundle`.
    """
    if not files:
        raise ValueError("files cannot be empty")

    raw_entries = [(Path(path).expanduser(), content) for path, content in files.items()]
    for path, _content in raw_entries:
        _reject_symlink_components(path)
    entries = [(path.resolve(), content) for path, content in raw_entries]
    destinations = [path for path, _ in entries]
    if len(set(destinations)) != len(destinations):
        raise ValueError("files contains duplicate destinations")
    if any(not isinstance(content, str) for _, content in entries):
        raise TypeError("all bundle contents must be strings")
    existing = [path for path in destinations if os.path.lexists(path)]
    if existing:
        raise FileExistsError(f"Bundle destination already exists: {existing[0]}")

    temporary_paths: list[Path] = []
    published: list[Path] = []
    try:
        for destination, content in entries:
            ensure_parent_dir(destination)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                temporary_paths.append(temporary)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())

        for temporary, destination in zip(temporary_paths, destinations, strict=True):
            os.replace(temporary, destination)
            published.append(destination)
        return destinations
    except Exception:
        for destination in published:
            destination.unlink(missing_ok=True)
        raise
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)


def read_json(file_path: os.PathLike | str) -> Any:
    path = Path(file_path).expanduser()
    _reject_symlink_target(path)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(file_path: os.PathLike | str, data: Any, indent: int = 2) -> Path:
    path = Path(file_path).expanduser()
    ensure_parent_dir(path)
    serialized = json.dumps(data, indent=indent, ensure_ascii=False) + "\n"
    return write_text(path, serialized)


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
        pattern_path = Path(pattern).expanduser()
        # Reject patterns that could traverse above the base directory.
        if pattern_path.is_absolute() or any(part == ".." for part in pattern_path.parts):
            continue
        results.extend(base.glob(pattern))
    # Keep unique, sorted, and confined to the base directory.
    confined: list[Path] = []
    for result in results:
        if not result.is_file():
            continue
        try:
            resolved = result.resolve()
            resolved.relative_to(base)
        except (ValueError, OSError):
            continue
        confined.append(resolved)
    return sorted(set(confined))


def load_key_from_file(key_file_path: os.PathLike | str, key_name: str) -> str:
    path = Path(key_file_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Key file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]
    # Keep the first occurrence of a repeated key and distinguish a present
    # (possibly empty) value from an absent key.
    key_pairs: dict[str, str] = {}
    for line in lines:
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in key_pairs:
            key_pairs[key] = value.strip()
    if key_name not in key_pairs:
        raise ValueError(f"{key_name} not found in {path}")
    return key_pairs[key_name]


def list_domain_markdown_files(
    domain_dir: os.PathLike | str, exclude_stems: Optional[Iterable[str]] = None
) -> list[Path]:
    base = Path(domain_dir).expanduser()
    if not base.exists():
        return []
    excludes = {Path(stem).stem for stem in (exclude_stems or [])}
    files = [p for p in base.glob("*.md") if p.stem not in excludes]
    return sorted(p.resolve() for p in files)
