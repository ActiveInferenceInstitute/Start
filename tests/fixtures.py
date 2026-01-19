"""Test fixtures for the START project.

This module provides REAL test fixtures (not mocks) that implement the same
interfaces as production code. Following the 'Domestic Test Object' pattern,
these fixtures provide predictable responses for testing without making
external API calls.

Note: Class names start with 'Api' instead of 'Test' to avoid pytest collection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ApiMessage:
    """Real message object matching OpenAI response format."""

    content: str


@dataclass
class ApiChoice:
    """Real choice object matching OpenAI response format."""

    message: ApiMessage
    index: int = 0
    finish_reason: str = "stop"


@dataclass
class ApiResponse:
    """Real response object matching OpenAI response format."""

    choices: List[ApiChoice]
    model: str = "test-model"
    id: str = "test-response-id"

    @classmethod
    def from_content(cls, content: str) -> "ApiResponse":
        """Create a response with the given content."""
        return cls(choices=[ApiChoice(message=ApiMessage(content=content))])


class ApiCompletions:
    """Real completions interface for testing."""

    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """Initialize with optional keyword-to-response mapping.

        Args:
            responses: Dict mapping keywords in prompts to response content.
                      If a keyword is found in the prompt, that response is returned.
                      Keys are checked in order, first match wins.
        """
        self._responses = responses or {}
        self._default_response = "Default test response content"
        self._call_count = 0
        self._last_messages: Optional[List[Dict[str, str]]] = None

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> ApiResponse:
        """Create a completion - real implementation.

        Args:
            model: The model name (not used in test)
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters (timeout, etc.)

        Returns:
            ApiResponse with appropriate content based on the messages
        """
        self._call_count += 1
        self._last_messages = messages

        # Combine all message content for keyword matching
        all_content = " ".join(
            msg.get("content", "") for msg in messages if isinstance(msg, dict)
        ).lower()

        # Check system message specifically for discriminating between calls
        system_content = ""
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "system":
                system_content = msg.get("content", "").lower()
                break

        # Find matching response based on keywords (check system first, then all content)
        for keyword, response in self._responses.items():
            keyword_lower = keyword.lower()
            if keyword_lower in system_content or keyword_lower in all_content:
                return ApiResponse.from_content(response)

        return ApiResponse.from_content(self._default_response)

    @property
    def call_count(self) -> int:
        """Return the number of times create was called."""
        return self._call_count

    @property
    def last_messages(self) -> Optional[List[Dict[str, str]]]:
        """Return the messages from the last call."""
        return self._last_messages


class ApiChat:
    """Real chat interface for testing."""

    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """Initialize with completions interface.

        Args:
            responses: Dict mapping keywords in prompts to response content.
        """
        self.completions = ApiCompletions(responses)


class ApiTestClient:
    """Real test client implementing the OpenAI client interface.

    This is NOT a mock - it's a real implementation that follows the same
    interface as the OpenAI client but returns predictable test data.
    """

    def __init__(
        self,
        api_key: str = "test-api-key",
        base_url: str = "https://test.api.endpoint",
        responses: Optional[Dict[str, str]] = None,
    ):
        """Initialize the test client.

        Args:
            api_key: Test API key (stored but not validated)
            base_url: Test base URL (stored but not used)
            responses: Dict mapping keywords in prompts to response content.
                      Example: {"domain analysis": "Analysis result", "curriculum": "Curriculum content"}
        """
        self.api_key = api_key
        self.base_url = base_url
        self.chat = ApiChat(responses)

    @classmethod
    def for_domain_analysis(cls, analysis: str, curriculum: str) -> "ApiTestClient":
        """Create a client configured for domain analysis testing.

        The responses are matched against the SYSTEM prompts, which contain:
        - "domain analysis" for the analysis call
        - "curriculum develop" for the curriculum call

        Args:
            analysis: Response content for domain analysis prompts
            curriculum: Response content for curriculum prompts

        Returns:
            ApiTestClient configured with appropriate responses
        """
        return cls(
            responses={
                # Order matters: check curriculum developer first (more specific)
                # SYSTEM_CURRICULUM contains "curriculum developer"
                # SYSTEM_ANALYSIS contains "researcher"
                "curriculum developer": curriculum,
                "researcher": analysis,
            }
        )

    @classmethod
    def for_entity_research(cls, research_content: str) -> "ApiTestClient":
        """Create a client configured for entity research testing.

        Args:
            research_content: Response content for entity research prompts

        Returns:
            ApiTestClient configured with appropriate responses
        """
        return cls(
            responses={
                "entity": research_content,
                "research": research_content,
            }
        )

    @classmethod
    def for_translation(cls, translated_content: str) -> "ApiTestClient":
        """Create a client configured for translation testing.

        Args:
            translated_content: Response content for translation prompts

        Returns:
            ApiTestClient configured with appropriate responses
        """
        return cls(
            responses={
                "translate": translated_content,
                "translation": translated_content,
            }
        )
