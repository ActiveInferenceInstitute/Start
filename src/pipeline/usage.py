"""Deterministic aggregation helpers for provider usage and cost telemetry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_USAGE_KEYS = (
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "estimated_cost_usd",
    "actual_cost_usd",
    "requests",
)


def _number(value: Any, *, integer: bool = False) -> float | int:
    if isinstance(value, bool):
        return 0
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return 0
    if integer:
        return max(0, int(converted))
    return max(0.0, converted)


def empty_usage() -> dict[str, float | int]:
    """Return a stable zero-valued usage record."""

    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "actual_cost_usd": 0.0,
        "requests": 0,
    }


def normalize_usage(value: Mapping[str, Any] | None) -> dict[str, float | int]:
    """Normalize one provider usage record without exposing arbitrary fields."""

    result = empty_usage()
    if not isinstance(value, Mapping):
        return result
    result["prompt_tokens"] = _number(value.get("prompt_tokens"), integer=True)
    result["completion_tokens"] = _number(value.get("completion_tokens"), integer=True)
    result["total_tokens"] = _number(value.get("total_tokens"), integer=True)
    result["estimated_cost_usd"] = _number(value.get("estimated_cost_usd"))
    # Planned estimates and observed provider usage are intentionally kept
    # separate so a preflight estimate cannot be mistaken for spend.
    result["actual_cost_usd"] = _number(value.get("actual_cost_usd"))
    result["requests"] = _number(value.get("requests", 1), integer=True)
    if result["total_tokens"] == 0:
        result["total_tokens"] = int(result["prompt_tokens"]) + int(result["completion_tokens"])
    return result


def aggregate_usage(value: Mapping[str, Any] | None) -> dict[str, float | int]:
    """Aggregate either one record or a mapping of named records."""

    if not isinstance(value, Mapping):
        return empty_usage()
    if any(key in value for key in _USAGE_KEYS):
        return normalize_usage(value)
    total = empty_usage()
    for child in value.values():
        if isinstance(child, Mapping):
            total = merge_usage(total, aggregate_usage(child))
    return total


def merge_usage(*values: Mapping[str, Any] | None) -> dict[str, float | int]:
    """Sum normalized usage records while preserving a stable schema."""

    total = empty_usage()
    for value in values:
        record = aggregate_usage(value)
        for key in ("prompt_tokens", "completion_tokens", "total_tokens", "requests"):
            total[key] = int(total[key]) + int(record[key])
        for key in ("estimated_cost_usd", "actual_cost_usd"):
            total[key] = float(total[key]) + float(record[key])
    return total
