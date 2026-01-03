# Prompt Templates Technical Reference

## Overview

Technical documentation for prompt template format and variable substitution.

## Template Format

### File Format
- **Format**: Markdown (.md)
- **Variable Syntax**: `{{variable_name}}`
- **Encoding**: UTF-8

### Variable Substitution

Variables are substituted using `{{variable_name}}` syntax:
- Variables are case-sensitive
- Missing variables return empty string (non-strict) or raise error (strict mode)
- None values are converted to empty strings

## Template Files

### `research_domain_analysis.md`
**Purpose**: Domain analysis research prompts

**Common Variables**:
- `domain_name`: Name of domain to analyze
- `fep_content`: Free Energy Principle content

### `research_domain_curriculum.md`
**Purpose**: Domain-specific curriculum generation

**Common Variables**:
- `domain_name`: Domain name
- `domain_analysis`: Domain analysis content
- `fep_content`: Free Energy Principle content

### `research_entity.md`
**Purpose**: Entity/audience research prompts

**Common Variables**:
- `entity_name`: Entity/audience name
- `entity_description`: Entity description
- `fep_content`: Free Energy Principle content

### `curriculum_section.md`
**Purpose**: Individual curriculum section generation

**Common Variables**:
- `section_name`: Section name
- `entity_name`: Entity/domain name
- `research_content`: Research content

### `translation.md`
**Purpose**: Translation prompts with cultural adaptation

**Common Variables**:
- `content`: Content to translate
- `target_language`: Target language name
- `language_script`: Script/writing system name

## Template Loading

Templates are loaded from `data/prompts/` directory using:
- `src/common/prompts.py::load_prompt_template(name)`
- `src/common/prompts.py::render_prompt(name, variables, strict)`

## Cross-References

- [README.md](README.md) - Template overview
- [../../src/common/prompts.py](../../src/common/prompts.py) - Prompt loading and rendering functions
