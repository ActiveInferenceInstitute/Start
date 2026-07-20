"""Canonical configuration and selection helpers for pipeline callers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.common.config import load_config
from src.config.schemas import (
    add_stable_ids,
    stable_identifier,
    validate_domains_config,
    validate_entities_config,
)


def load_domains_config() -> dict[str, Any]:
    config = load_config("domains")
    validate_domains_config(config)
    return add_stable_ids(config, "domains")


def load_entities_config() -> dict[str, Any]:
    config = load_config("entities")
    validate_entities_config(config)
    return add_stable_ids(config, "entities")


def domains_to_process(
    config: dict[str, Any], priority: str | None = None, category: str | None = None
) -> list[dict[str, Any]]:
    entries = list(config.get("domains", []))
    if priority:
        entries = [entry for entry in entries if entry.get("priority", "medium") == priority]
    if category:
        entries = [entry for entry in entries if entry.get("category") == category]
    return entries


def entities_to_process(
    config: dict[str, Any], priority: str | None = None
) -> list[dict[str, Any]]:
    entries = list(config.get("entities", []))
    if priority:
        entries = [entry for entry in entries if entry.get("priority", "medium") == priority]
    return entries


def output_exists(
    output_dir: Path,
    display_name: str,
    *,
    kind: str,
    stable_id: str | None = None,
) -> bool:
    """Check canonical output names using the same safe naming policy as writers."""

    from src.common.io import safe_name

    candidates = {safe_name(display_name), stable_identifier(display_name)}
    if stable_id:
        candidates.add(stable_id)
    return any(
        any(output_dir.glob(f"{candidate}_{kind}_*.json"))
        or any(output_dir.glob(f"{candidate}_{kind}_*.md"))
        for candidate in candidates
    )
