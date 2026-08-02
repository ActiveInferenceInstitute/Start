# START Project Documentation Hub

Welcome to the comprehensive documentation for the START (Scalable, Tailored Active-inference Research & Training) project - an advanced AI-powered system for creating personalized Active Inference and Free Energy Principle curricula.

## 🚀 **What is START?**

START is a complete educational content generation pipeline that combines:

- **Real-time research** using Perplexity API for current domain insights
- **Advanced LLM-based content generation** via OpenRouter for professional-quality curricula
- **Comprehensive personalization** tailored to specific learners and professional domains
- **Multilingual capabilities** with full cultural adaptation
- **Rich visualizations** including charts, diagrams, and interactive elements

## 📚 **Documentation Structure**

- Environment & Setup: [Environment Setup](./environment.md)
- System Architecture: [Pipeline Overview](./pipeline.md)
- Methods: [Methods and Evidence Protocol](./methods.md)
- Manuscript Note: [Reviewable Learning Artifacts](./manuscript.md)
- Operations: [Operations and Release Evidence](./operations.md)
- Getting Started: [Quickstart](./getting_started.md)
- Configuration: [Reference](./configuration.md)
- Data & Outputs: [Locations and artifacts](./data_outputs.md)
- Visualizations: [Gallery and regeneration](./visualizations.md)
- Translations: [Multilingual outputs](./translations.md)
- Docs & Deployment: [Local + GitHub Pages](./docs_and_deployment.md)
- Testing: [Policy and workflows](./TESTING.md)
- Examples: [Examples & outputs](./examples.md)
- Clone Management: [External repos](./clones.md)
- Learning Guides:
  - Usage Guide: [Learning Usage Guide](./learning_usage_guide.md)
  - API Integration: [Learning API Integration](./learning_api_integration.md)

### Core Guides

#### 🛠️ **Setup & Development**

- **[Environment Setup](./environment.md)** - Complete installation, configuration, and development guide
  - Prerequisites, API setup, dependency management
  - Development workflow, testing, troubleshooting
  - IDE integration and advanced configuration

#### 🔄 **System Architecture**

- **[Pipeline Overview](./pipeline.md)** - Comprehensive system architecture and workflow
  - acquire → prepare → process → parse → render curriculum pipeline
  - Configuration-driven research approach
  - API integration and content generation standards

#### 🧪 **Methods and Publication**

- **[Methods and Evidence Protocol](./methods.md)** - First-principles
  constraints, hypotheses, quality gates, and reproducibility protocol
- **[Manuscript Note](./manuscript.md)** - Publication-facing scope, evidence
  boundary, and limitations

#### 🔗 **External Integrations**

- **[Repository & Clone Management](./clones.md)** - External resource integration
  - Active Inference Institute ecosystem integration
  - Knowledge graph and implementation repositories
  - Educational resource enhancement strategies

### Specialized Documentation

#### 📖 **User Guides**

