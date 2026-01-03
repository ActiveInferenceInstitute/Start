# LLM API Integrations Technical Reference

## Overview

Technical documentation for LLM API integration modules.

## Module: `clients.py`

### Classes

#### `PerplexityConfig`
Configuration dataclass for Perplexity AI client.

**Attributes**:
- `api_key: str`: Perplexity API key
- `base_url: str`: API base URL (default: "https://api.perplexity.ai")
- `model: str`: Model name (default: from `PERPLEXITY_MODEL` env var or "llama-3.1-sonar-small-128k-online")

**Frozen**: Yes (immutable)

#### `OpenRouterConfig`
Configuration dataclass for OpenRouter client.

**Attributes**:
- `api_key: str`: OpenRouter API key
- `base_url: str`: API base URL (default: "https://openrouter.ai/api/v1")
- `model: str`: Model name (default: from `OPENROUTER_MODEL` env var or "anthropic/claude-3.5-sonnet")

**Frozen**: Yes (immutable)

### Functions

#### `build_perplexity_client(config: Optional[PerplexityConfig] = None) -> OpenAI`
Builds Perplexity client for research tasks.

**Parameters**:
- `config`: Optional configuration. If None, loads from environment variables.

**Returns**: OpenAI client configured for Perplexity API

**Raises**:
- `EnvironmentError`: If `PERPLEXITY_API_KEY` is not found or invalid
- `ValueError`: If configuration parameters are invalid

**Environment**: Requires `PERPLEXITY_API_KEY` environment variable

#### `build_openrouter_client(config: Optional[OpenRouterConfig] = None) -> OpenAI`
Builds OpenRouter client for content generation tasks.

**Parameters**:
- `config`: Optional configuration. If None, loads from environment variables.

**Returns**: OpenAI client configured for OpenRouter API

**Raises**:
- `EnvironmentError`: If `OPENROUTER_API_KEY` is not found or invalid
- `ValueError`: If configuration parameters are invalid

**Environment**: Requires `OPENROUTER_API_KEY` environment variable

## Module: `domain.py`

### Constants

#### `SYSTEM_ANALYSIS: str`
System prompt for domain analysis tasks.

#### `SYSTEM_CURRICULUM: str`
System prompt for curriculum development tasks.

### Functions

#### `chat(client: OpenAI, prompt: str, system: str, max_retries: int = 3, retry_delay: float = 1.0) -> str`
Sends chat completion request to Perplexity for domain research.

**Parameters**:
- `client`: OpenAI client configured for Perplexity API
- `prompt`: User prompt for domain research
- `system`: System prompt defining the AI's research role
- `max_retries`: Maximum number of retry attempts (default: 3)
- `retry_delay`: Initial delay between retries in seconds (default: 1.0, uses exponential backoff)

**Returns**: Research results from Perplexity's online-enabled models

**Raises**:
- `ValueError`: If inputs are invalid
- `RuntimeError`: If API request fails after all retries

**Behavior**: Implements exponential backoff retry logic

### Classes

#### `DomainResult`
Result dataclass for domain analysis.

**Attributes**:
- `timestamp: str`: Analysis timestamp
- `domain_name: str`: Name of analyzed domain
- `domain_analysis: str`: Domain analysis content
- `curriculum_content: str`: Generated curriculum content
- `processing_time: str`: Processing time information

### Functions

#### `analyze_domain(client: OpenAI, domain_input: str, fep_actinf_input: str, output_dir: str, domain_name: Optional[str] = None) -> DomainResult`
Performs comprehensive domain analysis using Perplexity API.

**Parameters**:
- `client`: OpenAI client configured for Perplexity API
- `domain_input`: Either file path or domain content directly
- `fep_actinf_input`: Either file path or FEP/ActInf content directly
- `output_dir`: Directory to save analysis results
- `domain_name`: Optional domain name for output files

**Returns**: `DomainResult` containing analysis and metadata

**Output**: Saves JSON and Markdown files to `output_dir`

## Module: `entity.py`

### Constants

#### `SYSTEM_DESCRIPTION: str`
System prompt for entity/audience research tasks.

### Functions

#### `extract_entity_description(entity_data: str) -> str`
Extracts entity description from formatted entity data.

**Parameters**:
- `entity_data`: Formatted entity data containing name, description, and category

**Returns**: The entity description string, or the full data if parsing fails

**Behavior**: Looks for "Description:" line, falls back to full data if not found

#### `chat(client: OpenAI, prompt: str, system: str) -> str`
Sends chat completion request to Perplexity for entity research.

**Parameters**:
- `client`: OpenAI client configured for Perplexity API
- `prompt`: User prompt for entity/audience research
- `system`: System prompt defining the AI's research role

**Returns**: Research results from Perplexity's online-enabled models

### Classes

#### `ResearchResult`
Result dataclass for entity research.

**Attributes**:
- `timestamp: str`: Research timestamp
- `entity_name: str`: Name of researched entity
- `entity_description: str`: Entity description
- `research_data: str`: Research analysis content
- `processing_time: str`: Processing time information

### Functions

#### `research_target_audience(client: OpenAI, entity_input: str, fep_actinf_input: str, output_dir: str, entity_name: Optional[str] = None) -> ResearchResult`
Researches target audience using Perplexity API.

