# Getting Started

Use this guide to install, run your first research session, and explore outputs.

## Prerequisites

See Environment Setup for full details: `docs/environment.md`.

## Quick Installation

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and set up project
git clone https://github.com/ActiveInferenceInstitute/Start.git
cd Start

# Install dependencies
uv sync --all-extras --dev

# Download language models
uv run python -m spacy download en_core_web_sm

# Configure API keys
cp .env.example .env
$EDITOR .env  # Add PERPLEXITY_API_KEY and OPENROUTER_API_KEY

# Verify installation
uv run pytest -q
uv run ruff check .
uv run black --check .
```

## First Research Session

```bash
# Ensure imports work
export PYTHONPATH=$(pwd):$PYTHONPATH

# Research a domain (creates comprehensive analysis)
uv run python learning/curriculum_creation/1_Research_Domain.py --domain biochemistry

# Research an entity (creates personalized profile)
uv run python learning/curriculum_creation/1_Research_Entity.py --entity karl_friston
```

## Generate Curriculum and Visualizations

```bash
# Generate curricula from research (40-60 hour programs)
uv run python learning/curriculum_creation/2_Write_Introduction.py

# Create visualizations (PNG charts + Mermaid diagrams)
uv run python learning/curriculum_creation/3_Introduction_Visualizations.py

# Translate to multiple languages (with cultural adaptation)
uv run python learning/curriculum_creation/4_Translate_Introductions.py --languages Spanish French
```

## Explore Generated Content

```bash
# Check generated research
ls data/domain_research/     # Domain analyses
ls data/audience_research/   # Entity profiles

# Check curriculum content
ls data/written_curriculums/     # Generated curricula
ls data/visualizations/          # Charts and diagrams
ls data/translated_curriculums/  # Multilingual content
```

## Common CLI Commands

```bash
# Research high-priority entities
python learning/curriculum_creation/1_Research_Entity.py --priority high

# Research specific domain with overwrite
python learning/curriculum_creation/1_Research_Domain.py --domain biochemistry --overwrite

# Filter by category and priority
python learning/curriculum_creation/1_Research_Domain.py --category life_sciences --priority high

# Generate multilingual content
python learning/curriculum_creation/4_Translate_Introductions.py --languages Spanish French German
```

