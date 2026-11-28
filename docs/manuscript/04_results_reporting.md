# Results reporting

Results must be generated from the current checkout rather than copied into a
static claim. Use:

```bash
uv run start-gate full      # suite + branch-aware coverage
uv run start-gate docs      # strict docs build + repository/link validation
uv run start-gate artifacts # provenance, output contracts, offline fixture replay
uv run start-gate numbers   # generated timings/coverage page is current
```

The current arm wall times, test selection counts, and coverage total are in
[`_generated/gate-timings.md`](https://github.com/ActiveInferenceInstitute/Start/blob/a825e8c13cc45196a048be76e4cc428719b8228b/docs/_generated/gate-timings.md), written by
`uv run start-gate measure`. They are intentionally not copied here because
counts, dependencies, and generated inputs change.
