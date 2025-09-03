# Testing Guide

This document provides comprehensive information about testing in the Active Inference curriculum generation system.

## Test Structure

The test suite is organized into several categories:

### Unit Tests
- **API Clients** (`test_clients.py`): Tests for Perplexity and OpenRouter API clients
- **Common Utilities** (`test_common_*.py`): Tests for shared utilities (IO, logging, paths, etc.)
- **Core Modules** (`test_domain.py`, `test_entity.py`): Tests for core domain analysis functionality
- **Configuration** (`test_config.py`, `test_languages_config.py`): Configuration loading and validation tests
- **System Components** (`test_system_*.py`): System reporting and dependency checking tests

### Script Tests  
- **Research Scripts** (`test_1_research_domain.py`, `test_2_write_introduction.py`): Tests for research pipeline scripts
- **Visualization Scripts** (`test_3_introduction_visualizations.py`): Tests for curriculum visualization generation
- **Translation Scripts** (`test_4_translate_introductions.py`): Tests for multi-language curriculum translation

### Integration Tests
- **End-to-End Workflows** (`test_integration.py`): Complete pipeline tests
- **Script Integration** (`test_curriculum_scripts_integration.py`): Cross-script integration tests
- **Repository Management** (`test_repos_*.py`): Repository cloning and management tests

## Running Tests

### Full Test Suite
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Specific Test Categories
```bash
# Run only unit tests (exclude integration/slow tests)
uv run pytest -m "not integration and not slow"

# Run integration tests
uv run pytest -m integration

# Run tests for specific component
uv run pytest tests/test_clients.py
uv run pytest tests/test_domain.py

# Run tests matching pattern
uv run pytest -k "test_domain"
```

### Test Markers

The test suite uses pytest markers to categorize tests:

- `@pytest.mark.integration`: Tests that require external resources or full system setup
- `@pytest.mark.slow`: Tests that take significant time to run
- `@pytest.mark.network`: Tests that require network connectivity

### Environment Setup for Tests

Some tests require specific environment setup:

```bash
# Set required environment variables for API tests
export PERPLEXITY_API_KEY="your-test-key-here"
export OPENROUTER_API_KEY="your-test-key-here"

# Use non-GUI matplotlib backend to prevent display issues
export MPLBACKEND=Agg

# Run tests
uv run pytest
```

## Test Development Guidelines

### Writing New Tests

1. **Naming Convention**: Test files should be named `test_<module_name>.py`
2. **Class Organization**: Group related tests in classes with descriptive names
3. **Test Methods**: Use descriptive method names that clearly indicate what is being tested
4. **Docstrings**: Include docstrings explaining what each test validates

Example:
```python
class TestDomainAnalysis:
    """Test domain analysis functionality."""
    
    def test_analyze_domain_with_valid_input(self):
        """Test domain analysis with valid input data."""
        # Test implementation
        pass
        
    def test_analyze_domain_with_invalid_input(self):
        """Test domain analysis error handling with invalid input."""
        # Test implementation  
        pass
```

### Mocking Guidelines

1. **Mock External Dependencies**: Always mock API calls, file system operations, and external services
2. **Use Appropriate Mock Types**: Use `Mock` for simple objects, `MagicMock` for complex behavior
3. **Patch at the Right Level**: Patch the module where the function is used, not where it's defined

Example:
```python
@patch('src.perplexity.domain.chat')
def test_domain_analysis_success(self, mock_chat):
    """Test successful domain analysis."""
    mock_chat.return_value = "Mock analysis result"
    # Test implementation
```

### Testing File Operations

For tests involving file operations, use pytest's `tmp_path` fixture:

```python
def test_file_processing(self, tmp_path):
    """Test file processing with temporary files."""
    # Create test file
    test_file = tmp_path / "test.json"
    test_file.write_text('{"test": "data"}')
    
    # Test file processing
    result = process_file(test_file)
    assert result is not None
```

### Testing Configuration Loading

Mock configuration files rather than creating real ones:

