# Active Inference Curriculum Creation Scripts

This directory contains a comprehensive suite of Python scripts for creating personalized Active Inference curricula. The scripts follow a modular, test-driven development approach and implement the full curriculum generation pipeline from research to translation.

## Overview

The curriculum creation process follows these stages:

1. **Research** (Scripts 1_*): Analyze domains and target audiences
2. **Content Generation** (Script 2_*): Create tailored curriculum content
3. **Visualization** (Script 3_*): Generate charts and diagrams
4. **Translation** (Script 4_*): Translate to multiple languages

## Scripts

### 1_Research_Domain.py
**Purpose**: Analyzes domain characteristics to create domain-specific Active Inference curricula.

**Key Features**:
- Processes domain files using online research via Perplexity API
- Generates comprehensive domain analysis reports
- Creates tailored curriculum content based on professional backgrounds
- Saves structured JSON and Markdown reports to `data/domain_research/`

**Usage**:
```bash
python 1_Research_Domain.py
```

**Input**: Domain files from `Languages/Inputs_and_Outputs/Domain/Synthetic_*.md`
**Output**: Research reports in `data/domain_research/`

**Functions**:
- `get_domain_files(domain_dir)`: Finds domain files to process
- `main()`: Orchestrates the complete domain analysis workflow

### 1_Research_Entity.py
**Purpose**: Researches target audience characteristics for personalized curriculum creation.

**Key Features**:
- Analyzes entity/audience files to understand learning needs
- Generates personalized curriculum recommendations
- Creates audience-specific research reports
- Saves structured reports to `data/audience_research/`

**Usage**:
```bash
python 1_Research_Entity.py
```

**Input**: Entity files from `Languages/Inputs_and_Outputs/Entity/*.py`
**Output**: Audience research reports in `data/audience_research/`

**Functions**:
- `get_entity_files(entity_dir)`: Finds entity files to process
- `main()`: Orchestrates the complete audience analysis workflow

### 2_Write_Introduction.py
**Purpose**: Converts research reports into comprehensive Active Inference curricula.

**Key Features**:
- Processes both domain and audience research files
- Generates modular curriculum sections using advanced prompts
- Creates complete curriculum packages with metadata
- Uses OpenRouter API for high-quality content generation
- Saves curricula to `data/written_curriculums/`

**Usage**:
```bash
python 2_Write_Introduction.py
```

**Input**: Research files from `data/domain_research/` and `data/audience_research/`
**Output**: Complete curricula in `data/written_curriculums/`

**Functions**:
- `get_research_files(research_dir)`: Finds research files to process
- `process_research_directory()`: Processes all files in a research directory
- `main()`: Orchestrates the complete curriculum generation workflow

### 3_Introduction_Visualizations.py
**Purpose**: Generates PNG charts and Mermaid diagrams for curriculum visualization.

**Key Features**:
- Creates comprehensive curriculum metrics and analysis charts
- Generates PNG charts using matplotlib and seaborn
- Creates Mermaid diagrams for curriculum structure and learning flow
- Analyzes content complexity, learning objectives, and technical content
- Saves visualizations to `data/visualizations/`

**Usage**:
```bash
python 3_Introduction_Visualizations.py [--input INPUT_DIR] [--output OUTPUT_DIR]
```

**Options**:
- `--input`: Custom input directory (default: `data/written_curriculums`)
- `--output`: Custom output directory (default: `data/visualizations`)

**Outputs**:
- `curriculum_metrics.png`: Comprehensive metrics dashboard
- `curriculum_structure.mmd`: Overall curriculum structure diagram
- `{entity}_flow.mmd`: Individual learning flow diagrams
- `curriculum_metrics.json`: Detailed metrics data

**Functions**:
- `extract_curriculum_metadata()`: Analyzes curriculum content for metrics
- `create_curriculum_metrics_chart()`: Generates PNG analytics charts
- `create_curriculum_flow_mermaid()`: Creates learning progression diagrams
- `create_curriculum_structure_mermaid()`: Creates overview structure diagrams

