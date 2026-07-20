"""LLM clients for Perplexity (research) and OpenRouter (content generation).

This module provides modular access to different LLM providers:
- Perplexity: For online research tasks requiring real-time information
- OpenRouter: For content generation, translation, and curriculum tasks
"""

from __future__ import annotations

import math
import os
import random
import re
import threading
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import urlparse

from openai import OpenAI

from src.common.env import load_project_env


@dataclass(frozen=True)
class PerplexityConfig:
    """Configuration for Perplexity AI client.

    Used for research tasks that require online/real-time information access.
    """

    api_key: str
    base_url: str = "https://api.perplexity.ai"
    model: str = "llama-3.1-sonar-small-128k-online"
    timeout: float = 60.0
    max_retries: int = 3
    backoff_seconds: float = 1.0

    def __post_init__(self) -> None:
        _validate_provider_settings(
            self.api_key,
            self.base_url,
            self.model,
            self.timeout,
            self.max_retries,
            self.backoff_seconds,
        )


@dataclass(frozen=True)
class OpenRouterConfig:
    """Configuration for OpenRouter client.

    Used for content generation tasks like translation and curriculum creation.
    """

    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "anthropic/claude-3.5-sonnet"
    timeout: float = 120.0
    max_retries: int = 3
    backoff_seconds: float = 1.0

    def __post_init__(self) -> None:
        _validate_provider_settings(
            self.api_key,
            self.base_url,
            self.model,
            self.timeout,
            self.max_retries,
            self.backoff_seconds,
        )


@dataclass(frozen=True)
class ChatPolicy:
    """Execution policy shared by all provider calls."""

    model: str
    timeout: float = 120.0
    max_retries: int = 3
    backoff_seconds: float = 1.0
    min_content_length: int = 1
    delay_seconds: float = 0.0
    max_backoff_seconds: float = 30.0
    jitter_seconds: float = 0.25
    input_cost_per_million: float = 0.0
    output_cost_per_million: float = 0.0
    response_format: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("Model name cannot be empty")
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        if self.max_retries < 1:
            raise ValueError("max_retries must be at least one")
        if (
            not math.isfinite(self.backoff_seconds)
            or not math.isfinite(self.delay_seconds)
            or self.backoff_seconds < 0
            or self.delay_seconds < 0
        ):
            raise ValueError("backoff_seconds and delay_seconds cannot be negative")
        if (
            not math.isfinite(self.max_backoff_seconds)
            or not math.isfinite(self.jitter_seconds)
            or self.max_backoff_seconds < 0
            or self.jitter_seconds < 0
        ):
            raise ValueError("backoff and jitter bounds cannot be negative")
        if (
            not math.isfinite(self.input_cost_per_million)
            or not math.isfinite(self.output_cost_per_million)
            or self.input_cost_per_million < 0
            or self.output_cost_per_million < 0
        ):
            raise ValueError("token costs cannot be negative")
        if self.min_content_length < 1:
            raise ValueError("min_content_length must be positive")


def validate_chat_response(response: object, *, min_content_length: int = 1) -> str:
    """Extract and validate assistant text from an OpenAI-compatible response."""
    if min_content_length < 1:
        raise ValueError("min_content_length must be positive")
    try:
        choices = response.choices
        message = choices[0].message
        content = message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("Provider response does not contain a completion choice") from exc
    if not isinstance(content, str) or len(content.strip()) < min_content_length:
        raise ValueError(
            f"Provider response content is empty or shorter than {min_content_length} characters"
        )
    return content.strip()


def _validate_provider_settings(
    api_key: str,
    base_url: str,
    model: str,
    timeout: float,
    max_retries: int,
    backoff_seconds: float,
) -> None:
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("API key cannot be empty")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid base URL: {base_url}")
    ChatPolicy(
        model=model,
        timeout=timeout,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
    )


