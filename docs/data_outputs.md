# Data & Outputs

This page summarizes where the system writes artifacts and what each directory contains.

## Research Artifacts

```text
data/
├── audience_research/       # Personalized learner/entity profiles (JSON/MD)
├── domain_research/         # Professional domain analyses (JSON/MD)
```

### Audience Research
- Inputs: entities defined in `data/config/entities.yaml`
- Outputs: `<Entity>_research_<YYYYMMDD>.{json,md}`

### Domain Research
- Inputs: domains defined in `data/config/domains.yaml`
- Outputs: `<Domain>_research_<YYYYMMDD>.{json,md}`

## Curriculum Content

```text
data/
├── written_curriculums/     # Generated curricula (per domain/entity)
├── translated_curriculums/  # Multilingual versions by language
```

### Written Curriculums
- Structure: per-domain folders containing section `.md` files and a summary `.json`.
- Example: `data/written_curriculums/Coffee Roasting/`

### Translated Curriculums
- Structure: language subfolders (e.g., `spanish/`, `french/`, `chinese/`, `tagalog/`).
- Contents: translated `.md` sections matching the source curriculum.

## Visualizations

```text
data/visualizations/
├── *_flow.mmd                 # Mermaid flow diagrams
├── *_section_breakdown.png    # Section-level charts
├── curriculum_metrics.{json,png}  # Aggregate metrics
├── curriculum_structure.mmd   # Overall structure diagram
```

### Generating Visualizations
Run from `learning/curriculum_creation/`:

```bash
uv run python 3_Introduction_Visualizations.py
```

## Prompt Templates

```text
data/prompts/
├── research_domain_analysis.md
├── research_domain_curriculum.md
├── research_entity.md
└── translation.md
```

These drive LLM prompt engineering for research, curriculum, personalization, and translation.

## Configuration Files

```text
data/config/
├── entities.yaml
├── domains.yaml
└── languages.yaml
```

Use these to control which entities/domains/languages are processed.



