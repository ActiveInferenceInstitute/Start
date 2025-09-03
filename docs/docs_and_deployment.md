# Documentation & Deployment

This page explains how to build, serve, and deploy the docs site locally and to GitHub Pages.

## Quick Commands

```bash
# Serve locally with live reload (opens browser)
./run_docs.sh --serve

# Build static site into ./site and open file URL
./run_docs.sh --build

# Deploy to GitHub Pages (gh-pages branch) and open Pages URL
./run_docs.sh --deploy
```

The script auto-selects a MkDocs runner in this order: `uvx mkdocs`, `mkdocs`, or `uv run --with mkdocs --with mkdocs-material mkdocs`.

## Prerequisites

- `mkdocs.yml` at repository root
- Either `uvx` (recommended), `mkdocs`, or `uv`
- Network access for GitHub Pages deploy

## GitHub Pages

### Deploy from Branch
- The script runs `mkdocs gh-deploy --force`, publishing to the `gh-pages` branch.
- GitHub Pages serves the site from `gh-pages` automatically when configured to "Deploy from a branch".
- After deploy, the script opens the computed URL: `https://<org>.github.io/<repo>/`.

### Deploy with Actions (Alternative)
If you prefer a custom GitHub Actions workflow (checkout → build → upload-pages-artifact → deploy-pages), add a workflow under `.github/workflows/pages.yml` following GitHub's guide. The local script remains useful for previewing changes and local development.

Reference: GitHub Docs — Publishing with a custom GitHub Actions workflow.

## Troubleshooting

- If `mkdocs` is not installed, the script falls back to `uvx` or a temporary `uv run` install.
- Ensure `mkdocs.yml` exists at the repo root.
- Conflicts warning (README vs index): ensure only one maps to the root path in `nav`.

### Common errors

- "mkdocs: command not found": Install `uv` and rely on `uvx mkdocs`, or `pipx install mkdocs`.
- 404 on GitHub Pages: Confirm repository settings → Pages → Deploy from `gh-pages` branch.
- Broken internal links: Verify paths in `mkdocs.yml` `nav:` entries match file names.



