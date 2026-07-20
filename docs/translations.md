# Translations & Localization

How multilingual outputs are generated and organized.

## Overview

The system supports the target languages configured in `data/config/languages.yaml`, with script-aware quality checks and evidence-status metadata.

## Run Translation

From the repository root:

```bash
uv run start-curriculum --non-interactive --stages translations \
  --languages Spanish French Chinese --json
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

