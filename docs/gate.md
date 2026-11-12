# Gate entry point

`uv run start-gate <arm>` is the repository's single quality gate. Each arm is
one command; the GitHub Actions workflows call the same arms instead of holding
their own copies, so a local run and a hosted run cannot drift apart.

```bash
uv run start-gate            # default arm: fast
uv run start-gate --list     # every arm with its exact argv
uv run start-gate full       # one arm
```

Arm definitions live in `scripts/gate.py`. `start-gate`
runs each arm's commands with the locked interpreter that `uv sync
--all-extras --dev --locked` installs, and sets `MPLBACKEND=Agg` unless the
environment already sets it.

## Arms

| Arm | What it runs | Workflow job |
| --- | --- | --- |
| `lint` | Ruff, Black, and `bash -n` over `run.sh run_docs.sh src/setup.sh` | `checks` |
| `types` | `mypy src scripts learning --ignore-missing-imports` | `checks`, release gate |
| `fast` | Pytest with `-m "not slow and not network and not integration"` | `test` (3.11) |
| `full` | Pytest with `--cov=src --cov-branch --cov-fail-under=80` | `test` (3.12) |
| `docs` | `mkdocs build --strict` plus `scripts.validate_repository` | `docs`, Pages deploy |
| `numbers` | Verifies the generated timing document against `scripts/gate.py` | `docs` |
| `gnn` | `scripts.check_gnn_pin` plus `tests/test_gnn_runner.py` | `gnn-conformance` |
| `gnn-exemplar` | Pinned upstream exemplar parse and type check (requires network) | `gnn-conformance` |
| `artifacts` | Artifact provenance baseline, output contracts, offline fixture replay | `checks`, release gate |
| `smoke` | CLI `--help` entries and loopback GUI endpoints | `checks` |
| `audit` | `pip-audit --strict` | `checks`, release gate |
| `lock` | `uv lock --check` | `macos-smoke` |
| `smoke-macos` | `tests/test_core_hardening.py tests/test_visualization_runner.py` | `macos-smoke` |

`scripts.validate_repository` is the documentation and link check: it parses
every tracked JSON/YAML/TOML file, resolves local Markdown links in authored
text, enforces the flat documentation index's coverage of authored `docs/`
pages, and rejects retired paths and prohibited authored terminology. There is
no separate Markdown link checker in this repository.

## Default arm and test selection

The default arm is `fast`, which uses the markers declared in
`pytest.ini`: `slow`, `network`, and `integration`. The exact
selection sizes and per-arm wall times are recorded in
[`_generated/gate-timings.md`](_generated/gate-timings.md); they are measured,
not maintained by hand.

## CI jobs and deduplication

`.github/workflows/ci.yml` splits work so no arm runs twice:

- `checks` runs `lint`, `types`, `artifacts`, `smoke`, and `audit` once on Python
  3.12, instead of repeating them in every matrix leg.
- `test` runs `fast` on Python 3.11 and `full` on Python 3.12, so the coverage
  pass is paid once.
- `docs` runs `docs` and `numbers`.
- `gnn-conformance` runs `gnn` and `gnn-exemplar`.
- `macos-smoke` runs `lock` and `smoke-macos`; the documentation build and shell
  syntax checks stay on Linux where they already run.

Every job installs from the same `uv.lock` with `uv sync --all-extras --dev
--locked`, so a stale lock fails the job instead of silently resolving new
versions.

## Local runs are the only gate

The estate's GitHub Actions runs are billing-locked, so a workflow file is not
evidence that a commit passes. Run the affected arms locally before landing.
Arm output is the evidence; `start-gate measure` records the numbers.

## Release workflow

`.github/workflows/release-gate.yml` is manual (`workflow_dispatch`). Shared
checks call `types`, `audit`, and `artifacts`; only its publication floors stay
inline: `scripts.audit_artifacts --check --fail-on-unprovenanced`,
`scripts.validate_outputs --check --publication`, and the 90% coverage run. The
publication floors report the recorded provenance debt tracked in
`TODO.md` rather than passing.
