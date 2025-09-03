# Visualizations

Gallery and references for generated diagrams and charts.

## Flow Diagrams

The pipeline produces flow diagrams for domains/entities and the overall curriculum structure (Mermaid source files). View and edit the `.mmd` sources directly.

Examples (in-repo):
- `data/visualizations/curriculum_structure.mmd`
- `data/visualizations/Coffee Roasting_flow.mmd`
- `data/visualizations/Myrmecology_flow.mmd`

## Section Breakdown Charts

Bar charts summarizing section metrics.

Artifacts:
- `data/visualizations/*_section_breakdown.png`

## Metrics

Aggregate curriculum metrics used for charts and diagnostics.

Artifacts:
- `data/visualizations/curriculum_metrics.json`
- `data/visualizations/curriculum_metrics.png`

## How to Regenerate

Run from `learning/curriculum_creation/`:

```bash
uv run python 3_Introduction_Visualizations.py
```

### Headless/CI environments

If running without a display (servers, CI), set a non-GUI backend for matplotlib:

```bash
export MPLBACKEND=Agg
uv run python learning/curriculum_creation/3_Introduction_Visualizations.py
```

### Troubleshooting

- Ensure inputs exist in `data/written_curriculums/` before generating charts.
- Confirm write permissions for `data/visualizations/`.
- Check `data/visualizations/curriculum_metrics.json` for schema if charts appear empty.



