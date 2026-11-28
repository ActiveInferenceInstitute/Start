# Visualizations

Visualization outputs are derived summaries, not independent evidence. Every
canonical render run writes a `visualization_manifest.json` that records the
input curriculum hashes, stable item IDs, output hashes, and the semantic limit
that charts describe structure rather than factual truth.

## Flow Diagrams

The pipeline produces flow diagrams for domains/entities and the overall curriculum structure (Mermaid source files). View and edit the `.mmd` sources directly.

Canonical examples:
- `data/visualizations/diagrams/curriculum_structure.mmd`
- `data/visualizations/diagrams/<stable-item-id>_flow.mmd`
- `data/visualizations/visualization_manifest.json`

## Section Breakdown Charts

Bar charts summarizing section metrics.

Artifacts:
- `data/visualizations/charts/curriculum_metrics.png`

## Metrics

Aggregate curriculum metrics used for charts and diagnostics.

Artifacts:
- `data/visualizations/metrics/curriculum_metrics.csv`
- `data/visualizations/metrics/curriculum_metrics.json`

## How to Regenerate

Run from the repository root:

```bash
uv run start-curriculum --non-interactive --stages visualizations --json
```

The render stage consumes `data/written_curriculums/`, uses stable identifiers
for filenames, and writes the CSV, JSON, PNG, Mermaid diagrams, and manifest as
one inspectable bundle. The manifest is the authoritative link between inputs
and derived outputs; it does not assert that a visual interpretation is true.

### Headless/CI environments

If running without a display (servers, CI), set a non-GUI backend for matplotlib:

```bash
export MPLBACKEND=Agg
uv run start-curriculum --non-interactive --stages visualizations --json
```

### Troubleshooting

- Ensure inputs exist in `data/written_curriculums/` before generating charts.
- Confirm write permissions for `data/visualizations/`.
- Check `data/visualizations/metrics/curriculum_metrics.json` for the metric
  schema if charts appear empty. The bundle manifest is at
  `data/visualizations/visualization_manifest.json`.
