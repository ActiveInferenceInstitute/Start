# START: Scalable, Tailored Active-inference Research & Training

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **An advanced AI-powered system for creating personalized Active Inference and Free Energy Principle curricula**

> Quick links: [Active Inference Institute Welcome](https://welcome.activeinference.institute/) • [Obsidian Knowledge Graph](https://obsidian.activeinference.institute/) (maps to cognitive repo)

START combines real-time research capabilities with sophisticated content generation to produce professional-grade, personalized educational materials for Active Inference and the Free Energy Principle. The system integrates multiple APIs, comprehensive prompt engineering, and multilingual capabilities to create world-class curricula tailored to specific domains and individual learners.

## 🚀 **Key Features**

### 🔍 **Intelligent Research**
- **Real-time Domain Analysis**: Live research using Perplexity API for current industry insights
- **Personalized Learner Profiling**: In-depth analysis of individual learning needs and backgrounds  
- **16+ Professional Domains**: Life sciences, technology, business, healthcare, education, and more
- **Configuration-Driven**: YAML-based target management with priority and category filtering
- **Enhanced Error Handling**: Robust validation and retry mechanisms for reliable operation

### ✍️ **Advanced Content Generation** 
- **Professional-Grade Curricula**: 40-60 hour structured learning programs
- **Comprehensive Modules**: 3-5 hour learning units with integrated assessments
- **5,000-8,000 Word Analyses**: Deep personalization and domain integration
- **Enhanced Prompts**: 6-9 section frameworks with validation and quality assurance
- **Content Quality Validation**: Automatic checking for completeness and consistency

### 📊 **Rich Visualizations**
- **Data Charts**: PNG visualizations of curriculum metrics and learning analytics
- **Process Diagrams**: Mermaid flowcharts showing curriculum structure and pathways
- **Interactive Elements**: Visual learning aids and conceptual frameworks
- **Metrics Dashboard**: Comprehensive curriculum analysis and reporting

### 🌍 **Multilingual Excellence**
- **11+ Languages**: Chinese, Spanish, Arabic, Hindi, French, Japanese, Russian, Swahili, Tagalog, and custom languages
- **Cultural Adaptation**: Full localization beyond literal translation
- **Professional Quality**: Native-speaker level fluency with technical accuracy
- **Smart Language Handling**: Flexible language support with custom language warnings

### 🧪 **Comprehensive Testing & Quality Assurance**
- **375+ Test Cases**: Extensive unit and integration test coverage
- **API Validation**: Robust testing of all external API integrations
- **Error Scenario Coverage**: Comprehensive testing of edge cases and error conditions
- **Continuous Integration**: Automated testing pipeline ensuring reliability

## 📦 **Core Pipeline Scripts**

### Configuration-Based Research
```bash
learning/curriculum_creation/
├── 1_Research_Domain.py    # Domain analysis with online research
├── 1_Research_Entity.py    # Audience profiling and personalization  
├── 2_Write_Introduction.py # Comprehensive curriculum generation
├── 3_Introduction_Visualizations.py # Charts and diagrams
└── 4_Translate_Introductions.py     # Multilingual content
```

### Enhanced Command-Line Interface
```bash
# Research high-priority entities
python 1_Research_Entity.py --priority high

# Research specific domain with overwrite
python 1_Research_Domain.py --domain biochemistry --overwrite

# Filter by category and priority
python 1_Research_Domain.py --category life_sciences --priority high

# Generate multilingual content
python 4_Translate_Introductions.py --languages Spanish French German
```

### Supporting Infrastructure
```bash
src/
├── common/          # Shared utilities (config, paths, prompts, I/O)
├── perplexity/      # API integration (Perplexity, OpenRouter)
├── config/          # Configuration management
└── visualization/   # Chart and diagram generation
```

## 🛠️ **Quick Installation**

### Prerequisites
- Python 3.10+ (3.11+ recommended)
- [uv package manager](https://astral.sh/uv)
- Perplexity API key for research
- OpenRouter API key for content generation

### Installation Steps
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and set up project
git clone https://github.com/ActiveInferenceInstitute/Start.git
cd Start

# Install dependencies
uv sync --all-extras --dev

# Download language models
uv run python -m spacy download en_core_web_sm

# Configure API keys
cp .env.example .env
$EDITOR .env  # Add PERPLEXITY_API_KEY and OPENROUTER_API_KEY

# Verify installation
uv run pytest -q
uv run ruff check .
uv run black --check .
```

## 🎯 **Getting Started**

### 1. First Research Session
```bash
# Set environment for proper imports
export PYTHONPATH=$(pwd):$PYTHONPATH

# Research a domain (creates comprehensive analysis)
uv run python learning/curriculum_creation/1_Research_Domain.py --domain biochemistry

# Research an entity (creates personalized profile)  
uv run python learning/curriculum_creation/1_Research_Entity.py --entity karl_friston
```

### 2. Generate Comprehensive Curriculum
```bash
# Generate curricula from research (40-60 hour programs)
uv run python learning/curriculum_creation/2_Write_Introduction.py

# Create visualizations (PNG charts + Mermaid diagrams)
uv run python learning/curriculum_creation/3_Introduction_Visualizations.py

# Translate to multiple languages (with cultural adaptation)
uv run python learning/curriculum_creation/4_Translate_Introductions.py --languages Spanish French
```

### 3. Explore Generated Content
```bash
# Check generated research
ls data/domain_research/     # Domain analyses
ls data/audience_research/   # Entity profiles

# Check curriculum content
ls data/written_curriculums/     # Generated curricula
ls data/visualizations/          # Charts and diagrams  
ls data/translated_curriculums/  # Multilingual content
```

## ⚙️ **Configuration System**

### Research Targets Configuration
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

### Advanced Filtering Options
```bash
# Process only high-priority items
python 1_Research_Entity.py --priority high
python 1_Research_Domain.py --priority high

# Filter by professional category
python 1_Research_Domain.py --category life_sciences
python 1_Research_Domain.py --category technology

# Process specific targets
python 1_Research_Entity.py --entity karl_friston
python 1_Research_Domain.py --domain biochemistry

# Control overwrite behavior
python 1_Research_Domain.py --overwrite  # Force overwrite existing
# Default: skip existing files automatically
```

## 📈 **Generated Content Quality**

### Research Analysis (Enhanced with new prompts)
- **Domain Reports**: 3,000-5,000 words of professional landscape analysis
- **Entity Profiles**: 5,000-8,000 words of personalized learning strategies
- **Real-time Data**: Current industry insights via Perplexity API
- **Evidence-Based**: Grounded in current research and best practices

### Curriculum Content (Professional-grade)
- **Structured Programs**: 40-60 hour comprehensive learning experiences
- **Modular Design**: 6-9 section frameworks with integrated assessments
- **Practical Applications**: Real-world case studies and hands-on exercises
- **Professional Integration**: Career development and workplace applications

### Multilingual Adaptations (Cultural excellence)
- **Full Localization**: Examples adapted to target cultures
- **Technical Accuracy**: Precise translation of scientific terms
- **Educational Quality**: Maintains pedagogical effectiveness across languages
- **Native Fluency**: Professional-quality content for each target language

## 🏗️ **System Architecture**

### Data Flow Pipeline
```
Configuration → Research → Content Generation → Visualization → Translation
      ↓             ↓              ↓                ↓             ↓
 data/config/  data/research/ data/curricula/  data/charts/  data/multilingual/
```

### Prompt Template System
```
data/prompts/
├── research_domain_analysis.md     # 6-section domain framework (3K-5K words)
├── research_domain_curriculum.md   # 9-section curriculum generation (40-60 hours)
├── research_entity.md              # 6-section personalization (5K-8K words)
├── curriculum_section.md           # Comprehensive module creation (3-5 hours)
└── translation.md                  # 7-section multilingual framework
```

### Quality Assurance Framework
- **Comprehensive Testing**: pytest with TDD approach
- **Code Quality**: ruff linting and black formatting  
- **API Integration**: Real-time validation with Perplexity and OpenRouter
- **Content Standards**: Professional-grade educational material validation

## 📊 **Example Outputs**

### Generated Research Files
```bash
# Domain research (382 lines, 24KB)
data/domain_research/biochemistry_research_20250902_152829.md

# Entity research (16KB personalized analysis)  
data/audience_research/karl_friston_research_20250902.json

# Curriculum content (240 lines comprehensive program)
data/written_curriculums/biochemistry/complete_curriculum_20250902.md

# Multilingual versions (318-324 lines each)
data/translated_curriculums/spanish/biochemistry_curriculum_spanish.md
data/translated_curriculums/french/biochemistry_curriculum_french.md
```

### Visualization Outputs
```bash
# PNG charts showing curriculum metrics
data/visualizations/curriculum_metrics.png

# Mermaid diagrams for structure and flow
data/visualizations/curriculum_structure.mmd
data/visualizations/biochemistry_flow.mmd
```

## 🎯 **Use Cases & Applications**

### Educational Institutions
- **University Courses**: Neuroscience, psychology, AI program curricula
- **Professional Development**: Corporate training for data science, healthcare, management
- **Research Training**: Graduate-level courses with theory and implementation

### Individual Learning  
- **Self-Directed Study**: Personalized curricula based on background and goals
- **Career Transition**: Bridge existing expertise to Active Inference applications
- **Academic Research**: Foundation for thesis work and research projects

### Organizational Training
- **Technology Companies**: AI ethics, decision frameworks, intelligent systems
- **Healthcare Organizations**: Evidence-based practice, clinical decision support
- **Consulting Firms**: Advanced analytical frameworks, problem-solving methodologies

## 📚 **Comprehensive Documentation**

### 🚀 **Getting Started Guides**
- **[Environment Setup](docs/environment.md)** - Complete installation and development setup
- **[Pipeline Overview](docs/pipeline.md)** - System architecture and workflow detailed guide
- **[Usage Guide](learning/curriculum_creation/USAGE_GUIDE.md)** - Step-by-step curriculum creation

### 🔧 **Technical References** 
- **[API Documentation](learning/curriculum_creation/README.md)** - Integration guides and examples
- **[Configuration Reference](docs/README.md)** - YAML schema and configuration options
- **[Clone Management](docs/clones.md)** - External repository integration

### 📋 **Advanced Topics**
- **Prompt Engineering**: Custom templates in `data/prompts/`
- **Extension Development**: Adding new domains and entities
- **Integration Patterns**: Incorporating START into existing workflows

## 🤝 **Active Inference Ecosystem Integration**

START connects with the broader Active Inference Institute ecosystem:

- **[Welcome Portal](https://welcome.activeinference.institute/)** - Community entry point and resources
- **[Knowledge Graph](https://obsidian.activeinference.institute/)** - Comprehensive concept mapping
- **[Cognitive Repository](https://github.com/ActiveInferenceInstitute/cognitive)** - Structured knowledge base
- **[Implementation Packages](docs/clones.md)** - Julia and Python Active Inference tools

### External Knowledge Resources
- **cognitive** knowledge base: [github.com/ActiveInferenceInstitute/cognitive](https://github.com/ActiveInferenceInstitute/cognitive)
- **RxInfer examples**: [github.com/docxology/RxInferExamples.jl](https://github.com/docxology/RxInferExamples.jl/)
- **ActiveInference.jl (textbook)**: [github.com/docxology/ActiveInference.jl/tree/textbook](https://github.com/docxology/ActiveInference.jl/tree/textbook)
- **pymdp (textbook)**: [github.com/docxology/pymdp/tree/textbook](https://github.com/docxology/pymdp/tree/textbook)

## 🔄 **Development Roadmap**

### Immediate Enhancements
- [ ] Expanded domain coverage (20+ professional fields)
- [ ] Enhanced visualization types (interactive diagrams, 3D models)
- [ ] Integration with learning management systems (LMS)
- [ ] Mobile-responsive curriculum formats

### Future Vision
- [ ] Real-time personalization based on learning progress
- [ ] Community-contributed domain and entity profiles  
- [ ] AR/VR learning platform integration
- [ ] Automated assessment and credentialing systems

## 🤝 **Contributing**

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code style and development process
- Pull request procedure and review guidelines
- Community guidelines and communication
- Testing requirements and quality standards

### Development Workflow
```bash
# Set up development environment
uv sync --all-extras --dev

# Run quality checks
uv run pytest -q           # Test suite
uv run ruff check .        # Linting
uv run black --check .     # Formatting

# Development with proper Python path
export PYTHONPATH=$(pwd):$PYTHONPATH
```

## 🧪 **Development & Testing**

### Testing Framework
The project includes a comprehensive testing framework with 375+ test cases covering:
- **Unit Tests**: Individual component testing with proper mocking
- **Integration Tests**: End-to-end pipeline validation  
- **API Tests**: External service integration validation
- **Error Handling**: Edge cases and failure scenarios

### Running Tests
```bash
# Run full test suite
uv run pytest

# Run specific test categories  
uv run pytest -m "not integration"     # Skip integration tests
uv run pytest -m integration           # Only integration tests
uv run pytest tests/test_domain.py     # Specific test file

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Set environment for GUI-free testing
export MPLBACKEND=Agg
uv run pytest
```

### Development Guidelines
- **Code Quality**: Black formatting, Ruff linting, comprehensive type hints
- **Testing**: Write tests for all new functionality with proper mocking
- **Documentation**: Include docstrings and update relevant docs
- **Error Handling**: Implement graceful degradation and user-friendly messages

### Project Structure
```
├── src/                    # Core system modules
│   ├── common/            # Shared utilities
│   ├── perplexity/        # API integrations  
│   ├── system/            # System utilities
│   └── terminal/          # CLI components
├── learning/              # Educational pipeline scripts
├── tests/                 # Test suite (375+ tests)
├── docs/                  # Documentation
│   ├── TESTING.md         # Testing guide
│   └── environment.md     # Setup instructions
└── data/                  # Generated content storage
```

For detailed testing information, see [docs/TESTING.md](docs/TESTING.md).

## 📄 **License & Citation**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Citation
If you use START in academic work, please cite:
```
START: Scalable, Tailored Active-inference Research & Training
Active Inference Institute (2024)
https://github.com/ActiveInferenceInstitute/Start
```

## 🙏 **Acknowledgments**

- **Active Inference Institute** for foundational research and community support
- **Karl Friston** for the Free Energy Principle and Active Inference frameworks  
- **Contributors** to pymdp, ActiveInference.jl, and related implementation packages
- **Educational partners** providing feedback and validation for curriculum effectiveness
- **Open source community** for tools, libraries, and collaborative development

## 📬 **Contact & Support**

- **GitHub Issues**: [Project Issues](https://github.com/ActiveInferenceInstitute/Start/issues)
- **Community**: [Active Inference Institute](https://www.activeinference.institute/)
- **Email**: [contact@activeinference.institute](mailto:contact@activeinference.institute)

## 🌟 **Join the Community**

Together we're building tools to make Active Inference accessible and adaptable across domains, languages, and perspectives. **START** represents a new paradigm in AI-powered educational content creation - join us in making advanced neuroscience and cognitive science accessible to learners worldwide!

**[📚 Explore Documentation](docs/README.md) | [🚀 Get Started](#-quick-installation) | [🤝 Join Community](https://www.activeinference.institute/)**