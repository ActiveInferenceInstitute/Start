---
name: instituteos-start
version: "1.0.0"
category: research
description: >
  START — Scalable, Tailored Active-inference Research & Training. An AI-powered
  system for creating personalized Active Inference and FEP curricula. Pipeline:
  research (Perplexity) → curriculum generation (OpenRouter) → visualization →
  translation.
tags:
  - active-inference
  - curriculum-generation
  - perplexity
  - openrouter
  - fep
---

# START — Active Inference Curriculum Generator

## Overview

START generates professional-grade Active Inference curricula using:
- **Perplexity API** for real-time domain/entity research
- **OpenRouter API** for LLM-based content generation and translation
- **Matplotlib/Seaborn** for visualization
- **Multilingual output** (11+ languages with script mapping)

## Quick Start

```bash
git clone https://github.com/ActiveInferenceInstitute/Start.git
cd Start

# Install dependencies
uv sync --all-extras --dev

# Run tests
uv run pytest -q

# Run the curriculum generation pipeline (interactive)
uv run python learning/curriculum_creation/generate_custom_curriculum.py

# Or use the browser GUI
uv run python learning/curriculum_creation/generate_curriculum_gui.py

# Or run individual pipeline stages:
uv run python learning/curriculum_creation/1_Research_Domain.py
uv run python learning/curriculum_creation/1_Research_Entity.py
uv run python learning/curriculum_creation/2_Write_Introduction.py
uv run python learning/curriculum_creation/3_Introduction_Visualizations.py
uv run python learning/curriculum_creation/4_Translate_Introductions.py
```

## Architecture

```
src/common/    — Shared utilities (io, paths, config, prompts, logging)
src/config/    — Language configuration
src/perplexity/— LLM API clients (Perplexity + OpenRouter), domain/entity/curriculum/translation
src/repos/     — Repository cloning for Active Inference ecosystem
src/system/    — Environment setup, dependency checking, reporting
src/terminal/  — Matrix-themed CLI (animations, colors, menu)
src/visualization/ — Curriculum metrics visualization
```

Pipeline scripts under `learning/curriculum_creation/` are **thin orchestrators**
that import from `src/` modules.

## Configuration

- `data/config/domains.yaml` — Domain definitions (keywords, categories, priorities)
- `data/config/entities.yaml` — Entity/audience profiles
- `data/config/languages.yaml` — Translation targets and script mappings
- `data/prompts/*.md` — Prompt templates with `{{variable}}` substitution

## Key Facts

- **Test suite** — all tests use real local protocols and temporary data
- **Provider tests** — local HTTP completion servers exercise the production client
- **Standalone** — not dependent on the template infrastructure
- **Path structure**: outputs under `data/`
- **Documentation**: 23+ docs pages, AGENTS.md per subpackage
