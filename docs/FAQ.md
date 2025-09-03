# FAQ

## What is START?
A pipeline for research-driven, personalized curricula using Perplexity and OpenRouter.

## How do I install and run tests?
See Environment: ./environment.md. Then run:
```bash
uv sync --all-extras --dev
uv run pytest -q
```

## How do I generate content?
See Getting Started: ./getting_started.md and Pipeline: ./pipeline.md.

## Where do outputs go?
See Data & Outputs: ./data_outputs.md.

## How do I see the docs site?
Run `./run_docs.sh --serve` (local) or visit GitHub Pages at the project site.

## How can I contribute?
See Contributing: ./CONTRIBUTING.md.

## Where are examples?
See Examples: ./examples.md and tests in `tests/`.

## What keys do I need?
Required: `PERPLEXITY_API_KEY` and `OPENROUTER_API_KEY`. Optional: `OPENAI_API_KEY`. Copy `.env.example` to `.env` and fill in values.

## Do tests use the network?
No by default. Network tests only run if `CI=true` and are marked with `@network`. See ./TESTING.md.

## Docs site won’t start — what should I check?
Use `./run_docs.sh --serve`. Ensure `mkdocs.yml` exists at repo root. The script prefers `uvx mkdocs`, then `mkdocs`, then a temporary `uv run` install of mkdocs.

## Visualizations not generating?
Run `uv run python learning/curriculum_creation/3_Introduction_Visualizations.py`. If running headless (servers/CI), set `MPLBACKEND=Agg`.

## CLI examples don’t work from my cwd
Either prefix scripts with their path (e.g., `uv run python learning/curriculum_creation/1_Research_Domain.py ...`) or `cd learning/curriculum_creation/` first.

## Where do outputs go?
Research in `data/audience_research/` and `data/domain_research/`; curricula in `data/written_curriculums/`; visuals in `data/visualizations/`; translations in `data/translated_curriculums/`. See ./data_outputs.md.
