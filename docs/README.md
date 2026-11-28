# START documentation

START is a configurable curriculum research and generation pipeline. This folder
is the GitHub-readable documentation index; every page is modular and links to
deeper material. The [Documentation Hub](index.md) is the MkDocs landing page and
the narrative hub for the published site.

Begin with [Getting Started](guides/getting_started.md), then review
[Configuration](reference/configuration.md) and the [Pipeline](architecture/pipeline.md).

**Quick reference**: [Documentation Index](documentation-index.md) ·
[Gate entry point](development/gate.md) · [Testing](development/TESTING.md) · [GNN conformance](development/gnn_conformance.md) ·
[Generated gate numbers](_generated/gate-timings.md)

## Start here

- [Documentation Hub (narrative hub, MkDocs landing)](index.md)
- [Getting Started](guides/getting_started.md)
- [Environment Setup](reference/environment.md)
- [Pipeline Overview](architecture/pipeline.md)
- [Configuration Reference](reference/configuration.md)
- [Testing Guide](development/TESTING.md)

## Setup and usage

- [Getting Started](guides/getting_started.md) — install, first run, generate outputs
- [Environment](reference/environment.md) — prerequisites, API keys, CI parity
- [Configuration](reference/configuration.md) — YAML schemas and CLI usage
- [Curriculum Generator GUI](guides/curriculum_gui.md) — browser-based generation
- [Clone Management](guides/clones.md) — fetch external ecosystem repositories
- [Examples & Outputs](guides/examples.md) — where generated artifacts live

## Architecture and evidence

- [Pipeline](architecture/pipeline.md) — acquire → prepare → process → parse → render
- [Methods & Evidence Protocol](architecture/methods.md) — constraints, hypotheses, quality gates
- [Manuscript Note](manuscript/README.md) — publication scope and limitations
- [Operations](development/operations.md) — release evidence and operational notes
- [GNN Conformance](development/gnn_conformance.md) — pin file, pointer, and conformance job

## Outputs and localization

- [Data & Outputs](architecture/data_outputs.md) — artifact directory purposes and descriptions
- [Visualizations](architecture/visualizations.md) — diagram/chart gallery and regeneration
- [Translations](architecture/translations.md) — multilingual output structure

## Development and reference

- [Gate entry point](development/gate.md) — `start-gate` arms, CI job mapping, local-run policy
- [Generated gate numbers](_generated/gate-timings.md) — arm wall times, test selection counts, coverage
- [Testing](development/TESTING.md) — policies, markers, offline/CI rules
- [Contributing](development/CONTRIBUTING.md) — workflow, quality gates, PR checklist
- [Conventions](development/conventions.md) — documentation structure and naming
- [FAQ](reference/FAQ.md) — common questions and troubleshooting
- [Roadmap](development/ROADMAP.md) — pointer to the canonical backlog in [`../TODO.md`](../TODO.md)
- [Docs & Deployment](development/docs_and_deployment.md) — local serve, build, GitHub Pages

## Learning guides

- [Usage Guide](guides/learning_usage_guide.md) — points at the curriculum-creation usage guide
- [API Integration](reference/learning_api_integration.md) — points at the curriculum-creation README

## Other material

- [Other materials index](other/index.md)
- [Inferant Stream 015-1](other/inferant_stream_015-1.md)

## Folder guides

- [Agent-facing docs guide](AGENTS.md) — technical reference for this folder
- [Other materials guides](other/README.md)

---

The same content is published from this documentation directory for GitHub
readers and the MkDocs site build (`mkdocs.yml`). [Documentation Index](documentation-index.md)
lists every long-lived page, including the generated gate-timings document.

## Documentation by topic

- [Guides](guides/README.md)
- [Architecture](architecture/README.md)
- [Reference](reference/README.md)
- [Development](development/README.md)
- [Manuscript source and render](manuscript/README.md)