- **[Usage Guide](https://github.com/ActiveInferenceInstitute/Start/blob/main/learning/curriculum_creation/USAGE_GUIDE.md)**
- **[API Integration Guide](https://github.com/ActiveInferenceInstitute/Start/blob/main/learning/curriculum_creation/README.md)**

#### 🔧 **Configuration Reference**

- **Entity Configuration**: `data/config/entities.yaml` - Target learner profiles
- **Domain Configuration**: `data/config/domains.yaml` - Professional domain definitions
- **Language Configuration**: `data/config/languages.yaml` - Translation targets

#### 📦 **Data & Outputs**

- **[Data & Outputs](./data_outputs.md)** - Where artifacts are written and how to use them

#### 📊 **Visualizations**

- **[Visualizations](./visualizations.md)** - Diagram and chart gallery with regeneration steps

#### 🌍 **Translations**

- **[Translations & Localization](./translations.md)** - Multilingual outputs and structure

#### 🧭 **Docs & Deployment**

- **[Docs & Deployment](./docs_and_deployment.md)** - Local serve, build, and GitHub Pages

#### 📝 **Prompt Engineering**

- **Domain Analysis Templates**: `data/prompts/research_domain_analysis.md`
- **Curriculum Generation Templates**: `data/prompts/research_domain_curriculum.md`
- **Personalization Templates**: `data/prompts/research_entity.md`
- **Translation Framework**: `data/prompts/translation.md`

## 🎯 **Quick Start Paths**

### For New Users

1. **[Environment Setup](./environment.md)** - Get up and running
2. **[Pipeline Overview](./pipeline.md)** - Understand the system
3. **[Usage Guide (GitHub)](https://github.com/ActiveInferenceInstitute/Start/blob/main/learning/curriculum_creation/USAGE_GUIDE.md)**

### For Developers

1. **[Environment Setup](./environment.md)** - Development environment
2. **[API Docs (GitHub)](https://github.com/ActiveInferenceInstitute/Start/blob/main/learning/curriculum_creation/README.md)**
3. **[Tests (GitHub)](https://github.com/ActiveInferenceInstitute/Start/tree/main/tests)**

### For Researchers

1. **[Pipeline Overview](./pipeline.md)** - Research capabilities
2. **[Clone Management](./clones.md)** - Access research repositories
3. **Configuration Files** - Customize research targets

## 🌐 **External Resources**

### Active Inference Institute Ecosystem

- **Website**: [activeinference.institute](https://www.activeinference.institute/)
- **Activities**: [activities.activeinference.institute](https://activities.activeinference.institute/)
- **X (Twitter)**: [x.com/InferenceActive](https://x.com/InferenceActive)
- **Discord**: [discord.activeinference.institute](https://discord.activeinference.institute/)
- **Donate**: [donate.activeinference.institute](http://donate.activeinference.institute/)
- **YouTube**: [youtube.com/c/ActiveInference](https://www.youtube.com/c/ActiveInference/)
- **Livestreams**: [video.activeinference.institute](https://video.activeinference.institute/)

### Math & Programming Resources

- **pymdp (official)**: [infer-actively/pymdp](https://github.com/infer-actively/pymdp)
- **Active Inference Tutorial Scripts**: [rssmith33/Active-Inference-Tutorial-Scripts](https://github.com/rssmith33/Active-Inference-Tutorial-Scripts)
- **Free Energy Principle papers**: [activeinference.github.io](https://activeinference.github.io/)
- **Active Inference: Demystified and Compared**: [arXiv:1909.10863](https://arxiv.org/abs/1909.10863)
- **Step-by-Step Tutorial**: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8956124/)

### In-Repo Entry Points

- **Top-level landing page**: [Here — starting at start/here](https://github.com/ActiveInferenceInstitute/Start/blob/main/here.md)
- **Other materials**: [Inferant Stream 015-1](./other/inferant_stream_015-1.md)

## 📋 **System Capabilities**

### Research & Analysis

- **Professional Domains**: Life sciences, technology, business, healthcare, education, and whatever you prefer. 
- **Configurable Target Entities**: Political figures, scientists, tech leaders, educators, and other explicitly configured audiences
- **Live Research**: Current industry insights and professional analysis when explicitly enabled
- **Comprehensive Analysis**: Prompt-targeted domain reports with explicit quality and evidence status

### Content Generation

- **Structured Curricula**: Prompt-defined learning programs with manifest-backed quality and provenance
- **Personalized Learning**: Tailored strategies whose generated structure and evidence status are validated
- **Modular Design**: Prompt-defined learning units whose actual scope is recorded for review
- **Assessment Integration**: Built-in evaluation and progress tracking

### Visualization & Media

- **Data Visualizations**: PNG charts with curriculum metrics and analysis
- **Process Diagrams**: Mermaid diagrams for structure and flow
- **Interactive Elements**: Visual learning aids and conceptual frameworks

### Multilingual Support

- **Configured Languages**: Language and script mappings are loaded from `data/config/languages.yaml`
- **Cultural Adaptation**: Full localization beyond literal translation
- **Review Boundary**: Structural and script checks are automated; language fluency and technical accuracy require human review

## 🔧 **Configuration Overview**

### Research Configuration

```yaml
# data/config/entities.yaml
entities:
  - name: "karl_friston"
    category: "scientist"
    priority: "high"

# data/config/domains.yaml
domains:
  - name: "biochemistry"
    category: "life_sciences"
    priority: "high"
```

### Command-Line Interface

```bash
# From repository root; installed commands use the locked uv environment
uv sync --all-extras --dev

# Research high-priority entities
uv run start-curriculum --non-interactive --stages entity-research \
  --entity-priority high --json

# Generate domain-specific curricula
uv run start-curriculum --non-interactive --stages domain-research \
  --domains biochemistry --json

# Create multilingual content
uv run start-curriculum --non-interactive --stages translations \
  --languages Spanish French --json

# Inspect generated output contracts and deterministic offline fixtures
uv run start-validate-outputs --check
uv run start-regenerate-offline --output-dir /tmp/start-fixtures --json
```

## 📊 **Project Structure**

```text
START/
├── src/                      # Core system implementation
├── learning/                 # Curriculum creation scripts
├── data/                     # Generated content and configuration
├── docs/                     # Comprehensive documentation
├── tests/                    # Test suite and validation
└── README.md                 # Project overview and quick start
```

## 🔄 **Development Workflow**

### Standard Development Cycle

1. **Configure targets** in `data/config/` YAML files
2. **Run research** using domain and entity scripts
3. **Generate curricula** with comprehensive content creation
4. **Create visualizations** for enhanced learning
5. **Translate content** for multilingual accessibility

### Quality Assurance

- **Comprehensive testing** with pytest and TDD approach
- **Code quality** with ruff linting and black formatting
- **API integration testing** for Perplexity and OpenRouter
- **Content validation** against Active Inference standards

## 📞 **Getting Help**

### Documentation Resources

- **This documentation hub** for comprehensive guides
- **Inline code documentation** with detailed docstrings
- **Example usage** in test files and usage guides
- **Configuration examples** in YAML files

### Community & Support

- **Active Inference Institute** for research questions
- **GitHub Issues** for technical problems and feature requests
- **Test Suite** for usage examples and validation patterns

---

**START** represents a new paradigm in educational content creation, combining cutting-edge AI research capabilities with comprehensive pedagogical design to produce world-class Active Inference curricula tailored to any professional domain or individual learner.

## Institute Shortlinks (email-friendly)

- 2025: [2025.activeinference.institute](https://2025.activeinference.institute/)
- Active Blockference: [active-blockference.activeinference.institute](https://active-blockference.activeinference.institute)
- Activities: [activities.activeinference.institute](https://activities.activeinference.institute)
- Affordances: [affordances.activeinference.institute](https://affordances.activeinference.institute/)
- Board of Directors (BoD): [bod.activeinference.institute](https://bod.activeinference.institute)
- Discord: [discord.activeinference.institute](https://discord.activeinference.institute)
- Donate: [donate.activeinference.institute](http://donate.activeinference.institute)
- Ecosystem: [ecosystem.activeinference.institute](https://ecosystem.activeinference.institute)
- EduActive: [eduactive.activeinference.institute](https://eduactive.activeinference.institute)
- Fellows: [fellows.activeinference.institute](https://fellows.activeinference.institute)
- Fellowship: [fellowship.activeinference.institute](https://fellowship.activeinference.institute)
- Internships: [intern.activeinference.institute](https://intern.activeinference.institute)
- Knowledge Engineering: [knowledge-engineering.activeinference.institute](https://knowledge-engineering.activeinference.institute)
- Measure: [measure.activeinference.institute](https://measure.activeinference.institute)
- Mentorship: [mentorship.activeinference.institute](https://mentorship.activeinference.institute/)
- Newsletter: [newsletter.activeinference.institute](https://newsletter.activeinference.institute)
- Obsidian (Knowledge Graph): [obsidian.activeinference.institute](https://obsidian.activeinference.institute)
- Ontology: [ontology.activeinference.institute](https://ontology.activeinference.institute)
- Partnership: [partnership.activeinference.institute](https://partnership.activeinference.institute)
- Partnerships: [partnerships.activeinference.institute](https://partnerships.activeinference.institute)
- PayPal: [paypal.activeinference.institute](https://paypal.activeinference.institute)
- Prepare: [prepare.activeinference.institute](https://prepare.activeinference.institute)
- Projects: [projects.activeinference.institute](https://projects.activeinference.institute)
- ReInference: [reinference.activeinference.institute](https://reinference.activeinference.institute)
- RxInfer: [rxinfer.activeinference.institute](https://rxinfer.activeinference.institute)
- SAB: [sab.activeinference.institute](https://sab.activeinference.institute)
- Strategy: [strategy.activeinference.institute](https://strategy.activeinference.institute)
- Support: [support.activeinference.institute](https://support.activeinference.institute)
- Symposium: [symposium.activeinference.institute](https://symposium.activeinference.institute/)
- Textbook Group: [textbook-group.activeinference.institute](https://textbook-group.activeinference.institute)
- TNB: [tnb.activeinference.institute](https://tnb.activeinference.institute/)
- Video: [video.activeinference.institute](https://video.activeinference.institute)
- Volunteer: [volunteer.activeinference.institute](https://volunteer.activeinference.institute)
- Wave Hypothesis: [wave-hypothesis.activeinference.institute](https://wave-hypothesis.activeinference.institute/)
- Weekly: [weekly.activeinference.institute](https://weekly.activeinference.institute/)
- Welcome: [welcome.activeinference.institute](https://welcome.activeinference.institute)

- Community & Project
  - Contributing: ./CONTRIBUTING.md
  - FAQ: ./FAQ.md
  - Roadmap: ./ROADMAP.md
