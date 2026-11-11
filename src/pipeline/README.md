# Pipeline (`src/pipeline`)

The canonical orchestrator for START. It runs the typed, resumable
`acquire → prepare → process → parse → render` pipeline and is what the
`start-curriculum` console entry point drives. The staged scripts under
`learning/curriculum_creation/` delegate here rather than reimplementing it.

The runner is transactional: a stage that contains a failed item reports
`ok=False`, and curriculum publication leaves no partial artifact when any
section fails.

## Modules

### `runner.py`

`PipelineRunner`, `RunContext` — the acquire → prepare → process → parse →
render orchestrator: stage selection, early stop, checkpoint/run manifests, and
usage aggregation.

### `contracts.py`

`PipelineResult`, `StageResult`, `StageItemResult`, `StageSpec`, `StageStatus`,
`RunConfig` — typed result contracts. `StageResult.__post_init__` re-assesses
status after deriving item failures so partial failure is never reported green.

### `stages.py`

Stage specifications and early-stop semantics; records skipped required stages
so resumed runs report real durations.

### `manifest.py`

`RunManifest`, `ArtifactRecord` — atomic run manifests and checkpoint
persistence.

### `artifacts.py`

Published artifact records and output-root enforcement.

### `provenance.py`

`input_record`, `file_input_record`, `generation_metadata` — evidence-status and
provenance metadata for generated artifacts.

### `quality.py`

`QualityReport`, `validate_generated_text`, `validate_translation` — structural
quality checks (word/section counts, script parity).

### `parsers.py`

Fence-aware Markdown parsing: `parse_research_response`,
`parse_curriculum_response`, `parse_translation_response`,
`parse_visualization_response` and their `*Response` dataclasses.

### `usage.py`

`empty_usage`, `merge_usage`, `aggregate_usage`, `normalize_usage` — provider
usage and cost normalization.

### `history.py`

`list_runs`, `summarize_runs`, `retention_candidates`, `prune_runs`,
`RunSummary` — filesystem-backed run history.

### `schemas.py`

`ProviderPayload`, `StructuredPayloadError`, `parse_structured_response`,
`payload_markdown` — pipeline-level structured-response validation.

### `__init__.py`

Re-exports the public surface above so callers can `from src.pipeline import
PipelineRunner, StageResult, ...`.

## Usage

The installed orchestrator is the supported entry point:

```bash
uv run start-curriculum --help
uv run start-curriculum --non-interactive --stages domain-research --json
uv run start-validate-outputs --check
```

The modules expose a typed Python API (`PipelineRunner`, `RunConfig`,
`StageResult`, `RunManifest`, the response parsers, and the usage/quality
helpers) re-exported from `src.pipeline`; see each module above and the tests
under `tests/` for current call signatures.

## Where it is documented

- [src/AGENTS.md](../AGENTS.md) — source-tree technical reference
- [../../docs/pipeline.md](../../docs/pipeline.md) — pipeline architecture and stages
- [../gnn/README.md](../gnn/README.md) — the separate `start-gnn` orchestrator
