"""Tests for the domain analysis module.

Uses real test fixtures (Domestic Test Object pattern) instead of mocks.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.perplexity.domain import DomainResult, analyze_domain, chat
from fixtures import ApiTestClient


class TestDomainResult:
    """Tests for DomainResult dataclass."""

    def test_domain_result_dataclass(self):
        """Test DomainResult dataclass creation and attributes."""
        result = DomainResult(
            timestamp="2024-01-01T12:00:00",
            domain_name="test_domain",
            domain_analysis="Test analysis content",
            curriculum_content="Test curriculum content",
            processing_time="1.50 seconds",
        )

        assert result.timestamp == "2024-01-01T12:00:00"
        assert result.domain_name == "test_domain"
        assert result.domain_analysis == "Test analysis content"
        assert result.curriculum_content == "Test curriculum content"
        assert result.processing_time == "1.50 seconds"

    def test_domain_result_with_empty_fields(self):
        """Test DomainResult with empty optional fields."""
        result = DomainResult(
            timestamp="2024-01-01T12:00:00",
            domain_name="minimal_domain",
            domain_analysis="",
            curriculum_content="",
            processing_time="0.10 seconds",
        )

        assert result.domain_name == "minimal_domain"
        assert result.domain_analysis == ""
        assert result.curriculum_content == ""


class TestChatFunction:
    """Tests for the chat function."""

    def test_chat_function_with_test_client(self):
        """Test chat function with real test client."""
        client = ApiTestClient(responses={"test": "AI response for test"})
        result = chat(client, "test prompt", "test system")
        assert result == "AI response for test"

    def test_chat_function_returns_string(self):
        """Test that chat function always returns a string."""
        client = ApiTestClient()
        result = chat(client, "any prompt", "any system")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_chat_function_with_different_prompts(self):
        """Test chat function with different prompts."""
        client = ApiTestClient(
            responses={
                "domain": "Domain response",
                "entity": "Entity response",
            }
        )

        domain_result = chat(client, "domain analysis prompt", "system")
        entity_result = chat(client, "entity research prompt", "system")

        assert domain_result == "Domain response"
        assert entity_result == "Entity response"


class TestAnalyzeDomain:
    """Tests for the analyze_domain function."""

    def test_analyze_domain_file_processing(self, tmp_path):
        """Test analyze_domain function with file I/O."""
        # Create test files
        domain_file = tmp_path / "test_domain.md"
        domain_file.write_text("Test domain content", encoding="utf-8")

        fep_actinf_file = tmp_path / "fep_actinf.md"
        fep_actinf_file.write_text("Test FEP-ActInf data", encoding="utf-8")

        # Create test client with appropriate responses
        client = ApiTestClient.for_domain_analysis(
            analysis="Real domain analysis result",
            curriculum="Real curriculum content",
        )

        output_dir = str(tmp_path / "output")
        Path(output_dir).mkdir(exist_ok=True)

        result = analyze_domain(client, str(domain_file), str(fep_actinf_file), output_dir)

        # Check result structure
        assert isinstance(result, DomainResult)
        assert result.domain_name == "test_domain"
        assert result.domain_analysis == "Real domain analysis result"
        assert result.curriculum_content == "Real curriculum content"
        assert result.timestamp  # Should have a timestamp
        assert "seconds" in result.processing_time

        # Check that output files were created
        output_path = Path(output_dir)
        json_files = list(output_path.glob("test_domain_research_*.json"))
        md_files = list(output_path.glob("test_domain_research_*.md"))

        assert len(json_files) == 1
        assert len(md_files) == 1

        # Check JSON content
        with open(json_files[0], "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert json_data["domain_name"] == "test_domain"
        assert json_data["domain_analysis"] == "Real domain analysis result"
        assert json_data["curriculum_content"] == "Real curriculum content"

        # Check Markdown content
        md_content = md_files[0].read_text(encoding="utf-8")
        assert "# test_domain Domain Research Report" in md_content
        assert "## Domain Analysis" in md_content
        assert "## Curriculum Content" in md_content
        assert "Real domain analysis result" in md_content
        assert "Real curriculum content" in md_content

    def test_analyze_domain_with_complex_content(self, tmp_path):
        """Test analyze_domain with longer, more realistic content."""
        # Create test files with realistic content
        domain_file = tmp_path / "neuroscience.md"
        domain_file.write_text(
            """# Neuroscience Domain
            
            Neuroscience is the scientific study of the nervous system.
            It encompasses molecular, cellular, developmental, structural,
            functional, and computational aspects of the nervous system.
            """,
            encoding="utf-8",
        )

        fep_actinf_file = tmp_path / "fep_actinf.md"
        fep_actinf_file.write_text(
            """# Free Energy Principle and Active Inference
            
            The Free Energy Principle provides a unified framework for
            understanding perception, learning, and action in biological systems.
            """,
            encoding="utf-8",
        )

        # Create test client
        client = ApiTestClient.for_domain_analysis(
            analysis="Comprehensive neuroscience domain analysis covering neural systems, "
            "brain function, and applications to Active Inference.",
            curriculum="Structured curriculum covering neural computation, "
            "predictive processing, and practical applications.",
        )

        output_dir = str(tmp_path / "output")
        Path(output_dir).mkdir(exist_ok=True)

        result = analyze_domain(client, str(domain_file), str(fep_actinf_file), output_dir)

        assert result.domain_name == "neuroscience"
        assert "neuroscience" in result.domain_analysis.lower()
        assert len(result.domain_analysis) > 50
        assert len(result.curriculum_content) > 50


class TestClientIntegration:
    """Integration tests for client building and usage."""

    def test_perplexity_client_config(self):
        """Test Perplexity client configuration without API key."""
        from src.perplexity.clients import PerplexityConfig, build_perplexity_client

        if not os.getenv("PERPLEXITY_API_KEY"):
            # Use test configuration when no real key available
            config = PerplexityConfig(api_key="test_key_for_validation")
            client = build_perplexity_client(config)
            assert hasattr(client, "chat")
            assert client.api_key == "test_key_for_validation"
            assert client.base_url == "https://api.perplexity.ai"
        else:
            # Use real key when available (CI or real environment)
            client = build_perplexity_client()
            assert hasattr(client, "chat")

    def test_openrouter_client_config(self):
        """Test OpenRouter client configuration without API key."""
        from src.perplexity.clients import OpenRouterConfig, build_openrouter_client

        if not os.getenv("OPENROUTER_API_KEY"):
            # Use test configuration when no real key available
            config = OpenRouterConfig(api_key="test_key_for_validation")
            client = build_openrouter_client(config)
            assert hasattr(client, "chat")
            assert client.api_key == "test_key_for_validation"
            assert str(client.base_url).rstrip("/") == "https://openrouter.ai/api/v1"
        else:
            # Use real key when available (CI or real environment)
            client = build_openrouter_client()
            assert hasattr(client, "chat")
