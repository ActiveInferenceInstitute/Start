# Documentation index

Flat index of every authored Markdown page in `docs/`, including folder guides
and GitHub-only README pages. The `docs` gate enforces completeness; script-written
pages in `_generated/` are exempt. The narrative hub is `README.md`; the MkDocs
landing page is [`index.md`](index.md).

## Entry points

- `README.md` — documentation hub and navigation (GitHub-only; excluded from the built site)
- [index.md](index.md) — MkDocs landing page
- [gate.md](development/gate.md) — `start-gate` arms, CI job mapping, and local-run policy
- [documentation-index.md](documentation-index.md) — this file

## Setup and usage

- [getting_started.md](guides/getting_started.md) — install, first run, generate outputs
- [environment.md](reference/environment.md) — prerequisites, API keys, CI parity
- [configuration.md](reference/configuration.md) — YAML schemas and CLI usage
- [curriculum_gui.md](guides/curriculum_gui.md) — loopback browser generator
- [clones.md](guides/clones.md) — external ecosystem repository clones
- [examples.md](guides/examples.md) — where generated artifacts live

## Architecture and evidence

- [pipeline.md](architecture/pipeline.md) — acquire → prepare → process → parse → render
- [methods.md](architecture/methods.md) — constraints, hypotheses, quality gates
- [Manuscript source and render](manuscript/README.md) — engineering methods and evidence
- [operations.md](development/operations.md) — release evidence and operational notes
- [gnn_conformance.md](development/gnn_conformance.md) — pin file, pointer, and conformance job

## Outputs and localization

- [data_outputs.md](architecture/data_outputs.md) — artifact directory purposes
- [visualizations.md](architecture/visualizations.md) — diagram and chart gallery
- [translations.md](architecture/translations.md) — multilingual output structure

## Development and reference

- [TESTING.md](development/TESTING.md) — testing policy, markers, gate usage
- [CONTRIBUTING.md](development/CONTRIBUTING.md) — workflow, quality gates, PR checklist
- [conventions.md](development/conventions.md) — documentation structure and naming
- [FAQ.md](reference/FAQ.md) — common questions and troubleshooting
- [ROADMAP.md](development/ROADMAP.md) — pointer to the canonical backlog in `TODO.md`
- [docs_and_deployment.md](development/docs_and_deployment.md) — local serve, build, Pages deploy

## Learning guides

- [learning_usage_guide.md](guides/learning_usage_guide.md) — points at the curriculum-creation usage guide
- [learning_api_integration.md](reference/learning_api_integration.md) — points at the curriculum-creation README

## Folder guides

- `AGENTS.md` — technical reference for this folder
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

## Additional pages

- [Architecture](architecture/README.md)
- [Development](development/README.md)
- [Guides](guides/README.md)
- [Abstract](manuscript/00_abstract.md)
- [Contribution and scope](manuscript/01_contribution_and_scope.md)
- [Method](manuscript/02_method.md)
- [Evidence boundary](manuscript/03_evidence_boundary.md)
- [Results reporting](manuscript/04_results_reporting.md)
- [Limitations and next study](manuscript/05_limitations_and_next_study.md)
- [References](manuscript/99_references.md)
- [Manuscript guidance](manuscript/AGENTS.md)
- [LaTeX preamble](manuscript/preamble.md)
- [Reference](reference/README.md)
