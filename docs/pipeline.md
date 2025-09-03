# Active Inference Curriculum Creation Pipeline

## Overview

The START project provides a comprehensive, AI-powered pipeline for creating personalized Active Inference and Free Energy Principle curricula. The system uses real-time research via Perplexity API and advanced LLM-based content generation to produce professional-grade educational materials.

## Pipeline Stages

Stages
- Inputs: `data/config/entities.yaml`, `data/config/domains.yaml`, `data/config/languages.yaml`
- Research → Curriculum Generation → Visualization → Translation → Outputs

Links
- [Configuration Reference](./configuration.md)
- [Visualizations](./visualizations.md)
- [Translations](./translations.md)

### 1. **Research Phase** 🔍

- **Domain Research**: Analyze professional domains (biochemistry, AI, neuroscience, etc.)
- **Entity Research**: Create personalized profiles for target learners
- **Configuration-Driven**: Uses YAML configs for scalable, organized research

### 2. **Curriculum Generation** ✍️

- **Comprehensive Content**: 40-60 hour professional development programs
- **Personalized**: Tailored to specific domains and individual learning profiles
- **Structured Modules**: Multi-section educational frameworks with assessments

### 3. **Visualization Creation** 📊

- **Data Visualizations**: PNG charts showing curriculum metrics and analysis
- **Process Diagrams**: Mermaid diagrams for curriculum structure and flow
- **Interactive Elements**: Visual learning aids and conceptual frameworks

### 4. **Multilingual Translation** 🌍

- **Cultural Adaptation**: Full localization beyond literal translation
- **Professional Quality**: Native-speaker level fluency with technical accuracy
- **Multiple Languages**: Support for 9+ target languages with script mapping

## Script Entrypoints

### Core Curriculum Creation Scripts
```bash
# Configuration-based research (NEW APPROACH)
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
├── entities.yaml         # Target learner profiles (8 entities)
├── domains.yaml          # Professional domains (16 domains) 
└── languages.yaml        # Translation targets (9+ languages)
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
├── research_domain_curriculum.md   # 9-section curriculum generation
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

### Advanced Command-Line Interface
```bash
# Filter by priority and category
python 1_Research_Domain.py --priority high --category life_sciences

# Process specific targets
python 1_Research_Entity.py --entity karl_friston --overwrite

# Multilingual output with specific languages
python 4_Translate_Introductions.py --languages Spanish French German
```

### Comprehensive Content Generation
- **Domain Analysis**: 3,000-5,000 word professional landscape analysis
- **Curriculum Content**: 40-60 hour structured learning programs
- **Personalization**: 5,000-8,000 word tailored learning strategies
- **Section Modules**: 3-5 hour comprehensive learning units

## API Integration

### Perplexity API (Research)
- **Real-time Research**: Current online information and analysis
- **Professional Insights**: Industry trends, challenges, opportunities
- **Comprehensive Analysis**: Multi-perspective domain understanding

### OpenRouter API (Content Generation)
- **Advanced LLMs**: High-quality curriculum and translation generation
- **Structured Output**: Consistent, professional educational content
- **Multilingual Capability**: Native-quality translations with cultural adaptation

## Quality Assurance

### Content Standards
- **Professional Grade**: University course and corporate training quality
- **Evidence-Based**: Real research and current industry insights
- **Comprehensive Coverage**: Multi-modal learning approaches
- **Assessment Integrated**: Built-in evaluation and progress tracking

### Technical Standards
- **Modular Architecture**: Clean, maintainable, testable code
- **Error Handling**: Robust failure recovery and logging
- **Performance Optimized**: Efficient API usage and data processing
- **Standards Compliant**: Following Python best practices and project conventions

### Cross-References
- Environment setup and CI workflow: `docs/environment.md`
- Testing policy and markers: `docs/TESTING.md`
- Clone management for optional resources: `docs/clones.md`
