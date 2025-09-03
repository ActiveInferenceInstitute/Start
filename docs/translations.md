# Translations & Localization

How multilingual outputs are generated and organized.

## Overview

The system supports 9+ target languages with cultural adaptation, driven by `data/config/languages.yaml` and the translation prompt template.

## Run Translation

From `learning/curriculum_creation/`:

```bash
uv run python 4_Translate_Introductions.py --languages Spanish French Chinese
```

If `--languages` is omitted, languages are read from `data/config/languages.yaml`.

## Outputs

Artifacts are organized under `data/translated_curriculums/` by language:

```text
data/translated_curriculums/
├── spanish/
├── french/
├── chinese/
└── tagalog/
```

Each language folder mirrors the source curriculum file structure and filenames.

## Configuration

Languages are defined in:

```text
data/config/languages.yaml
```

Add or remove language keys as needed. The translation script validates requested languages against this file.

## Tips

- Ensure source curricula exist under `data/written_curriculums/` before translating.
- Large translation sets can be slow; specify a subset with `--languages` to iterate quickly.

## Prompt Template

Translation guidance lives in:

```text
data/prompts/translation.md
```

This template ensures tone, terminology, and cultural appropriateness while preserving technical accuracy.



