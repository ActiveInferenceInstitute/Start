# Here — starting at `start/here`

Welcome. This is a simple, actionable landing page into the Active Inference Ecosystem and Institute, centered on this repository. If you only read one file to begin, make it this one.

---

## Why this repo exists

- **Learn by doing**: Generate, visualize, and translate curriculum content grounded in real data.
- **Build end-to-end**: No mocks; real IO, reproducible scripts, and tests.
- **Contribute to the ecosystem**: Improve docs, scripts, and learning materials for the broader community.

---

## Active Inference @Web

- **Institute**: [Active Inference Institute](https://www.activeinference.institute/)
- **Livestreams**: [activeinference.institute/livestreams](https://www.activeinference.institute/livestreams)
- **Courses**: [activeinference.institute/courses](https://www.activeinference.institute/courses)
- **Journal**: [Active Inference Journal](https://www.activeinference.org/research/journal)
- **Volunteer & internships**: [activeinference.org/education/volunteer](https://www.activeinference.org/education/volunteer)
- **Welcome portal**: [welcome.activeinference.institute](https://welcome.activeinference.institute/)
- **Knowledge graph**: [obsidian.activeinference.institute](https://obsidian.activeinference.institute/)
- **Cognitive repository**: [ActiveInferenceInstitute/cognitive](https://github.com/ActiveInferenceInstitute/cognitive)
- **Tutorial scripts**: [Active Inference Tutorial Scripts](https://github.com/rssmith33/Active-Inference-Tutorial-Scripts)
- **Free Energy Principle papers**: [activeinference.github.io](https://activeinference.github.io/)
- **Demystified overview**: [arXiv:1909.10863](https://arxiv.org/abs/1909.10863)
- **Step-by-step tutorial**: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8956124/)
- **pymdp docs**: [Active Inference from Scratch](https://pymdp-rtd.readthedocs.io/en/master/notebooks/active_inference_from_scratch.html)

---

## Repo docs (read first)

- **Overview**: [docs/index.md](docs/index.md)
- **Getting set up**: [docs/getting_started.md](docs/getting_started.md), [docs/environment.md](docs/environment.md)
- **Configuration & conventions**: [docs/configuration.md](docs/configuration.md), [docs/conventions.md](docs/conventions.md)
- **Pipelines**: [docs/pipeline.md](docs/pipeline.md), [docs/examples.md](docs/examples.md)
- **Testing**: [docs/TESTING.md](docs/TESTING.md), `pytest.ini`

---

## What you can do with this repo

- **Research a domain or entity** and write a concise introduction
  - Scripts: `learning/curriculum_creation/1_Research_Domain.py`, `learning/curriculum_creation/1_Research_Entity.py`, `learning/curriculum_creation/2_Write_Introduction.py`
  - Guides: [learning/curriculum_creation/INTERACTIVE_GUIDE.md](learning/curriculum_creation/INTERACTIVE_GUIDE.md), [learning/curriculum_creation/README.md](learning/curriculum_creation/README.md), [learning/curriculum_creation/USAGE_GUIDE.md](learning/curriculum_creation/USAGE_GUIDE.md)

- **Visualize curriculum structure**
  - Script: `learning/curriculum_creation/3_Introduction_Visualizations.py`
  - Outputs: `data/visualizations/` (e.g., `*_flow.mmd`, `*_section_breakdown.png`, `curriculum_structure.mmd`)

- **Translate introductions**
  - Script: `learning/curriculum_creation/4_Translate_Introductions.py`
  - Outputs: `data/translated_curriculums/` (Chinese, French, Spanish, Tagalog)

- **Generate full custom curriculum**
  - Entry point: `learning/curriculum_creation/generate_custom_curriculum.py`
  - Outputs: `data/written_curriculums/` (organized by topic)

---

## Deep links (repository map)

- **Core code**: `src/`
  - Common utilities: `src/common/`
  - System & reporting: `src/system/`
  - Visualization: `src/visualization/`
  - Terminal UX: `src/terminal/`
  - External clients: `src/perplexity/`, `src/repos/`

- **Data and artifacts**: `data/`
  - Prompts: `data/prompts/`
  - Research: `data/domain_research/`, `data/audience_research/`
  - Visuals: `data/visualizations/`
  - Written & translated: `data/written_curriculums/`, `data/translated_curriculums/`

- **Documentation**: `docs/` (rendered site in `site/`)

- **Tests**: `tests/` (end-to-end and unit tests; `pytest.ini` config)

- **Top-level helpers**: `run.sh`, `run_docs.sh`, `pyproject.toml`, `mkdocs.yml`

---

## Contribute and connect

- Contributing fixes or features: follow [docs/conventions.md](docs/conventions.md) and run tests locally.
- Ask questions or propose ideas via issues/PRs and reference relevant tests in `tests/`.
- Explore ecosystem code: [ActiveInferenceInstitute/cognitive](https://github.com/ActiveInferenceInstitute/cognitive)

---

## A note of welcome

Thanks for being here. This project aims to make active inference practical, legible, and collaborative. Start small, ship something real, and share what you learn.

---

## Go beyond prose: Math & Programming

For readers who want to move into formalism and implementation.

### Quick start (commands)

1. Install Python 3.11+ and UV. Then bootstrap:

```bash
uv sync --all-extras --dev
```

1. Run the full test workflow (no network by default):

```bash
uv run pytest -q
```

1. Explore examples, data, and scripts below; then try an end-to-end curriculum generation run:

```bash
uv run python learning/curriculum_creation/generate_custom_curriculum.py --help
```

1. Optional: build and view local docs site:

```bash
chmod +x ./run_docs.sh && ./run_docs.sh
```

### Math & notation

Equations are supported via LaTeX in Markdown. For example, variational free energy:

\[ F(q) = \mathbb{E}_{q(z)}[\log q(z)] - \mathbb{E}_{q(z)}[\log p(x, z)] \]

and Bayes' rule:

\( p(z\mid x) = \frac{p(x\mid z)\,p(z)}{p(x)} \).

### Common tasks (development)

- Validate environment, code style, and tests:

```bash
uv run pytest -q && uv run ruff check . && uv run black --check .
```

- Run a domain research → intro → viz → translate flow (manually):

```bash
uv run python learning/curriculum_creation/1_Research_Domain.py
uv run python learning/curriculum_creation/2_Write_Introduction.py
uv run python learning/curriculum_creation/3_Introduction_Visualizations.py
uv run python learning/curriculum_creation/4_Translate_Introductions.py
```

- Inspect outputs:
  - Research: `data/domain_research/`
  - Visuals: `data/visualizations/`
  - Curriculums: `data/written_curriculums/`
  - Translations: `data/translated_curriculums/`