**Parameters**:
- `client`: OpenAI client configured for Perplexity API
- `entity_input`: Either file path or entity content directly
- `fep_actinf_input`: Either file path or FEP/ActInf content directly
- `output_dir`: Directory to save research results
- `entity_name`: Optional entity name for output files (extracted from path if not provided)

**Returns**: `ResearchResult` containing analysis and metadata

**Output**: Saves JSON file to `output_dir`

## Module: `curriculum.py`

### Constants

#### `SYSTEM: str`
System prompt for curriculum generation tasks.

### Functions

#### `chat(client: OpenAI, prompt: str, system: str, model: Optional[str] = None) -> str`
Sends chat completion request to OpenRouter for content generation.

**Parameters**:
- `client`: OpenAI client configured for OpenRouter
- `prompt`: User prompt for content generation
- `system`: System prompt defining the AI's role
- `model`: Optional model override (defaults to `OPENROUTER_MODEL` env var)

**Returns**: Generated content from the model

#### `validate_curriculum_content(content: str, min_word_count: int = 100) -> Dict[str, Any]`
Validates curriculum content for quality and completeness.

**Parameters**:
- `content`: Curriculum content to validate
- `min_word_count`: Minimum word count for content (default: 100)

**Returns**: Dictionary with validation results:
  - `valid`: Boolean indicating if content is valid
  - `errors`: List of error messages
  - `warnings`: List of warning messages
  - `metrics`: Dictionary with word_count, line_count, section_count

**Checks**: Word count, section structure, content balance, repetition detection

#### `extract_sections(content: str) -> Dict[str, str]`
Extracts sections from curriculum content.

**Parameters**:
- `content`: Curriculum content with markdown headers

**Returns**: Dictionary mapping section names to section content

#### `save_section(output_dir: str, entity_name: str, section_name: str, content: str) -> Path`
Saves individual curriculum section to file.

**Parameters**:
- `output_dir`: Output directory
- `entity_name`: Entity/domain name
- `section_name`: Section name
- `content`: Section content

**Returns**: Path to saved file

#### `save_complete_curriculum(output_dir: str, entity_name: str, sections: Dict[str, str]) -> Path`
Saves complete curriculum package.

**Parameters**:
- `output_dir`: Output directory
- `entity_name`: Entity/domain name
- `sections`: Dictionary of section names to content

**Returns**: Path to saved complete curriculum file

#### `process_research_file(client: OpenAI, research_file: str, output_dir: str) -> None`
Processes research file into complete curriculum.

**Parameters**:
- `client`: OpenAI client configured for OpenRouter
- `research_file`: Path to research JSON file
- `output_dir`: Output directory for curriculum files

**Behavior**: Loads research, generates sections, saves complete curriculum

## Module: `translation.py`

### Functions

#### `generate_translation_prompt(content: str, target_language: str) -> str`
Generates translation prompt using template with variables.

**Parameters**:
- `content`: Content to translate
- `target_language`: Target language name

**Returns**: Rendered translation prompt

**Uses**: `render_prompt()` with "translation" template

#### `split_content_into_chunks(content: str, max_chunk_size: int) -> List[str]`
Splits content into chunks for translation, preserving section boundaries.

**Parameters**:
- `content`: Content to split
- `max_chunk_size`: Maximum size of each chunk

**Returns**: List of content chunks

**Behavior**: Splits on markdown headers to preserve section structure

#### `translate_curriculum(client: OpenAI, content: str, target_language: str, max_chunk_size: int = 4000, model: Optional[str] = None) -> str`
Translates curriculum content to target language using OpenRouter.

**Parameters**:
- `client`: OpenAI client configured for OpenRouter
- `content`: Content to translate
- `target_language`: Target language for translation
- `max_chunk_size`: Maximum size of content chunks (default: 4000)
- `model`: Optional model override (defaults to `OPENROUTER_MODEL` env var)

**Returns**: Translated content as a single string

**Behavior**: Splits content into chunks, translates each chunk, combines results

#### `save_translation(output_dir: str, entity_name: str, language: str, content: str) -> Path`
Saves translated content to language-specific directory.

**Parameters**:
- `output_dir`: Base output directory
- `entity_name`: Entity/curriculum name
- `language`: Target language name
- `content`: Translated content

**Returns**: Path to saved translation file

**Output**: Saves to `{output_dir}/{language.lower()}/{entity_name}_curriculum_{language}_{timestamp}.md`

#### `process_translations(client: OpenAI, curriculum_dir: str, output_dir: str, target_languages: List[str]) -> tuple[int, int]`
Processes translations for multiple curricula and languages.

**Parameters**:
- `client`: OpenAI client configured for OpenRouter
- `curriculum_dir`: Directory containing curriculum files
- `output_dir`: Output directory for translations
- `target_languages`: List of target language names

**Returns**: Tuple of (success_count, failed_count)

**Behavior**: Finds all complete curricula, translates to each target language

## Cross-References

- [README.md](README.md) - Module overview and usage examples
- [../README.md](../README.md) - Source code overview
- [../../docs/pipeline.md](../../docs/pipeline.md) - Pipeline architecture
