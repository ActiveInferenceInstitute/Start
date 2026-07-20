# Active Inference Curriculum Creation Pipeline

## Overview

The START project provides a pipeline for creating personalized Active Inference and Free Energy Principle curricula. Live provider calls are optional; offline fixtures and synthetic foundation material are explicitly labeled and never treated as live evidence.

## Pipeline Stages

Stages
- Inputs: `data/config/entities.yaml`, `data/config/domains.yaml`, `data/config/languages.yaml`
- `acquire` → `prepare` → `process` → `parse` → `render`

Each run has a stable run ID, a filesystem checkpoint directory, and an
atomic `manifest.json`. Required-stage failures make `PipelineResult.ok` false;
optional-stage failures remain visible in structured stage results.

Links
- [Configuration Reference](./configuration.md)
- [Visualizations](./visualizations.md)
- [Translations](./translations.md)

### 1. **Acquire** 🔍

- **Domain Research**: Analyze professional domains (biochemistry, AI, neuroscience, etc.)
- **Entity Research**: Create personalized profiles for target learners
- **Configuration-Driven**: Uses YAML configs for scalable, organized research

### 2. **Prepare and Process** ✍️

- **Comprehensive Content**: Prompt-defined professional development programs with manifest-backed quality status
- **Personalized**: Tailored to specific domains and individual learning profiles
- **Structured Modules**: Multi-section educational frameworks with assessments

### 3. **Parse and Render** 📊

- **Data Visualizations**: PNG charts showing curriculum metrics and analysis
- **Process Diagrams**: Mermaid diagrams for curriculum structure and flow
- **Visualization manifest**: Input/output hashes and the derived-evidence
  boundary for every canonical render bundle
- **Interactive Elements**: Visual learning aids and conceptual frameworks

### 4. **Multilingual Translation** 🌍

- **Cultural Adaptation**: Full localization beyond literal translation
- **Review Required**: Translation structure and script checks are automated; fluency and technical accuracy require human review
- **Multiple Languages**: Support for the configured target languages with script mapping

## Script Entrypoints

### Staged Entrypoints
```bash
# Numbered files remain importable staged entrypoints; use the canonical runner.
learning/curriculum_creation/1_Research_Domain.py    # Domain analysis
learning/curriculum_creation/1_Research_Entity.py    # Audience profiling  
learning/curriculum_creation/2_Write_Introduction.py # Curriculum generation
learning/curriculum_creation/3_Introduction_Visualizations.py # Charts & diagrams
learning/curriculum_creation/4_Translate_Introductions.py     # Multilingual output
```

### Supporting Infrastructure
```bash
src/perplexity/           # Perplexity API integration
src/common/               # Shared utilities (paths, config, prompts)
src/config/               # Configuration management
src/visualization/        # Visualization generation
```

## Data Architecture

### Input Configuration

```text
data/config/
├── entities.yaml         # Target learner profiles
├── domains.yaml          # Professional domains
└── languages.yaml        # Translation targets and scripts
```

### Research Outputs

```text
data/
├── audience_research/     # Personalized learner analysis
├── domain_research/       # Professional domain analysis
├── written_curriculums/   # Generated curriculum content
├── translated_curriculums/ # Multilingual versions
└── visualizations/        # Charts and diagrams
```

### Template System

```text
data/prompts/
├── research_domain_analysis.md     # 6-section domain framework
├── research_domain_curriculum.md   # Prompt-defined curriculum generation
├── research_entity.md              # 6-section personalization
├── curriculum_section.md           # Comprehensive module creation
└── translation.md                  # 7-section multilingual framework
```

## Enhanced Features

### Configuration-Driven Research
- **YAML-Based Control**: All research targets defined in configuration files
- **Priority Filtering**: Process high/medium/low priority items
- **Category Filtering**: Focus on specific domain categories
- **Overwrite Control**: Skip existing by default, force overwrite with flags
- **Release controls**: The canonical runner supports `--dry-run`,
  `--estimate-cost`, `--run-id`, `--resume`, `--offline`, `--budget-usd`, and
  machine-readable `--json` summaries.
- **Evidence boundaries**: Synthetic foundational material is labeled as
  synthetic; provider, model, prompt, source hashes, usage, and quality status
  accompany generated outputs.

### Advanced Command-Line Interface
```bash
# Filter by priority and category
uv run start-curriculum --non-interactive --stages domain-research \
  --domain-priority high --domain-category life_sciences --json

# Process specific targets
uv run start-curriculum --non-interactive --stages entity-research \
  --entities karl_friston --overwrite --json

# Multilingual output with specific languages
uv run start-curriculum --non-interactive --stages translations \
  --languages Spanish French German --json
```

### Comprehensive Content Generation
- **Domain Analysis**: Prompt-targeted professional landscape analysis, checked for structure and provenance
- **Curriculum Content**: Structured learning programs whose actual output is recorded and validated
- **Personalization**: Prompt-targeted tailored learning strategies, checked before publication
- **Section Modules**: Prompt-defined learning units; duration is an estimate requiring review

## API Integration

### Perplexity API (Research)
- **Live Research**: Current online information and analysis when a live provider run is explicitly enabled
- **Professional Insights**: Industry trends, challenges, opportunities
- **Comprehensive Analysis**: Multi-perspective domain understanding

### OpenRouter API (Content Generation)
- **Advanced LLMs**: High-quality curriculum and translation generation
- **Structured Output**: Consistent, professional educational content
- **Multilingual Capability**: Configured translation workflows with structural, parity, and script checks; cultural and technical review remains required

## Quality Assurance

### Content Standards
- **Reviewable structure**: Required sections, lengths, citations, and provenance are checked before publication
- **Evidence-labeled**: Live research, source material, synthetic foundations, offline fixtures, and derived visuals are never silently conflated
- **Human validation**: Technical accuracy, pedagogical suitability, language fluency, and learning outcomes remain review responsibilities
- **Explicit limits**: Generated content is not independently fact-checked or evidence of learning outcomes by the pipeline alone

### Technical Standards
- **Modular Architecture**: Clean, maintainable, testable code
- **Error Handling**: Robust failure recovery and logging
- **Performance Optimized**: Efficient API usage and data processing
- **Standards Compliant**: Following Python best practices and project conventions

## Operational commands

```bash
# Plan without contacting providers
uv run start-curriculum --non-interactive --dry-run --run-id plan-001 --json

# Validate generated text and JSON contracts without modifying data
uv run start-validate-outputs --check

# Regenerate a deterministic, explicitly synthetic fixture
uv run start-regenerate-offline --output-dir /tmp/start-fixtures --run-id fixture-001 --json

# Inspect or conservatively prune filesystem-backed run history
uv run start-run-history --root data/written_curriculums/.runs --json
uv run start-run-history --root data/written_curriculums/.runs --keep 10 --prune --json
```

### Cross-References
- Environment setup and CI workflow: `docs/environment.md`
- Testing policy and markers: `docs/TESTING.md`
- Clone management for optional resources: `docs/clones.md`
