from __future__ import annotations

import pytest

from src.perplexity.clients import (
    ChatPolicy,
    OpenRouterConfig,
    PerplexityConfig,
    build_openrouter_client,
    build_perplexity_client,
)


def test_provider_configs_are_explicit() -> None:
    perplexity = PerplexityConfig(api_key="configured", model="research-model")
    openrouter = OpenRouterConfig(api_key="configured", model="content-model")
    assert build_perplexity_client(perplexity).base_url.host == "api.perplexity.ai"
    assert build_openrouter_client(openrouter).base_url.host == "openrouter.ai"
    assert ChatPolicy(model="local", min_content_length=3).model == "local"


def test_provider_credentials_are_required(monkeypatch) -> None:
    monkeypatch.setenv("PERPLEXITY_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with pytest.raises(EnvironmentError):
        build_perplexity_client()
    with pytest.raises(EnvironmentError):
        build_openrouter_client()


def test_policy_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="max_retries"):
        ChatPolicy(model="local", max_retries=0)
