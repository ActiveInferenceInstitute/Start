"""Small, deterministic helpers for artifact provenance metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import sha256_file, sha256_text, utc_now


def input_record(value: str, *, label: str, path: str | None = None) -> dict[str, Any]:
    """Describe a text input without storing its complete contents in metadata."""

    record: dict[str, Any] = {
        "label": label,
        "sha256": sha256_text(value),
        "size_bytes": len(value.encode("utf-8")),
    }
    if path:
        record["path"] = str(Path(path))
    return record


def file_input_record(path: str | Path, *, label: str) -> dict[str, Any]:
    """Describe a file input by digest and size."""

    file_path = Path(path)
    return {
        "label": label,
        "path": str(file_path),
        "sha256": sha256_file(file_path),
        "size_bytes": file_path.stat().st_size,
    }


def generation_metadata(
    *,
    provider: str,
    model: str,
    prompt_name: str,
    prompt: str,
    evidence_status: str,
    inputs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a portable metadata block for generated content."""

    return {
        "provider": provider,
        "model": model,
        "prompt_name": prompt_name,
        "prompt_sha256": sha256_text(prompt),
        "evidence_status": evidence_status,
        "generated_at": utc_now(),
        "inputs": inputs,
    }
