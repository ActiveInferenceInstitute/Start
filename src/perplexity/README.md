# LLM API Integrations

Integration modules for Large Language Model APIs used in the START project.

## Overview

This module provides access to two different LLM providers, each optimized for different tasks:

- **Perplexity API**: Real-time research and domain analysis with online information access
- **OpenRouter API**: Content generation, curriculum creation, and translation

## Modules

### `clients.py`
Client builders for both API providers:
- `PerplexityConfig`: Configuration dataclass for Perplexity
- `OpenRouterConfig`: Configuration dataclass for OpenRouter
- `build_perplexity_client()`: Creates Perplexity API client
- `build_openrouter_client()`: Creates OpenRouter API client

### `domain.py`
Domain research using Perplexity:
- `chat()`: Send research requests to Perplexity
- `analyze_domain()`: Comprehensive domain analysis workflow
- `DomainResult`: Result dataclass with analysis and curriculum content

### `entity.py`
Entity/audience research using Perplexity:
- `extract_entity_description()`: Extract description from entity data
- `chat()`: Send research requests to Perplexity
- `research_target_audience()`: Complete audience research workflow
- `ResearchResult`: Result dataclass with research data

### `curriculum.py`
Curriculum generation using OpenRouter:
- `chat()`: Send content generation requests to OpenRouter
- `validate_curriculum_content()`: Validate generated content quality
- `extract_sections()`: Extract sections from curriculum content
- `save_section()`: Save individual curriculum sections
- `save_complete_curriculum()`: Save complete curriculum package
- `process_research_file()`: Process research files into curricula

### `translation.py`
Translation services using OpenRouter:
- `generate_translation_prompt()`: Generate translation prompts
- `split_content_into_chunks()`: Split content for translation
- `translate_curriculum()`: Translate curriculum content
- `save_translation()`: Save translated content
- `process_translations()`: Batch translation processing

## Usage Examples

```python
from src.perplexity.clients import build_perplexity_client, build_openrouter_client
from src.perplexity.domain import analyze_domain
from src.perplexity.entity import research_target_audience
from src.perplexity.curriculum import process_research_file
from src.perplexity.translation import translate_curriculum, save_translation

# Build clients
perplexity_client = build_perplexity_client()
openrouter_client = build_openrouter_client()

# Research domain
domain_result = analyze_domain(
    perplexity_client,
    domain_input="biochemistry",
    fep_actinf_input="path/to/fep_content.md"
)

# Research entity
entity_result = research_target_audience(
    perplexity_client,
    entity_input="karl_friston",
    fep_actinf_input="path/to/fep_content.md",
    output_dir="data/audience_research"
)

# Generate curriculum
process_research_file(
    openrouter_client,
    research_file="data/domain_research/biochemistry_research.json",
    output_dir="data/written_curriculums"
)

# Translate curriculum
translated = translate_curriculum(
    openrouter_client,
    content=curriculum_content,
    target_language="Spanish"
)
save_translation("data/translated_curriculums", "entity_name", "Spanish", translated)
```

## Environment Variables

- `PERPLEXITY_API_KEY`: API key for Perplexity (required)
- `PERPLEXITY_MODEL`: Model name (default: "llama-3.1-sonar-small-128k-online")
- `OPENROUTER_API_KEY`: API key for OpenRouter (required)
- `OPENROUTER_MODEL`: Model name (default: "anthropic/claude-3.5-sonnet")

## Navigation

- [AGENTS.md](AGENTS.md) - Complete function reference
- [../README.md](../README.md) - Source code overview
- [../../docs/pipeline.md](../../docs/pipeline.md) - Pipeline architecture
