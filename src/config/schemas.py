"""Typed, dependency-light schemas for user-controlled YAML configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping
from urllib.parse import urlparse

from src.common.io import safe_name

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")
_PRIORITIES = {"high", "medium", "low"}


def stable_identifier(value: str) -> str:
    """Return a deterministic identifier distinct from a display name."""

    identifier = safe_name(value, fallback="item", max_length=80).casefold()
    identifier = re.sub(r"[^a-z0-9_-]+", "-", identifier).strip("-_")
    if not identifier or not re.match(r"^[a-z0-9]", identifier):
        raise ValueError(f"Unable to derive a stable identifier from {value!r}")
    return identifier[:80]


def _identifier(value: Any, display_name: str, label: str) -> str:
    result = value if value is not None else stable_identifier(display_name)
    if not isinstance(result, str) or not _ID_PATTERN.fullmatch(result):
        raise ValueError(f"{label} id must match {_ID_PATTERN.pattern}: {result!r}")
    return result


def _required_text(entry: Mapping[str, Any], key: str, label: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must contain a non-empty {key}")
    if any(char in value for char in "\r\n"):
        raise ValueError(f"{label} {key} cannot contain newlines")
    return value.strip()


def _category(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID_PATTERN.fullmatch(value.strip()):
        raise ValueError(f"{label} category must be a stable slug")
    return value.strip()


def _optional_sources(entry: Mapping[str, Any], label: str) -> list[str]:
    sources = entry.get("source_urls", entry.get("sources", []))
    if sources is None:
        return []
    if not isinstance(sources, list) or any(not isinstance(source, str) for source in sources):
        raise ValueError(f"{label} source_urls must be a list of URL strings")
    normalized: list[str] = []
    for source in sources:
        parsed = urlparse(source.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"{label} contains an unsafe source URL: {source!r}")
        normalized.append(source.strip())
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} source_urls contains duplicates")
    return normalized


def _optional_verification_date(entry: Mapping[str, Any], label: str) -> str | None:
    value = entry.get("verification_date", entry.get("verified_at"))
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} verification_date must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} verification_date must be an ISO date") from exc
    return value


@dataclass(frozen=True)
class DomainConfig:
    id: str
    name: str
    description: str
    category: str
    priority: str
    keywords: tuple[str, ...]
    source_urls: tuple[str, ...] = ()
    verification_date: str | None = None


@dataclass(frozen=True)
class EntityConfig:
    id: str
    name: str
    description: str
    category: str
    priority: str
    source_urls: tuple[str, ...] = ()
    verification_date: str | None = None


@dataclass(frozen=True)
class LanguageConfig:
    id: str
    name: str
    script: str


def validate_domains_config(
    config: Mapping[str, Any], *, require_provenance: bool = False
) -> list[DomainConfig]:
    """Validate domains and return typed records with stable IDs."""

    entries = config.get("domains")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Domains configuration must contain a non-empty domains list")
    records: list[DomainConfig] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"Domain {index}"
        if not isinstance(entry, Mapping):
            raise ValueError(f"{label} must be a mapping")
        name = _required_text(entry, "name", label)
        identifier = _identifier(entry.get("id"), name, label)
        if identifier in seen:
            raise ValueError(f"Duplicate domain id: {identifier}")
        seen.add(identifier)
        description = _required_text(entry, "description", label)
        category = _category(entry.get("category"), label)
        priority = entry.get("priority", "medium")
        if priority not in _PRIORITIES:
            raise ValueError(f"{label} priority must be high, medium, or low")
        keywords = entry.get("keywords", [])
        if not isinstance(keywords, list) or any(
            not isinstance(keyword, str) or not keyword.strip() for keyword in keywords
        ):
            raise ValueError(f"{label} keywords must be a list of non-empty strings")
        source_urls = tuple(_optional_sources(entry, label))
        verification_date = _optional_verification_date(entry, label)
        if require_provenance and (not source_urls or verification_date is None):
            raise ValueError(
                f"{label} requires source_urls and verification_date in publication mode"
            )
        records.append(
            DomainConfig(
                identifier,
                name,
                description,
                category,
                priority,
                tuple(keyword.strip() for keyword in keywords),
                source_urls,
                verification_date,
            )
        )
    return records


def validate_entities_config(
    config: Mapping[str, Any], *, require_provenance: bool = False
) -> list[EntityConfig]:
    """Validate entities and return typed records with stable IDs."""

    entries = config.get("entities")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Entities configuration must contain a non-empty entities list")
    records: list[EntityConfig] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"Entity {index}"
        if not isinstance(entry, Mapping):
            raise ValueError(f"{label} must be a mapping")
        name = _required_text(entry, "name", label)
        identifier = _identifier(entry.get("id"), name, label)
        if identifier in seen:
            raise ValueError(f"Duplicate entity id: {identifier}")
        seen.add(identifier)
        priority = entry.get("priority", "medium")
        if priority not in _PRIORITIES:
            raise ValueError(f"{label} priority must be high, medium, or low")
        source_urls = tuple(_optional_sources(entry, label))
        verification_date = _optional_verification_date(entry, label)
        if require_provenance and (not source_urls or verification_date is None):
            raise ValueError(
                f"{label} requires source_urls and verification_date in publication mode"
            )
        records.append(
            EntityConfig(
                identifier,
                name,
                _required_text(entry, "description", label),
                _category(entry.get("category"), label),
                priority,
                source_urls,
                verification_date,
            )
        )
    return records


def validate_languages_config(config: Mapping[str, Any]) -> list[LanguageConfig]:
    """Validate language names, mappings, and stable identifiers."""

    entries = config.get("target_languages")
    mappings = config.get("script_mappings", {})
    if not isinstance(entries, list) or not entries:
        raise ValueError("Language configuration must contain a non-empty target_languages list")
    if not isinstance(mappings, Mapping):
        raise ValueError("Language script_mappings must be a mapping")
    result: list[LanguageConfig] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if isinstance(entry, str):
            name = entry.strip()
            script = mappings.get(name, name)
        elif isinstance(entry, Mapping):
            name = _required_text(entry, "name", f"Language {index}")
            script = entry.get("script", mappings.get(name, name))
        else:
            raise ValueError(f"Language {index} must be a string or mapping")
        if not name or not isinstance(script, str) or not script.strip():
            raise ValueError(f"Language {index} must have non-empty name and script")
        identifier = stable_identifier(name)
        if identifier in seen:
            raise ValueError(f"duplicate language id: {identifier}")
        seen.add(identifier)
        result.append(LanguageConfig(identifier, name, script.strip()))
    for key, value in mappings.items():
        if (
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(value, str)
            or not value.strip()
        ):
            raise ValueError("Language script_mappings must contain non-empty strings")
    return result


def add_stable_ids(config: Mapping[str, Any], key: str) -> dict[str, Any]:
    """Return a copy of config with generated IDs for backward-compatible callers."""

    result = dict(config)
    entries = []
    for entry in config.get(key, []):
        copied = dict(entry) if isinstance(entry, Mapping) else entry
        if isinstance(copied, dict) and "id" not in copied and isinstance(copied.get("name"), str):
            copied["id"] = stable_identifier(copied["name"])
        entries.append(copied)
    result[key] = entries
    return result
