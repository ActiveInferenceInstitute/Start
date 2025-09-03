# Documentation Conventions

This repository follows a modular, folder-based documentation approach that works both as raw Markdown and as a website (via MkDocs/GitHub Pages).

## File naming

- Top-level docs live in `docs/` and use clear, task-oriented names:
  - `getting_started.md`, `environment.md`, `pipeline.md`, `configuration.md`, `TESTING.md`, `examples.md`, `clones.md`, `README.md`
- Use lowercase with underscores; reserve uppercase for canonical files like `README.md`, `TESTING.md`.
- Prefer one topic per file; keep files focused and short.

## Structure (Diátaxis mapping)

- Tutorials: `getting_started.md`, examples embedded in usage guides
- How-to guides: `learning/curriculum_creation/USAGE_GUIDE.md`
- Explanations: `pipeline.md`, `clones.md`
- Reference: `environment.md`, `configuration.md`, `TESTING.md`

## Links and cross-references

- Intra-doc links use relative paths (e.g., `./pipeline.md`).
- Cross-area links should point to `learning/` guides where appropriate.
- Keep Mermaid diagrams minimal and with clickable links when useful.

## Site generation

- `mkdocs.yml` defines navigation mirroring the folder layout.
- Landing page is `docs/index.md`, mirroring `docs/README.md` hub content.
- Use common Markdown extensions: toc, admonition, tables, codehilite, def_list, footnotes, attr_list.

## Quality and maintenance

- Keep docs accurate and updated with changes.
- Use clear, concise language; avoid jargon.
- Validate locally with `uv run mkdocs serve` when editing site structure.
