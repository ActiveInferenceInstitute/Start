# Data & Outputs

This page summarizes where the system writes artifacts and what each directory contains.

## Research Artifacts

```text
data/
├── audience_research/       # Personalized learner/entity profiles (JSON/MD)
├── domain_research/         # Professional domain analyses (JSON/MD)
```

### Audience Research
- Inputs: entities defined in `data/config/entities.yaml`
- Outputs: `<entity-id>_research_<YYYYMMDD>.json`; display names remain in metadata

### Domain Research
- Inputs: domains defined in `data/config/domains.yaml`
- Outputs: `<domain-id>_research_<YYYYMMDD>.{json,md}`; display names remain in metadata

## Curriculum Content

```text
data/
├── written_curriculums/     # Generated curricula (per domain/entity)
├── translated_curriculums/  # Multilingual versions by language
```

### Written Curriculums
- Structure: per-stable-ID folders containing section `.md` files and a summary `.json`.
- Example: `data/written_curriculums/coffee_roasting/`

### Translated Curriculums
- Structure: stable language-ID subfolders (e.g., `spanish/`, `french/`, `chinese/`).
- Contents: `<entity-id>_curriculum_<language-id>_<timestamp>.md` with source hashes and parity metadata.

## Visualizations

```text
data/visualizations/
├── charts/curriculum_metrics.png
├── diagrams/                   # Stable-ID Mermaid flow diagrams
├── metrics/curriculum_metrics.{csv,json}
└── visualization_manifest.json # Input/output hashes and evidence boundary
```

### Generating Visualizations
Run from the repository root:

```bash
uv run start-curriculum --non-interactive --stages visualizations --json
```

The render stage returns only artifacts created by that invocation and does
not treat unrelated pre-existing files in the output directory as part of the new
bundle. Validate the resulting manifest with `start-validate-outputs`.

## Prompt Templates

```text
data/prompts/
├── research_domain_analysis.md
├── research_domain_curriculum.md
├── research_entity.md
└── translation.md
```

These drive LLM prompt engineering for research, curriculum, personalization, and translation.

## Configuration Files

```text
data/config/
├── entities.yaml
├── domains.yaml
└── languages.yaml
```

Use these to control which entities/domains/languages are processed.

## Auditing and curation

Audit is read-only. Curation requires a human-reviewed JSON allow-list and is
plan-first; mutation requires an explicit archive destination or `--remove`.

```bash
uv run start-audit-artifacts --root . --write data/artifact-manifests/current.json
uv run start-curate-artifacts --manifest data/artifact-manifests/current.json \
  --keep /path/to/reviewed-keep.json --only-duplicates --json
uv run start-curate-artifacts --manifest data/artifact-manifests/current.json \
  --keep /path/to/reviewed-keep.json --archive-dir /path/to/archive --apply --json
```
