# GNN conformance

`gnn conformance (pinned)` is defined in `.github/workflows/ci.yml` and reads
`.github/gnn-pin.json`, which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`).

The job verifies the pin and installed parser, then parses and type-checks the
pinned upstream `input/gnn_files/basics/static_perception.md` exemplar. It does
not scan repository `*.gnn.md` files; Start has none at this head. This is a
pipeline and pin conformance baseline, not a model claim.
