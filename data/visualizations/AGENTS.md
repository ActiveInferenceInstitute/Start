# Visualization bundle technical reference

The canonical generator is `src/visualization/runner.py`, invoked through
`uv run start-curriculum --non-interactive --stages visualizations`. It writes
one deterministic, inspectable bundle:

```text
data/visualizations/
├── charts/curriculum_metrics.png
├── diagrams/<stable-item-id>_flow.mmd
├── diagrams/curriculum_structure.mmd
├── metrics/curriculum_metrics.csv
├── metrics/curriculum_metrics.json
└── visualization_manifest.json
```

The manifest records schema version, input item identifiers and hashes, output
hashes and sizes, generation time, and the boundary that these are derived
structural summaries rather than independent factual evidence. Paths use the
stable identifier policy from `src/config/schemas.py`; display names remain in
the metric records and manifest metadata.

The numbered visualization script remains importable as a staged entrypoint,
but new automation should use the canonical runner. Do not manually edit generated
files; regenerate, validate, and review the manifest instead.

Cross-references: [README.md](README.md),
[src/visualization/runner.py](../../src/visualization/runner.py), and
[visualization guide](../../docs/visualizations.md).
