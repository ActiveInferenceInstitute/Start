"""Tests for the entity research module."""

from __future__ import annotations

import os
from pathlib import Path

from src.perplexity.entity import ResearchResult, chat, research_target_audience


def test_research_result_dataclass():
    """Test ResearchResult dataclass creation and attributes."""
    result = ResearchResult(
        timestamp="2024-01-01T12:00:00",
        entity_name="test_entity",
        entity_description="Test entity description",
        research_data="Test research data content",
        processing_time="2.30 seconds",
    )

    assert result.timestamp == "2024-01-01T12:00:00"
    assert result.entity_name == "test_entity"
    assert result.entity_description == "Test entity description"
    assert result.research_data == "Test research data content"
    assert result.processing_time == "2.30 seconds"


def test_chat_function(monkeypatch):
    """Test chat function with mocked OpenAI client."""

    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    class MockChoice:
        def __init__(self, content):
            self.message = MockMessage(content)

    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockCompletions:
        def create(self, model, messages):
            return MockResponse("Mock research response")

    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()

    class MockClient:
        def __init__(self):
            self.chat = MockChat()

    mock_client = MockClient()
    result = chat(mock_client, "test prompt", "test system")
    assert result == "Mock research response"


def test_research_target_audience_file_processing(tmp_path, monkeypatch):
    """Test research_target_audience function with file I/O (using mocked client)."""

    # Create test files
    entity_file = tmp_path / "test_entity.md"
    entity_file.write_text("Test entity content", encoding="utf-8")

    fep_actinf_file = tmp_path / "fep_actinf.md"
    fep_actinf_file.write_text("Test FEP-ActInf data", encoding="utf-8")

    # Mock the OpenAI client
    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    class MockChoice:
        def __init__(self, content):
            self.message = MockMessage(content)

    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockCompletions:
        def create(self, model, messages):
            return MockResponse("Mock audience research data")

    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()

    class MockClient:
        def __init__(self):
            self.chat = MockChat()

    mock_client = MockClient()
    output_dir = str(tmp_path / "output")

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    result = research_target_audience(
        mock_client, str(entity_file), str(fep_actinf_file), output_dir
    )

    # Check result structure
    assert isinstance(result, ResearchResult)
    assert result.entity_name == "test_entity"
    assert result.research_data == "Mock audience research data"
    assert result.timestamp  # Should have a timestamp
    assert "seconds" in result.processing_time

    # Check that output JSON file was created
    output_path = Path(output_dir)
    json_files = list(output_path.glob("test_entity_research_*.json"))

    assert len(json_files) == 1

    # Check JSON content
    import json

    with open(json_files[0], "r", encoding="utf-8") as f:
        json_data = json.load(f)

    assert json_data["entity_name"] == "test_entity"
    assert json_data["research_data"] == "Mock audience research data"
    assert json_data["timestamp"] == result.timestamp
    assert json_data["processing_time"] == result.processing_time


def test_research_target_audience_default_output_dir(tmp_path, monkeypatch):
    """Test research_target_audience with default output directory."""

    # Mock data_audience_research_dir to return tmp_path
    def mock_data_audience_research_dir():
        return tmp_path

    import src.perplexity.entity

    monkeypatch.setattr(
        src.perplexity.entity, "data_audience_research_dir", mock_data_audience_research_dir
    )

    # Create test files
    entity_file = tmp_path / "test_entity.md"
    entity_file.write_text("Test entity content", encoding="utf-8")

    fep_actinf_file = tmp_path / "fep_actinf.md"
    fep_actinf_file.write_text("Test FEP-ActInf data", encoding="utf-8")

    # Mock the OpenAI client
    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    class MockChoice:
        def __init__(self, content):
            self.message = MockMessage(content)

    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockCompletions:
        def create(self, model, messages):
            return MockResponse("Mock research with default dir")

    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()

    class MockClient:
        def __init__(self):
            self.chat = MockChat()

    mock_client = MockClient()

    # Call with empty output_dir to test default
    result = research_target_audience(mock_client, str(entity_file), str(fep_actinf_file), "")

    # Check result
    assert isinstance(result, ResearchResult)
    assert result.entity_name == "test_entity"
    assert result.research_data == "Mock research with default dir"

    # Check that output file was created in default location
    json_files = list(tmp_path.glob("test_entity_research_*.json"))
    assert len(json_files) == 1


def test_research_target_audience_real_client():
    """Integration test with Perplexity client (uses mock if no key available)."""
    from src.perplexity.clients import PerplexityConfig, build_perplexity_client

    if not os.getenv("PERPLEXITY_API_KEY"):
        # Use mock configuration for testing when no real key available
        config = PerplexityConfig(api_key="mock_key_for_testing")
        client = build_perplexity_client(config)
        assert hasattr(client, "chat")

        # Test that we can create the client without errors
        assert client.api_key == "mock_key_for_testing"
        assert client.base_url == "https://api.perplexity.ai"
    else:
        # Use real key when available (CI or real environment)
        client = build_perplexity_client()
        assert hasattr(client, "chat")
