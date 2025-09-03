"""Tests for the domain analysis module."""

from __future__ import annotations

import os
from pathlib import Path

from src.perplexity.domain import DomainResult, analyze_domain, chat


def test_domain_result_dataclass():
    """Test DomainResult dataclass creation and attributes."""
    result = DomainResult(
        timestamp="2024-01-01T12:00:00",
        domain_name="test_domain",
        domain_analysis="Test analysis content",
        curriculum_content="Test curriculum content",
        processing_time="1.50 seconds"
    )
    
    assert result.timestamp == "2024-01-01T12:00:00"
    assert result.domain_name == "test_domain"
    assert result.domain_analysis == "Test analysis content"
    assert result.curriculum_content == "Test curriculum content"
    assert result.processing_time == "1.50 seconds"


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
        def create(self, model, messages, **kwargs):
            # Accept any additional kwargs like timeout
            # Return mock response based on input
            return MockResponse("Mock AI response")
    
    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()
    
    class MockClient:
        def __init__(self):
            self.chat = MockChat()
    
    mock_client = MockClient()
    result = chat(mock_client, "test prompt", "test system")
    assert result == "Mock AI response"


def test_analyze_domain_file_processing(tmp_path, monkeypatch):
    """Test analyze_domain function with file I/O (using mocked client)."""
    
    # Create test files
    domain_file = tmp_path / "test_domain.md"
    domain_file.write_text("Test domain content", encoding="utf-8")
    
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
        def create(self, model, messages, **kwargs):
            # Accept any additional kwargs like timeout
            # Return different responses based on the system message
            system_content = messages[0]["content"]
            if "domain analysis" in system_content.lower():
                return MockResponse("Mock domain analysis")
            else:
                return MockResponse("Mock curriculum content")
    
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
    
    result = analyze_domain(
        mock_client, 
        str(domain_file), 
        str(fep_actinf_file), 
        output_dir
    )
    
    # Check result structure
    assert isinstance(result, DomainResult)
    assert result.domain_name == "test_domain"
    assert result.domain_analysis == "Mock domain analysis"
    assert result.curriculum_content == "Mock curriculum content"
    assert result.timestamp  # Should have a timestamp
    assert "seconds" in result.processing_time
    
    # Check that output files were created
    output_path = Path(output_dir)
    json_files = list(output_path.glob("test_domain_research_*.json"))
    md_files = list(output_path.glob("test_domain_research_*.md"))
    
    assert len(json_files) == 1
    assert len(md_files) == 1
    
    # Check JSON content
    import json
    with open(json_files[0], 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    assert json_data["domain_name"] == "test_domain"
    assert json_data["domain_analysis"] == "Mock domain analysis"
    assert json_data["curriculum_content"] == "Mock curriculum content"
    
    # Check Markdown content
    md_content = md_files[0].read_text(encoding='utf-8')
    assert "# test_domain Domain Research Report" in md_content
    assert "## Domain Analysis" in md_content
    assert "## Curriculum Content" in md_content
    assert "Mock domain analysis" in md_content
    assert "Mock curriculum content" in md_content


def test_analyze_domain_real_client():
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
