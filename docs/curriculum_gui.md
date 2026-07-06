# Curriculum Generator GUI

The START project includes a lightweight browser-based GUI for generating custom Active Inference curricula without needing to use the command line.

## Quick Start

```bash
uv run python learning/curriculum_creation/generate_curriculum_gui.py
```

This launches a local HTTP server (default: `http://127.0.0.1:8765`) and opens your default browser.

## GUI Features

- **Domain selection**: Choose from configured domains or enter a custom domain
- **Entity selection**: Choose from configured entities or enter a custom entity with optional description
- **Language selection**: Choose from configured languages or enter a custom language
- **Live progress**: Real-time progress bar, stage name, ETA estimate
- **Results summary**: After completion, shows success/failure counts per pipeline stage

## How It Works

The GUI uses **only the Python standard library** — no extra dependencies. It:

1. Serves an HTML/CSS/JS frontend from a built-in HTTP server
2. Accepts form input (domain, entity, language, entity description)
3. Spawns a background thread running the `CurriculumOrchestrator` from `generate_custom_curriculum.py`
4. Polls a `/status` endpoint every second for live updates
5. Displays results when the pipeline completes

## Pipeline Stages

The GUI runs all five stages of the pipeline:

1. **Domain Research** (25%) — Analyzes the domain using Perplexity API
2. **Entity Research** (25%) — Researches the target audience using Perplexity API
3. **Curriculum Generation** (30%) — Generates curriculum content using OpenRouter API
4. **Visualization** (10%) — Creates charts and Mermaid diagrams
5. **Translation** (10%) — Translates to the target language using OpenRouter API

## Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--host` | Server host address | `127.0.0.1` |
| `--port` | Server port | `8765` |
| `--no-browser` | Don't auto-open browser | `False` |

Example:
```bash
uv run python learning/curriculum_creation/generate_curriculum_gui.py --port 9000 --no-browser
```

## API Endpoints

The GUI server exposes these JSON endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves the HTML GUI |
| `/options` | GET | Returns available domains, entities, languages as JSON |
| `/status` | GET | Returns current pipeline progress as JSON |
| `/results` | GET | Returns HTML summary of completed run |
| `/start` | POST | Starts a pipeline run with form data |

## Notes

- The GUI requires the same API keys as the CLI pipeline (`PERPLEXITY_API_KEY`, `OPENROUTER_API_KEY`)
- Only one pipeline run can be active at a time
- Custom domains/entities/languages entered in the text fields are created on-the-fly
- Entity descriptions are optional but improve research quality for custom entities