# GNN conformance

START registers one upstream GNN checkout and checks it against a recorded pin.
Nothing here re-implements the GNN pipeline; the conformance job proves that the
pin, the clone registration, and the installed upstream parser agree.

## Canonical pin

`.github/gnn-pin.json` is the pin file, schema
`gnn-importer-pin/v1`:

| Field | Value |
| --- | --- |
| `schema` | `gnn-importer-pin/v1` |
| `repository` | `ActiveInferenceInstitute/Generalized_Notation_Notation` |
| `revision` | `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1` |
| `tag` | `v5.0.3` |
| `recorded` | `2026-11-12` |

The same revision is registered for cloning in `src/repos/cloning.py`, and
`src/gnn/main.py` builds the pipeline command the pin describes.

## Pointer

`.github/GNN.md` records what the conformance job parses:
the pinned upstream `input/gnn_files/basics/static_perception.md` exemplar, with
no scan of repository `*.gnn.md` files because Start has none at this head. It
states explicitly that this is a pipeline and pin conformance baseline, not a
model claim.

## Job

The job key is `gnn-conformance` and its display name is
`gnn conformance (pinned)`, both in `.github/workflows/ci.yml`. Its two steps are
gate arms:

- **Check pinned GNN registration** — `uv run start-gate gnn` runs
  `scripts/check_gnn_pin.py` (schema, repository, revision, clone registration,
  and pipeline command) and then `tests/test_gnn_runner.py`.
- **Parse the pinned GNN exemplar** — `uv run start-gate gnn-exemplar` runs
  `scripts/check_gnn_exemplar.py`, which first runs the same full pin validation
  as the offline arm, then installs the pinned upstream package without resolving
  dependencies. Its `defusedxml` and `psutil` helpers come from the locked `dev`
  extra (`uv sync --all-extras --dev --locked`). It fetches the pinned exemplar
  and runs the upstream parser, syntax validator, and type checker. This arm
  needs network access; the other arms do not.

## Actions used

Both workflows in this repository pin `actions/checkout` at
`3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1) and `astral-sh/setup-uv` at
`68559e99cc807c1eb7e9238fd43a15bba460eec2` (v10.3.3) with `enable-cache: true`.

The estate composite action
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`
is not referenced by any workflow in this repository at this head; the workflows
use `astral-sh/setup-uv` directly.
