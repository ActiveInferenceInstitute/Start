# Configuration Reference

This page collects configuration examples and CLI snippets.

## YAML Examples

```yaml
# data/config/entities.yaml - Target learners
entities:
  - name: "karl_friston"
    description: "Neuroscientist, developer of Free Energy Principle"
    category: "scientist"
    priority: "high"
  - name: "elon_musk"
    description: "CEO of Tesla, SpaceX, and other ventures"
    category: "tech_leader"
    priority: "medium"

# data/config/domains.yaml - Professional domains
domains:
  - name: "biochemistry"
    id: "biochemistry"           # stable identifier; display name may change
    description: "Study of chemical processes within living organisms"
    category: "life_sciences"
    priority: "high"
    keywords: ["molecular biology", "enzymes", "metabolism"]
  - name: "artificial_intelligence"
    description: "Computer systems capable of tasks requiring human intelligence"
    category: "technology"
    priority: "high"
    keywords: ["machine learning", "neural networks", "robotics"]
    source_urls: ["https://example.org/source"]
    verification_date: "2026-07-17"
```

## CLI Examples

```bash
# Process only high-priority items through the canonical runner
uv run start-curriculum --non-interactive --stages entity-research \
  --entity-priority high --json
uv run start-curriculum --non-interactive --stages domain-research \
  --domain-priority high --json

# Filter by professional category
uv run start-curriculum --non-interactive --stages domain-research \
  --domain-category life_sciences --json
uv run start-curriculum --non-interactive --stages domain-research \
  --domain-category technology --json

# Process specific targets
uv run start-curriculum --non-interactive --stages entity-research \
  --entities karl_friston --json
uv run start-curriculum --non-interactive --stages domain-research \
  --domains biochemistry --json

# Control overwrite behavior
uv run start-curriculum --non-interactive --stages domain-research \
  --overwrite --json  # Force overwrite existing
# Default: skip existing files automatically

# Plan a safe, offline run with a stable manifest location
uv run python -m learning.curriculum_creation.generate_custom_curriculum \
  --non-interactive --domains biochemistry --entities "Karl Friston" \
  --languages Spanish --dry-run --run-id planning-example --json

# Require source URLs and verification dates for publication-mode inputs
uv run start-curriculum --non-interactive --domains biochemistry \
  --entities "Karl Friston" --languages Spanish --publication \
  --budget-usd 0.25 --run-id publication-example --json

# Inspect generated output contracts and filesystem run history
uv run start-validate-outputs --check
uv run start-run-history --root data/written_curriculums/.runs --json
```

Publication mode fails closed when configured domains or entities lack
`source_urls` and an ISO `verification_date`. Exploratory custom inputs remain
available outside publication mode but are marked as unverified in run
provenance. `--budget-usd` is enforced both against the preflight estimate and
against observed provider usage when pricing metadata is available.

## Project Structure (High-Level)

```text
START/
├── src/                      # Core system implementation
├── learning/                 # Curriculum creation scripts
├── data/                     # Generated content and configuration
├── docs/                     # Comprehensive documentation
├── tests/                    # Test suite and validation
└── README.md                 # Project overview and quick start
```