### 4_Translate_Introductions.py
**Purpose**: Translates curricula into multiple configured languages.

**Key Features**:
- Loads target languages from YAML configuration
- Validates language requests against available options
- Uses OpenRouter API for high-quality translation
- Applies proper script mappings and cultural adaptations
- Saves translated curricula to `data/translated_curriculums/`

**Usage**:
```bash
python 4_Translate_Introductions.py [--input INPUT_DIR] [--output OUTPUT_DIR] [--languages LANG1 LANG2 ...]
```

**Options**:
- `--input`: Custom input directory (default: `data/written_curriculums`)
- `--output`: Custom output directory (default: `data/translated_curriculums`)
- `--languages`: Specific languages to translate (default: all configured languages)

**Functions**:
- `validate_languages()`: Validates requested languages against configuration
- `main()`: Orchestrates the complete translation workflow

## Data Structure

All scripts follow a consistent data organization pattern:

```
data/
├── audience_research/          # Entity/audience research reports
│   └── {entity}_research_{timestamp}.json
├── domain_research/           # Domain analysis reports
│   ├── {domain}_research_{timestamp}.json
│   └── {domain}_research_{timestamp}.md
├── written_curriculums/       # Generated curricula
│   └── {entity}/
│       ├── {section}_{timestamp}.md
│       └── complete_curriculum_{timestamp}.md
├── translated_curriculums/    # Translated curricula
│   └── {language}/
│       └── {entity}_curriculum_{language}_{timestamp}.md
└── visualizations/           # Charts and diagrams
    ├── curriculum_metrics.png
    ├── curriculum_structure.mmd
    └── {entity}_flow.mmd
```

## Configuration

### Language Configuration
Configure target languages in `data/config/languages.yaml`:

```yaml
target_languages:
  - Chinese
  - Spanish
  - Arabic
  - Hindi
  - French
  # ... more languages

script_mappings:
  Arabic: "Modern Standard Arabic"
  Chinese: "Simplified Chinese"
  # ... more mappings
```

### Prompt Templates
Customize prompts in `data/prompts/`:
- `research_domain_analysis.md`: Domain analysis prompts
- `research_domain_curriculum.md`: Domain curriculum generation
- `research_entity.md`: Entity research prompts
- `curriculum_section.md`: Section generation prompts
- `translation.md`: Translation prompts

## Dependencies

### Core Dependencies
- `openai`: API client for Perplexity and OpenRouter
- `pathlib`: Path handling
- `pydantic`: Data validation
- `pyyaml`: Configuration loading

### Visualization Dependencies
- `matplotlib`: Chart generation
- `seaborn`: Statistical visualizations
- `pandas`: Data manipulation

### Development Dependencies
- `pytest`: Testing framework
- `black`: Code formatting
- `ruff`: Linting

## Environment Setup

1. Install dependencies:
```bash
uv sync --all-extras --dev
```

2. Set up environment variables:
```bash
export PERPLEXITY_API_KEY="your-perplexity-key"
export OPENROUTER_API_KEY="your-openrouter-key"
```

3. Configure models (optional):
```bash
export PERPLEXITY_MODEL="llama-3.1-sonar-small-128k-online"
export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
```

## Usage Examples

### Complete Pipeline
Run all scripts in sequence:

```bash
# 1. Research domains and entities
python 1_Research_Domain.py
python 1_Research_Entity.py

# 2. Generate curricula
python 2_Write_Introduction.py

# 3. Create visualizations
python 3_Introduction_Visualizations.py

# 4. Translate to target languages
python 4_Translate_Introductions.py
```

### Custom Visualization
Generate visualizations for specific input:

```bash
python 3_Introduction_Visualizations.py --input /path/to/curricula --output /path/to/viz
```

### Selective Translation
Translate only to specific languages:

```bash
python 4_Translate_Introductions.py --languages Spanish French German
```

## Error Handling & Quality Assurance

All scripts implement comprehensive error handling and quality assurance:

