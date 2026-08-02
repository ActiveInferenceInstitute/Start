# Getting Started

Use this guide to install, run your first research session, and explore outputs.

## Prerequisites

See Environment Setup for full details: `environment.md`.

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
# Plan a release-aware run without contacting providers
uv run start-curriculum --non-interactive --domains biochemistry \
  --entities karl_friston --languages Spanish --dry-run --run-id getting-started --json

# For live research, remove --dry-run only after reviewing the estimate and budget.
```

## Generate Curriculum and Visualizations

```bash
# Generate curricula from research through the canonical runner
uv run start-curriculum --non-interactive --stages curriculum --json

# Create visualizations through the canonical render stage
uv run start-curriculum --non-interactive --stages visualizations --json

# Translate to multiple languages through the canonical parse stage
uv run start-curriculum --non-interactive --stages translations \
  --languages Spanish French --json
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
uv run start-curriculum --non-interactive --stages entity-research \
  --entity-priority high --json

# Research specific domain with overwrite
uv run start-curriculum --non-interactive --stages domain-research \
  --domains biochemistry --overwrite --json

# Filter by category and priority
uv run start-curriculum --non-interactive --stages domain-research \
  --domain-category life_sciences --domain-priority high --json

# Generate multilingual content
uv run start-curriculum --non-interactive --stages translations \
  --languages Spanish French German --json
```
