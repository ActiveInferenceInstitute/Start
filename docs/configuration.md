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
    description: "Study of chemical processes within living organisms"
    category: "life_sciences"
    priority: "high"
    keywords: ["molecular biology", "enzymes", "metabolism"]
  - name: "artificial_intelligence"
    description: "Computer systems capable of tasks requiring human intelligence"
    category: "technology"
    priority: "high"
    keywords: ["machine learning", "neural networks", "robotics"]
```

## CLI Examples

```bash
# Process only high-priority items
python learning/curriculum_creation/1_Research_Entity.py --priority high
python learning/curriculum_creation/1_Research_Domain.py --priority high

# Filter by professional category
python learning/curriculum_creation/1_Research_Domain.py --category life_sciences
python learning/curriculum_creation/1_Research_Domain.py --category technology

# Process specific targets
python learning/curriculum_creation/1_Research_Entity.py --entity karl_friston
python learning/curriculum_creation/1_Research_Domain.py --domain biochemistry

# Control overwrite behavior
python learning/curriculum_creation/1_Research_Domain.py --overwrite  # Force overwrite existing
# Default: skip existing files automatically
```

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


