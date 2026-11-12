# Documentation index

Flat index of the long-lived documentation in `docs/`. The narrative hub is
`README.md`; the MkDocs landing page is [`index.md`](index.md).

## Entry points

- `README.md` — documentation hub and navigation (GitHub-only; excluded from the built site)
- [index.md](index.md) — MkDocs landing page
- [gate.md](gate.md) — `start-gate` arms, CI job mapping, and local-run policy
- [documentation-index.md](documentation-index.md) — this file

## Setup and usage

- [getting_started.md](getting_started.md) — install, first run, generate outputs
- [environment.md](environment.md) — prerequisites, API keys, CI parity
- [configuration.md](configuration.md) — YAML schemas and CLI usage
- [curriculum_gui.md](curriculum_gui.md) — loopback browser generator
- [clones.md](clones.md) — external ecosystem repository clones
- [examples.md](examples.md) — where generated artifacts live

## Architecture and evidence

- [pipeline.md](pipeline.md) — acquire → prepare → process → parse → render
- [methods.md](methods.md) — constraints, hypotheses, quality gates
- [manuscript.md](manuscript.md) — manuscript-facing engineering note
- [operations.md](operations.md) — release evidence and operational notes
- [gnn_conformance.md](gnn_conformance.md) — pin file, pointer, and conformance job

## Outputs and localization

- [data_outputs.md](data_outputs.md) — artifact directory purposes
- [visualizations.md](visualizations.md) — diagram and chart gallery
- [translations.md](translations.md) — multilingual output structure

## Development and reference

- [TESTING.md](TESTING.md) — testing policy, markers, gate usage
- [CONTRIBUTING.md](CONTRIBUTING.md) — workflow, quality gates, PR checklist
- [conventions.md](conventions.md) — documentation structure and naming
- [FAQ.md](FAQ.md) — common questions and troubleshooting
- [ROADMAP.md](ROADMAP.md) — pointer to the canonical backlog in `TODO.md`
- [docs_and_deployment.md](docs_and_deployment.md) — local serve, build, Pages deploy

## Learning guides

- [learning_usage_guide.md](learning_usage_guide.md) — points at the curriculum-creation usage guide
- [learning_api_integration.md](learning_api_integration.md) — points at the curriculum-creation README

## Folder guides

- [AGENTS.md](AGENTS.md) — technical reference for this folder
- `other/README.md` — other materials
- [other/AGENTS.md](other/AGENTS.md) — other materials technical reference

## Other material

- [other/index.md](other/index.md) — other materials index
- [other/inferant_stream_015-1.md](other/inferant_stream_015-1.md) — Inferant Stream 015-1

## Generated documents

Written by a script; do not edit by hand.

- [_generated/gate-timings.md](_generated/gate-timings.md) — arm wall times, test
  selection counts, and coverage total, written by `uv run start-gate measure`
  and verified by `uv run start-gate numbers`