@dataclass(frozen=True)
class CompletionUsage:
    """Provider usage information normalized across compatible APIs."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    actual_cost_usd: float | None = None

    def as_dict(self) -> dict[str, float | int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "actual_cost_usd": (
                self.estimated_cost_usd if self.actual_cost_usd is None else self.actual_cost_usd
            ),
            "requests": 1,
        }


@dataclass(frozen=True)
class CompletionResult:
    """Validated completion text plus operational metadata."""

    content: str
    model: str
    provider: str
    attempts: int
    usage: CompletionUsage = CompletionUsage()

    def as_dict(self) -> dict[str, object]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "attempts": self.attempts,
            "usage": self.usage.as_dict(),
        }


class ProviderRequestError(RuntimeError):
    """Base error for provider calls that were not successfully completed."""

    def __init__(self, message: str, *, retryable: bool = False, attempts: int = 0):
        super().__init__(_redact_sensitive(message))
        self.retryable = retryable
        self.attempts = attempts


class ProviderOfflineError(ProviderRequestError):
    """Raised when an offline run reaches a live provider boundary."""


def _wait_with_cancellation(
    seconds: float, cancellation_event: threading.Event | None = None
) -> bool:
    """Wait without making cancellation wait for a backoff or pacing delay."""

    if seconds <= 0:
        return bool(cancellation_event and cancellation_event.is_set())
    if cancellation_event is None:
        time.sleep(seconds)
        return False
    return cancellation_event.wait(seconds)


class RequestLimiter:
    """Small process-local limiter for concurrent provider requests."""

    def __init__(self, max_concurrent: int = 1, min_interval_seconds: float = 0.0):
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least one")
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds cannot be negative")
        self._semaphore = threading.BoundedSemaphore(max_concurrent)
        self._min_interval = min_interval_seconds
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def acquire(self, cancellation_event: threading.Event | None = None) -> None:
        """Acquire a slot while allowing callers to cancel a queued request."""

        while not self._semaphore.acquire(timeout=0.05):
            if cancellation_event is not None and cancellation_event.is_set():
                raise ProviderRequestError("provider request cancelled")
        with self._lock:
            wait = max(0.0, self._next_allowed - time.monotonic())
            self._next_allowed = max(time.monotonic(), self._next_allowed) + self._min_interval
        if _wait_with_cancellation(wait, cancellation_event):
            self.release()
            raise ProviderRequestError("provider request cancelled")

    def release(self) -> None:
        self._semaphore.release()

    def __enter__(self) -> "RequestLimiter":
        self.acquire()
        return self

    def __exit__(self, *_args: object) -> None:
        self.release()


def _retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    value = headers.get("retry-after") or headers.get("Retry-After")
    try:
        return max(0.0, float(value)) if value is not None else None
    except (TypeError, ValueError):
        if not value:
            return None
        try:
            target = parsedate_to_datetime(str(value)).timestamp()
            return max(0.0, target - time.time())
        except (TypeError, ValueError, OverflowError):
            return None


def _redact_sensitive(value: object) -> str:
    """Remove common credential forms and cap provider text exposed to callers."""

    text = str(value)
    text = re.sub(r"(?:sk|pplx)-[A-Za-z0-9_-]+", "[redacted-key]", text)
    text = re.sub(r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [redacted]", text, flags=re.IGNORECASE)
    text = re.sub(r"(?i)(api[_ -]?key\s*[:=]\s*)\S+", r"\1[redacted]", text)
    return text[:500]


def _safe_provider_error(exc: Exception) -> str:
    """Expose only provider error class/status, never prompt or response text."""

    status_code = getattr(exc, "status_code", None)
    status = f" status={status_code}" if isinstance(status_code, int) else ""
    redacted = _redact_sensitive(exc)
    credential_marker = " [redacted-key]" if "[redacted-key]" in redacted else ""
    return f"{type(exc).__name__}{status}{credential_marker}"


def _is_retryable_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return status_code in {408, 409, 425, 429} or status_code >= 500
    name = type(exc).__name__.lower()
    return any(token in name for token in ("timeout", "connection", "rate_limit"))


def _usage_from_response(response: object, policy: ChatPolicy) -> CompletionUsage:
    usage = getattr(response, "usage", None)
    prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion = int(getattr(usage, "completion_tokens", 0) or 0)
    total = int(getattr(usage, "total_tokens", prompt + completion) or 0)
    cost = (
        prompt * policy.input_cost_per_million + completion * policy.output_cost_per_million
    ) / 1_000_000
    provider_cost = getattr(usage, "cost", None)
    if provider_cost is None:
        provider_cost = getattr(usage, "total_cost", None)
    try:
        actual_cost = max(0.0, float(provider_cost)) if provider_cost is not None else None
    except (TypeError, ValueError):
        actual_cost = None
    return CompletionUsage(prompt, completion, total, cost, actual_cost)


def complete_chat_result(
    client: OpenAI,
    messages: list[dict[str, str]],
    policy: ChatPolicy,
    *,
    provider: str = "openai-compatible",
    limiter: RequestLimiter | None = None,
    offline: bool = False,
    cancellation_event: threading.Event | None = None,
) -> CompletionResult:
    """Execute a bounded request and return validated text plus usage metadata."""

    if offline:
        raise ProviderOfflineError("offline mode refuses live provider requests")
    if client is None or not hasattr(client, "chat"):
        raise ValueError("client must provide a chat completions interface")
    if not messages or any(
        not isinstance(message, dict)
        or not isinstance(message.get("role"), str)
        or not isinstance(message.get("content"), str)
        or not message["content"].strip()
        for message in messages
    ):
        raise ValueError("messages must contain non-empty role and content strings")
    last_error: Exception | None = None
    for attempt in range(policy.max_retries):
        if cancellation_event is not None and cancellation_event.is_set():
            raise ProviderRequestError("provider request cancelled", attempts=attempt)
        try:
            if limiter is None:
                request = {"model": policy.model, "messages": messages, "timeout": policy.timeout}
                if policy.response_format is not None:
                    request["response_format"] = policy.response_format
                response = client.chat.completions.create(**request)
            else:
                limiter.acquire(cancellation_event)
                try:
                    request = {
                        "model": policy.model,
                        "messages": messages,
                        "timeout": policy.timeout,
                    }
                    if policy.response_format is not None:
                        request["response_format"] = policy.response_format
                    response = client.chat.completions.create(**request)
                finally:
                    limiter.release()
            content = validate_chat_response(response, min_content_length=policy.min_content_length)
            if _wait_with_cancellation(policy.delay_seconds, cancellation_event):
                raise ProviderRequestError("provider request cancelled", attempts=attempt + 1)
            return CompletionResult(
                content=content,
                model=policy.model,
                provider=provider,
                attempts=attempt + 1,
                usage=_usage_from_response(response, policy),
            )
        except Exception as exc:
            if isinstance(exc, ProviderRequestError):
                raise
            last_error = exc
            retryable = _is_retryable_error(exc)
            if not retryable or attempt + 1 >= policy.max_retries:
                raise ProviderRequestError(
                    "Chat completion failed after "
                    f"{attempt + 1} attempt(s): {_safe_provider_error(exc)}",
                    retryable=retryable,
                    attempts=attempt + 1,
                ) from exc
            retry_after = _retry_after_seconds(exc)
            delay = (
                retry_after if retry_after is not None else policy.backoff_seconds * (2**attempt)
            )
            delay = min(policy.max_backoff_seconds, delay)
            if policy.jitter_seconds:
                delay += random.uniform(0.0, policy.jitter_seconds)
            if _wait_with_cancellation(delay, cancellation_event):
                raise ProviderRequestError(
                    "provider request cancelled", attempts=attempt + 1
                ) from exc
    raise ProviderRequestError(
        "Chat completion failed after "
        f"{policy.max_retries} attempts: {_safe_provider_error(last_error)}",
        retryable=_is_retryable_error(last_error) if last_error else False,
        attempts=policy.max_retries,
    ) from last_error


class ProviderAdapter:
    """Provider boundary carrying stable identity and operational policy."""

    def __init__(
        self,
        client: OpenAI,
        *,
        provider: str,
        policy: ChatPolicy,
        limiter: RequestLimiter | None = None,
        offline: bool = False,
        cancellation_event: threading.Event | None = None,
    ) -> None:
        if not provider or not provider.strip():
            raise ValueError("provider cannot be empty")
        self.client = client
        self.provider = provider.strip()
        self.policy = policy
        self.limiter = limiter
        self.offline = offline
        self.cancellation_event = cancellation_event

    def complete(self, messages: list[dict[str, str]]) -> CompletionResult:
        """Complete a request using the configured provider policy."""

        return complete_chat_result(
            self.client,
            messages,
            self.policy,
            provider=self.provider,
            limiter=self.limiter,
            offline=self.offline,
            cancellation_event=self.cancellation_event,
        )


def _validate_config(config: PerplexityConfig | OpenRouterConfig) -> None:
    _validate_provider_settings(
        config.api_key,
        config.base_url,
        config.model,
        config.timeout,
        config.max_retries,
        config.backoff_seconds,
    )


def build_perplexity_client(config: Optional[PerplexityConfig] = None) -> OpenAI:
    """Build Perplexity client for research tasks.

    Args:
        config: Optional configuration. If None, loads from environment.

    Returns:
        OpenAI client configured for Perplexity API

    Raises:
        EnvironmentError: If PERPLEXITY_API_KEY is not found or invalid
        ValueError: If configuration parameters are invalid
    """
    if config is None:
        load_project_env()
        api_key = os.environ.get("PERPLEXITY_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "PERPLEXITY_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )

        # Basic validation of API key format
        if len(api_key.strip()) < 10:
            raise ValueError("PERPLEXITY_API_KEY appears to be invalid (too short)")

        config = PerplexityConfig(
            api_key=api_key.strip(),
            model=os.environ.get("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
        )

    _validate_config(config)

    try:
        return OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0,
        )
    except Exception as e:
        raise EnvironmentError(f"Failed to create Perplexity client: {str(e)}") from e


def build_openrouter_client(config: Optional[OpenRouterConfig] = None) -> OpenAI:
    """Build OpenRouter client for content generation tasks.

    Args:
        config: Optional configuration. If None, loads from environment.

    Returns:
        OpenAI client configured for OpenRouter API

    Raises:
        EnvironmentError: If OPENROUTER_API_KEY is not found or invalid
        ValueError: If configuration parameters are invalid
    """
    if config is None:
        load_project_env()
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )

        # Basic validation of API key format
        if len(api_key.strip()) < 10:
            raise ValueError("OPENROUTER_API_KEY appears to be invalid (too short)")

        config = OpenRouterConfig(
            api_key=api_key.strip(),
            model=os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        )

    _validate_config(config)

    try:
        return OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0,
        )
    except Exception as e:
        raise EnvironmentError(f"Failed to create OpenRouter client: {str(e)}") from e
