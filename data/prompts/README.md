# Prompt Templates

Prompt templates for curriculum generation with variable substitution.

## Overview

This directory contains Markdown prompt templates used for generating research analyses, curricula, and translations.

## Templates

### `research_domain_analysis.md`
Template for domain analysis research prompts.

### `research_domain_curriculum.md`
Template for domain-specific curriculum generation.

### `research_entity.md`
Template for entity/audience research prompts.

### `curriculum_section.md`
Template for individual curriculum section generation.

### `translation.md`
Template for translation prompts with cultural adaptation.

## Variable Substitution

Templates use `{{variable_name}}` syntax for variable substitution.

Example:
```
Analyze the domain: {{domain_name}}
Using the script: {{language_script}}
```

## Usage

Templates are loaded and rendered by:
- `src/common/prompts.py::render_prompt()`
- `src/common/prompts.py::load_prompt_template()`

## Navigation

- [AGENTS.md](AGENTS.md) - Template format and variable reference
- [../README.md](../README.md) - Data directory overview
- [../../src/common/prompts.py](../../src/common/prompts.py) - Prompt utilities