```python
@patch('src.common.config.load_yaml_config')
def test_config_loading(self, mock_load_yaml):
    """Test configuration loading."""
    mock_load_yaml.return_value = {"test": "config"}
    config = load_config("test")
    assert config["test"] == "config"
```

## Common Test Patterns

### API Client Testing
```python
@patch('openai.OpenAI')
def test_api_client_success(self, mock_openai):
    """Test successful API client operation."""
    mock_client = Mock()
    mock_openai.return_value = mock_client
    
    # Mock API response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response
    
    # Test client usage
    result = api_function(mock_client)
    assert result == "Test response"
```

### Error Handling Testing
```python
def test_function_handles_file_not_found(self):
    """Test function properly handles missing files."""
    with pytest.raises(FileNotFoundError, match="File not found"):
        process_missing_file("/nonexistent/path")
```

### Progress Tracking Testing
```python
def test_progress_tracking(self, caplog):
    """Test that progress is properly logged."""
    with caplog.at_level(logging.INFO):
        process_multiple_items(test_items)
    
    # Verify progress messages
    assert "Processing 1/3" in caplog.text
    assert "Processing 2/3" in caplog.text
    assert "Processing 3/3" in caplog.text
```

## Troubleshooting Tests

### Common Issues and Solutions

1. **Path Mocking Issues**
   ```python
   # Instead of mocking Path attributes directly:
   # with patch.object(path, "exists", return_value=True):  # This fails
   
   # Mock the pathlib operations:
   with patch('pathlib.Path.exists', return_value=True):
       # Test code
   ```

2. **Module Loading Issues**
   ```python
   # For scripts with hyphens in names, use importlib:
   spec = importlib.util.spec_from_file_location(
       "module_name", 
       "path/to/script-with-hyphens.py"
   )
   module = importlib.util.module_from_spec(spec)
   spec.loader.exec_module(module)
   
   # Add to sys.modules for proper patching:
   sys.modules['module_name'] = module
   ```

3. **Matplotlib Display Issues**
   ```bash
   # Set non-GUI backend before running tests:
   export MPLBACKEND=Agg
   uv run pytest
   ```

4. **API Key Validation**
   ```python
   # Use keys with proper length for tests:
   monkeypatch.setenv("API_KEY", "test_key_valid_length_1234")
   ```

## Test Data Management

### Using Fixtures
```python
@pytest.fixture
def sample_research_data():
    """Provide sample research data for tests."""
    return {
        "domain_name": "test_domain",
        "analysis": "Test analysis content",
        "key_concepts": ["concept1", "concept2"]
    }

def test_with_fixture_data(sample_research_data):
    """Test using fixture data."""
    assert sample_research_data["domain_name"] == "test_domain"
```

### Temporary Files
```python
def test_with_temp_files(tmp_path):
    """Test with temporary files."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("test: value")
    
    result = load_config_file(config_file)
    assert result["test"] == "value"
```

## Continuous Integration

Tests are run automatically in CI/CD pipelines. To ensure compatibility:

1. **No External Dependencies**: Tests should not require external APIs or services
2. **Deterministic Results**: Tests should produce consistent results across environments
3. **Reasonable Runtime**: Keep test execution time reasonable for CI environments

## Test Coverage

Maintain high test coverage by:

1. **Testing All Public Functions**: Every public function should have at least one test
2. **Testing Error Cases**: Include tests for error conditions and edge cases  
3. **Testing Integration Points**: Test how components work together
4. **Regular Coverage Reports**: Run coverage analysis regularly to identify gaps

```bash
# Generate coverage report
uv run pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Clear Assertions**: Use descriptive assertions that clearly indicate what failed
3. **Minimal Setup**: Only set up what's necessary for each test
4. **Fast Execution**: Keep tests fast by mocking expensive operations
5. **Descriptive Names**: Use test names that clearly describe what is being tested

By following these guidelines, you can contribute effectively to the test suite and ensure the reliability of the Active Inference curriculum generation system.
