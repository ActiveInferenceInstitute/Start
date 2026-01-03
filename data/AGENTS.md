# Data Directory Technical Reference

## Overview

Technical documentation for data directory structure, file formats, and naming conventions.

## Directory Structure

### `audience_research/`
**Purpose**: Entity/audience research outputs

**File Format**: JSON
**Naming**: `{entity}_research_{timestamp}.json`
**Schema**: Contains entity name, description, research data, timestamp, processing time

### `config/`
**Purpose**: Configuration files

**File Formats**: YAML
**Files**:
- `domains.yaml`: Domain definitions with name, category, priority
- `entities.yaml`: Entity definitions with name, description, category, priority
- `languages.yaml`: Language configuration with target_languages and script_mappings

### `domain_research/`
**Purpose**: Domain research outputs

**File Formats**: JSON and Markdown
**Naming**: `{domain}_research_{timestamp}.json` and `.md`
**Schema**: Contains domain name, analysis, curriculum content, timestamp, processing time

### `prompts/`
**Purpose**: Prompt templates for curriculum generation

**File Format**: Markdown with variable substitution
**Variable Syntax**: `{{variable_name}}`
**Templates**:
- `research_domain_analysis.md`: Domain analysis template
- `research_domain_curriculum.md`: Curriculum generation template
- `research_entity.md`: Entity research template
- `curriculum_section.md`: Section generation template
- `translation.md`: Translation template

### `translated_curriculums/`
**Purpose**: Translated curriculum outputs

**Structure**: Organized by language subdirectories
**File Format**: Markdown
**Naming**: `{entity}_curriculum_{language}_{timestamp}.md`
**Languages**: Chinese, Spanish, Arabic, Hindi, French, Japanese, Russian, Swahili, Tagalog, etc.

### `visualizations/`
**Purpose**: Visualization outputs

**File Formats**: PNG, Mermaid (.mmd), JSON
**Types**:
- `{entity}_complexity_analysis.png`: Complexity analysis charts
- `{entity}_flow.mmd`: Learning flow diagrams
- `{entity}_learning_objectives.png`: Learning objectives charts
- `{entity}_section_breakdown.png`: Section breakdown charts
- `{entity}_technical_content.png`: Technical content charts
- `curriculum_metrics.json`: Metrics data
- `curriculum_metrics.png`: Metrics dashboard
- `curriculum_structure.mmd`: Overall structure diagram

### `written_curriculums/`
**Purpose**: Generated curriculum outputs

**Structure**: Organized by entity/domain subdirectories
**File Formats**: Markdown, JSON
**Naming**:
- Sections: `{section}_{timestamp}.md`
- Complete: `complete_curriculum_{timestamp}.md`
- Metadata: `{entity}_metadata_{timestamp}.json`

## Timestamp Format

All timestamped files use format: `YYYYMMDD_HHMMSS`

Example: `20250903_073951`

## Cross-References

- [README.md](README.md) - Data directory overview
- [../docs/data_outputs.md](../docs/data_outputs.md) - Data outputs documentation
- [../docs/pipeline.md](../docs/pipeline.md) - Pipeline architecture
