# START documentation

START is a configurable curriculum research and generation pipeline. This folder
is the GitHub-readable documentation index; every page is modular and links to
deeper material. The [Documentation Hub](index.md) is the MkDocs landing page and
the narrative hub for the published site.

Begin with [Getting Started](getting_started.md), then review
[Configuration](configuration.md) and the [Pipeline](pipeline.md).

**Quick reference**: [Documentation Index](documentation-index.md) ·
[Gate entry point](gate.md) · [Testing](TESTING.md) · [GNN conformance](gnn_conformance.md) ·
[Generated gate numbers](_generated/gate-timings.md)

## Start here

- [Documentation Hub (narrative hub, MkDocs landing)](index.md)
- [Getting Started](getting_started.md)
- [Environment Setup](environment.md)
- [Pipeline Overview](pipeline.md)
- [Configuration Reference](configuration.md)
- [Testing Guide](TESTING.md)

## Setup and usage

- [Getting Started](getting_started.md) — install, first run, generate outputs
- [Environment](environment.md) — prerequisites, API keys, CI parity
- [Configuration](configuration.md) — YAML schemas and CLI usage
- [Curriculum Generator GUI](curriculum_gui.md) — browser-based generation
- [Clone Management](clones.md) — fetch external ecosystem repositories
- [Examples & Outputs](examples.md) — where generated artifacts live

## Architecture and evidence

- [Pipeline](pipeline.md) — acquire → prepare → process → parse → render
- [Methods & Evidence Protocol](methods.md) — constraints, hypotheses, quality gates
- [Manuscript Note](manuscript.md) — publication scope and limitations
- [Operations](operations.md) — release evidence and operational notes
- [GNN Conformance](gnn_conformance.md) — pin file, pointer, and conformance job

## Outputs and localization

- [Data & Outputs](data_outputs.md) — artifact directory purposes and descriptions
- [Visualizations](visualizations.md) — diagram/chart gallery and regeneration
- [Translations](translations.md) — multilingual output structure

## Development and reference

- [Gate entry point](gate.md) — `start-gate` arms, CI job mapping, local-run policy
- [Generated gate numbers](_generated/gate-timings.md) — arm wall times, test selection counts, coverage
- [Testing](TESTING.md) — policies, markers, offline/CI rules
- [Contributing](CONTRIBUTING.md) — workflow, quality gates, PR checklist
- [Conventions](conventions.md) — documentation structure and naming
- [FAQ](FAQ.md) — common questions and troubleshooting
- [Roadmap](ROADMAP.md) — pointer to the canonical backlog in [`../TODO.md`](../TODO.md)
- [Docs & Deployment](docs_and_deployment.md) — local serve, build, GitHub Pages

## Learning guides

- [Usage Guide](learning_usage_guide.md) — points at the curriculum-creation usage guide
- [API Integration](learning_api_integration.md) — points at the curriculum-creation README

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
