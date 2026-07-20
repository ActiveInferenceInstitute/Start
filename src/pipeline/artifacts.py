"""Filesystem-backed run and artifact helpers.

The pipeline keeps each run inspectable on disk.  Final artifacts are written
atomically and manifests are persisted after every stage so a process can
resume without confusing partial output for a successful run.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.io import write_text


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    """Return the SHA-256 digest for bytes."""

    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest for UTF-8 text."""

    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    """Hash a file without loading the complete file into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_run_id(value: str) -> str:
    """Normalize a run identifier to one safe filesystem component."""

    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip(".-")
    if not normalized:
        raise ValueError("run_id cannot be empty")
    return normalized[:120]


def create_run_directory(root: Path | str, run_id: str) -> Path:
    """Create and return ``root/run_id`` without following a symlink root."""

    raw_base = Path(root).expanduser()
    if raw_base.exists() and raw_base.is_symlink():
        raise ValueError(f"run root cannot be a symlink: {raw_base}")
    base = raw_base.resolve()
    run_dir = base / safe_run_id(run_id)
    if run_dir.exists() and run_dir.is_symlink():
        raise ValueError(f"run directory cannot be a symlink: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_json_atomic(path: Path | str, payload: dict[str, Any]) -> Path:
    """Serialize and atomically publish a JSON document."""

    content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return write_text(path, content)


def write_stage_checkpoint(run_dir: Path | str, stage_name: str, payload: dict[str, Any]) -> Path:
    """Persist a stage checkpoint under a safe stage-specific directory."""

    safe_stage = safe_run_id(stage_name)
    stage_dir = Path(run_dir) / "stages" / safe_stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    return write_json_atomic(stage_dir / "checkpoint.json", payload)


def read_json(path: Path | str) -> dict[str, Any]:
    """Read a JSON object and reject non-object payloads."""

    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON document must contain an object: {path}")
    return payload