### Robust Error Handling
- **Graceful degradation**: Continue processing other items if one fails
- **Detailed logging**: Comprehensive logs for debugging and monitoring with progress tracking
- **Input validation**: Extensive validation with clear error messages and helpful suggestions
- **API resilience**: Retry mechanisms with exponential backoff for transient failures
- **Keyboard interrupt handling**: Clean shutdown on user interruption

### Content Validation
- **Template validation**: Prompt templates are validated for structure and completeness
- **Configuration validation**: YAML/Markdown config files are validated on load
- **Content quality checks**: Generated curriculum content is validated for:
  - Minimum word count requirements
  - Proper section structure
  - Content uniqueness (repetition detection)
  - Balanced section lengths

### Enhanced User Experience
- **Progress tracking**: Real-time progress indicators (e.g., "Processing 3/10")
- **Helpful error messages**: Clear guidance on resolving configuration and setup issues
- **Validation feedback**: Warnings for content quality issues without blocking processing
- **Resource management**: Automatic cleanup of failed operations

## Testing

The scripts include comprehensive tests:

- **Unit tests**: Test individual functions
- **Integration tests**: Test script workflows
- **Mock testing**: Test without external API calls
- **Documentation tests**: Verify code documentation standards

Run tests:
```bash
python tests/test_curriculum_scripts_integration.py
```

## Logging

All scripts use structured logging:

```python
logger = common_setup_logging()
logger.info("Starting process")
logger.error("Process failed", extra={"error": str(e)})
```

Logs include:
- Timestamps and levels
- Process progress and statistics
- Error details and stack traces
- Performance metrics

## Best Practices

### Code Quality
- **Type hints**: Full type annotations for better IDE support
- **Docstrings**: Comprehensive documentation for all functions
- **Modular design**: Separation of concerns and reusable components
- **Error handling**: Comprehensive exception handling and logging

### Data Management
- **Consistent naming**: Standardized file naming conventions
- **Structured formats**: JSON for data, Markdown for readable content
- **Timestamping**: All outputs include generation timestamps
- **Version control**: Track changes and maintain backward compatibility

### Performance
- **Batch processing**: Process multiple items efficiently
- **Rate limiting**: Respect API rate limits
- **Caching**: Avoid redundant API calls where possible
- **Progress tracking**: Clear progress indicators for long operations

## Troubleshooting

### Common Issues

**API Key Errors**:
- Ensure environment variables are set correctly
- Verify API keys are valid and have appropriate permissions

**File Not Found Errors**:
- Check input directory structure matches expected layout
- Ensure required files exist before processing

**Memory Issues**:
- Process large datasets in batches
- Clear intermediate data when not needed

**Network Errors**:
- Implement retry logic for transient failures
- Check network connectivity and API endpoint availability

### Debug Mode
Enable verbose logging by setting log level:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Enhanced Troubleshooting

**Configuration Errors**:
- Scripts now provide detailed guidance when configuration files are missing or invalid
- Clear error messages explain exactly what's expected in configuration files
- Validation warnings help identify potential issues before processing

**API Connection Issues**:
- Improved API key validation with format checking
- Better error messages for authentication failures
- Retry logic with exponential backoff for transient network issues
- Connection timeout handling with informative error messages

**Content Quality Issues**:
- Content validation warnings for short or repetitive generated content
- Section structure validation to ensure proper curriculum organization
- Template variable validation to catch missing prompt parameters
- File size and format checking before processing

**Processing Failures**:
- Individual item failures don't stop entire batch processing
- Clear progress indicators show exactly which items succeeded/failed
- Detailed error logging with full stack traces in debug mode
- Graceful handling of keyboard interrupts

## Contributing

### Code Style
- Follow PEP 8 style guidelines
- Use `black` for code formatting
- Use `ruff` for linting
- Include comprehensive docstrings

### Testing
- Write tests for new functionality
- Follow TDD practices
- Include both unit and integration tests
- Test error conditions and edge cases

### Documentation
- Update this README for any changes
- Include docstrings for all public functions
- Add usage examples for complex features
- Document configuration options

## License

This project follows the repository's LICENSE terms.
