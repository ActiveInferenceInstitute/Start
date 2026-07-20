# Data Directory

Generated content, configuration files, and research outputs.

`domain_research/Synthetic_FEP-ActInf.md` is explicitly synthetic offline
foundation material and must not be cited as live evidence. The current
non-destructive inventory is `artifact-manifests/current.json`; use
`uv run python -m scripts.audit_artifacts --json` and
`uv run start-validate-outputs --check` to regenerate structural audits before
curation. Use `uv run start-regenerate-offline` for deterministic synthetic
fixtures; it never contacts a provider.

## Overview

This directory contains all generated content, configuration files, and research outputs from the START curriculum generation pipeline.

## Directory Structure

### `audience_research/`
Entity/audience research outputs in JSON format.

### `config/`
Configuration files in YAML format:
- `domains.yaml`: Domain definitions
- `entities.yaml`: Entity/audience definitions
- `languages.yaml`: Language configuration

### `domain_research/`
Domain research outputs in JSON and Markdown formats.

### `prompts/`
Prompt templates for curriculum generation:
- `research_domain_analysis.md`: Domain analysis prompts
- `research_domain_curriculum.md`: Curriculum generation prompts
- `research_entity.md`: Entity research prompts
- `curriculum_section.md`: Section generation prompts
- `translation.md`: Translation prompts

### `translated_curriculums/`
Translated curriculum outputs organized by language.

### `visualizations/`
Visualization outputs:
- `charts/` PNG charts and graphs
- `diagrams/` stable-ID Mermaid diagrams
- `metrics/` CSV and JSON metric files
- `visualization_manifest.json` input/output hashes and derived-evidence status

### `written_curriculums/`
Generated curriculum outputs organized by entity/domain.

## File Naming Conventions

- Research files: `{name}_research_{timestamp}.json` or `.md`
- Curriculum files: `{section}_{timestamp}.md` or `complete_curriculum_{timestamp}.md`
- Translation files: `{entity}_curriculum_{language}_{timestamp}.md`
- Visualization files:
  - Entity-specific: `diagrams/{stable-item-id}_flow.mmd`
  - Global aggregate: `metrics/curriculum_metrics.{csv,json}`, `charts/curriculum_metrics.png`, and `diagrams/curriculum_structure.mmd`

## Navigation

- [AGENTS.md](AGENTS.md) - Data structure and file format reference
- [../docs/data_outputs.md](../docs/data_outputs.md) - Data outputs documentation
- [../docs/pipeline.md](../docs/pipeline.md) - Pipeline architecture
