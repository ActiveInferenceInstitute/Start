# Contributing

Thanks for improving START. This guide covers workflow, quality gates, and conventions.

## Workflow
- Fork and branch: feature/<topic> or fix/<topic>
- Keep changes minimal, cohesive, and lint-clean
- Write/update tests alongside changes (pytest)
- Open a PR with a clear description and links to related issues

## Local Quality Checks
```bash
uv sync --all-extras --dev --locked
uv run start-gate          # default arm: fast test selection
uv run start-gate lint     # ruff, black, shell syntax
uv run start-gate docs     # strict docs build + link/config validation
uv run start-gate --list   # every arm, with the command it runs
```

Each arm is the command CI runs; see [Gate entry point](gate.md).

## Coding Standards
- Python 3.11+; type annotations for public functions
- Readable, modular code; early returns; meaningful names
- No TODO comments; implement or open an issue
- Docstrings for public APIs; short, high-signal comments

## Docs
- Update relevant pages under `docs/` when behavior or dev flows change
- Use dense link-based outlines instead of embedded Mermaid
- Serve locally via `./run_docs.sh --serve`; build/deploy via `./run_docs.sh --build` / `--deploy`
- Check navigation in `mkdocs.yml` when adding or renaming pages

## Commit Messages
- Imperative mood: "Add", "Fix", "Refactor"
- Reference issues: `Fixes #123` when applicable

## PR Checklist
- [ ] Tests added/updated
- [ ] Docs updated
- [ ] Affected `uv run start-gate` arms pass locally (GitHub Actions is billing-locked)
- [ ] Clear motivation and scope

## Community
- Discussions, questions: issues or Discord
- Respectful, constructive collaboration
