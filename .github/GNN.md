# GNN conformance

`gnn conformance (pinned)` is defined in `.github/workflows/ci.yml` and reads
`.github/gnn-pin.json`, which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.1.0`
(`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`).

The job verifies the pin and installed parser, then parses and type-checks the
pinned upstream `input/gnn_files/basics/static_perception.md` exemplar. It does
not scan repository `*.gnn.md` files; Start has none at this head. This is a
pipeline and pin conformance baseline, not a model claim.
