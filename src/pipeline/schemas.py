"""Dependency-light schemas for provider responses.

Publication runs use these JSON envelopes so downstream stages receive a typed
contract instead of guessing where sections and citations are located.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping


class StructuredPayloadError(ValueError):
    """Raised when a provider response cannot satisfy its stage contract."""


@dataclass(frozen=True)
class ProviderPayload:
    kind: str
    content: str = ""
    sections: dict[str, str] | None = None
    citations: tuple[str, ...] = ()
    target_language: str | None = None
    schema_version: str = "1.0"

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "content": self.content,
            "citations": list(self.citations),
        }
        if self.sections is not None:
            payload["sections"] = dict(self.sections)
        if self.target_language is not None:
            payload["target_language"] = self.target_language
        return payload


def _json_object(raw: str) -> Mapping[str, Any]:
    text = raw.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StructuredPayloadError("provider response is not valid JSON") from exc
    if not isinstance(payload, Mapping):
        raise StructuredPayloadError("provider response must be a JSON object")
    return payload


def _version_matches(value: Any) -> bool:
    """Accept the canonical '1.0' as string, integer, or float form."""
    return value == "1.0" or value == 1 or value == 1.0


def _text(payload: Mapping[str, Any], key: str, *, required: bool = True) -> str:
    value = payload.get(key)
    if value is None and not required:
        return ""
    if not isinstance(value, str) or not value.strip():
        raise StructuredPayloadError(f"provider payload requires non-empty string field: {key}")
    return value.strip()


def _citations(payload: Mapping[str, Any], *, required: bool) -> tuple[str, ...]:
    value = payload.get("citations", [])
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise StructuredPayloadError("provider payload citations must be a list of strings")
    citations = tuple(dict.fromkeys(item.strip() for item in value))
    if required and not citations:
        raise StructuredPayloadError("research provider payload requires at least one citation")
    return citations


def parse_structured_response(raw: str, kind: str) -> ProviderPayload:
    """Parse a strict research, curriculum, or translation response envelope."""

    if kind not in {"research", "curriculum", "translation"}:
        raise ValueError(f"unsupported provider payload kind: {kind}")
    payload = _json_object(raw)
    if not _version_matches(payload.get("schema_version")):
        raise StructuredPayloadError("provider payload schema_version must be '1.0'")
    if payload.get("kind") != kind:
        raise StructuredPayloadError(f"provider payload kind must be '{kind}'")
    citations = _citations(payload, required=kind == "research")
    if kind == "curriculum":
        sections = payload.get("sections")
        if not isinstance(sections, Mapping) or not sections:
            raise StructuredPayloadError("curriculum provider payload requires non-empty sections")
        normalized: dict[str, str] = {}
        for name, content in sections.items():
            if not isinstance(name, str) or not name.strip():
                raise StructuredPayloadError("curriculum section names must be non-empty strings")
            if any(char in name for char in "\r\n"):
                raise StructuredPayloadError(
                    "curriculum section names cannot contain newlines or control characters"
                )
            if not isinstance(content, str) or not content.strip():
                raise StructuredPayloadError(f"curriculum section '{name.strip()}' is empty")
            normalized[name.strip()] = content.strip()
        return ProviderPayload(kind, sections=normalized, citations=citations)
    content = _text(payload, "content")
    language = None
    if kind == "translation":
        language = _text(payload, "target_language")
    return ProviderPayload(
        kind,
        content=content,
        citations=citations,
        target_language=language,
    )


def payload_markdown(payload: ProviderPayload) -> str:
    """Render a validated payload for the existing Markdown-based writers."""

    if payload.sections is not None:
        return "\n\n".join(f"# {name}\n\n{content}" for name, content in payload.sections.items())
    return payload.content
