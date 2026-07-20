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

The script uses the repository-locked `uv run mkdocs` environment, matching CI and the Pages workflow.

## Prerequisites

- `mkdocs.yml` at repository root
- `uv` with the locked development environment (`uv sync --all-extras --dev`)
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

- If MkDocs is not available, run `uv sync --all-extras --dev` before retrying.
- Ensure `mkdocs.yml` exists at the repo root.
- Conflicts warning (README vs index): ensure only one maps to the root path in `nav`.

### Common errors

- "mkdocs: command not found": Install `uv`, then run `uv sync --all-extras --dev`.
- 404 on GitHub Pages: Confirm repository settings → Pages → Deploy from `gh-pages` branch.
- Broken internal links: Verify paths in `mkdocs.yml` `nav:` entries match file names.


