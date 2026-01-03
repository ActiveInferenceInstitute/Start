# Curriculum Creation Scripts Technical Reference

## Overview

Technical documentation for curriculum creation scripts and their functions.

## Scripts

### `1_Research_Domain.py`
Domain research script using Perplexity API.

**Functions**:
- `load_domains_config() -> Dict[str, Any]`: Load domains configuration
- `get_domain_files(domain_dir: Path) -> List[Path]`: Get domain files to process
- `main()`: Main execution function

**Input**: Domain files from `Languages/Inputs_and_Outputs/Domain/`
**Output**: Research reports in `data/domain_research/`

### `1_Research_Entity.py`
Entity/audience research script using Perplexity API.

**Functions**:
- `load_entities_config() -> Dict[str, Any]`: Load entities configuration
- `get_entity_files(entity_dir: Path) -> List[Path]`: Get entity files to process
- `main()`: Main execution function

**Input**: Entity files from `Languages/Inputs_and_Outputs/Entity/`
**Output**: Research reports in `data/audience_research/`

### `2_Write_Introduction.py`
Curriculum generation script using OpenRouter API.

**Functions**:
- `get_research_files(research_dir: Path, pattern: str) -> List[Path]`: Get research files
- `process_research_directory(research_dir: Path, output_dir: Path, client) -> None`: Process directory
- `main()`: Main execution function

**Input**: Research files from `data/domain_research/` and `data/audience_research/`
**Output**: Curricula in `data/written_curriculums/`

### `3_Introduction_Visualizations.py`
Visualization generation script.

**Functions**:
- `extract_curriculum_metadata()`: Extract metadata from curricula
- `create_curriculum_metrics_chart()`: Generate metrics charts
- `create_curriculum_flow_mermaid()`: Create flow diagrams
- `create_curriculum_structure_mermaid()`: Create structure diagrams
- `main()`: Main execution function

**Input**: Curricula from `data/written_curriculums/`
**Output**: Visualizations in `data/visualizations/`

### `4_Translate_Introductions.py`
Translation script using OpenRouter API.

**Functions**:
- `validate_languages()`: Validate requested languages
- `main()`: Main execution function

**Input**: Curricula from `data/written_curriculums/`
**Output**: Translations in `data/translated_curriculums/`

### `generate_curriculum_gui.py`
GUI-based curriculum generator.

**Functions**: GUI interface for curriculum generation

### `generate_custom_curriculum.py`
Custom curriculum generator with interactive mode.

**Functions**: Interactive curriculum generation workflow

## Cross-References

- [README.md](README.md) - Script overview and usage
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Usage guide
- [INTERACTIVE_GUIDE.md](INTERACTIVE_GUIDE.md) - Interactive guide
