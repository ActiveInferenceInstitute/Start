"""LLM clients for Perplexity (research) and OpenRouter (content generation).

This module provides modular access to different LLM providers:
- Perplexity: For online research tasks requiring real-time information
- OpenRouter: For content generation, translation, and curriculum tasks
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from src.common.env import load_project_env, require_env


@dataclass(frozen=True)
class PerplexityConfig:
    """Configuration for Perplexity AI client.
    
    Used for research tasks that require online/real-time information access.
    """
    api_key: str
    base_url: str = "https://api.perplexity.ai"
    model: str = os.environ.get("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online")


@dataclass(frozen=True)
class OpenRouterConfig:
    """Configuration for OpenRouter client.
    
    Used for content generation tasks like translation and curriculum creation.
    """
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")


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
    load_project_env()
    if config is None:
        api_key = os.environ.get("PERPLEXITY_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "PERPLEXITY_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
        
        # Basic validation of API key format
        if len(api_key.strip()) < 10:
            raise ValueError("PERPLEXITY_API_KEY appears to be invalid (too short)")
        
        config = PerplexityConfig(api_key=api_key.strip())
    
    # Validate config parameters
    if not config.api_key or not config.api_key.strip():
        raise ValueError("API key cannot be empty")
    
    if not config.base_url or not config.base_url.startswith('http'):
        raise ValueError(f"Invalid base URL: {config.base_url}")
    
    if not config.model or not config.model.strip():
        raise ValueError("Model name cannot be empty")
    
    try:
        return OpenAI(api_key=config.api_key, base_url=config.base_url)
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
    load_project_env()
    if config is None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
        
        # Basic validation of API key format
        if len(api_key.strip()) < 10:
            raise ValueError("OPENROUTER_API_KEY appears to be invalid (too short)")
        
        config = OpenRouterConfig(api_key=api_key.strip())
    
    # Validate config parameters
    if not config.api_key or not config.api_key.strip():
        raise ValueError("API key cannot be empty")
    
    if not config.base_url or not config.base_url.startswith('http'):
        raise ValueError(f"Invalid base URL: {config.base_url}")
    
    if not config.model or not config.model.strip():
        raise ValueError("Model name cannot be empty")
    
    try:
        return OpenAI(api_key=config.api_key, base_url=config.base_url)
    except Exception as e:
        raise EnvironmentError(f"Failed to create OpenRouter client: {str(e)}") from e



