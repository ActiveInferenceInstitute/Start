# External Repositories & Clone Management

The START project integrates with several Active Inference and computational neuroscience repositories to provide comprehensive educational resources and examples. These can be optionally cloned into `src/_clones/` for local development and curriculum enhancement.

## Repository Ecosystem

### Core Knowledge Resources

#### **cognitive** (Active Inference Institute Knowledge Graph)
- **URL**: [github.com/ActiveInferenceInstitute/cognitive](https://github.com/ActiveInferenceInstitute/cognitive)
- **Destination**: `src/_clones/cognitive`
- **Purpose**: Knowledge graph backing for curriculum development, providing structured Active Inference concepts and relationships
- **Integration**: Used as reference material for comprehensive curriculum content and concept validation

#### **RxInferExamples.jl** (Bayesian Inference Examples)
- **URL**: [github.com/docxology/RxInferExamples.jl](https://github.com/docxology/RxInferExamples.jl/)
- **Destination**: `src/_clones/RxInferExamples.jl`
- **Purpose**: Practical examples of Bayesian inference and probabilistic programming
- **Integration**: Source of hands-on exercises and computational examples for technical curricula

### Implementation Resources

#### **ActiveInference.jl** (Julia Implementation)
- **URL**: [github.com/docxology/ActiveInference.jl/tree/textbook](https://github.com/docxology/ActiveInference.jl/tree/textbook)
- **Destination**: `src/_clones/ActiveInference.jl`
- **Branch**: `textbook` (educational focus)
- **Purpose**: Julia-based Active Inference implementation with educational documentation
- **Integration**: Technical reference and code examples for programming-focused curricula

#### **pymdp** (Python Active Inference)
- **URL**: [github.com/docxology/pymdp/tree/textbook](https://github.com/docxology/pymdp/tree/textbook)
- **Destination**: `src/_clones/pymdp`
- **Branch**: `textbook` (educational focus)
- **Purpose**: Python implementation of Active Inference and Free Energy Principle
- **Integration**: Hands-on programming exercises and computational examples

## Clone Management

### Automated Cloning

Use the integrated clone utility for consistent repository management:

```bash
# Core knowledge graph
uv run python src/repos/clone_repo.py --url https://github.com/ActiveInferenceInstitute/cognitive --dest src/_clones/cognitive --shallow

# Bayesian inference examples
uv run python src/repos/clone_repo.py --url https://github.com/docxology/RxInferExamples.jl --dest src/_clones/RxInferExamples.jl --shallow

# Julia Active Inference (textbook branch)
uv run python src/repos/clone_repo.py --url https://github.com/docxology/ActiveInference.jl --dest src/_clones/ActiveInference.jl --branch textbook --shallow

# Python Active Inference (textbook branch)  
uv run python src/repos/clone_repo.py --url https://github.com/docxology/pymdp --dest src/_clones/pymdp --branch textbook --shallow
```

### Manual Repository Management

```bash
# Clone with specific options
git clone --shallow-since="2023-01-01" --branch textbook https://github.com/docxology/ActiveInference.jl src/_clones/ActiveInference.jl

# Update existing clones
cd src/_clones/cognitive && git pull origin main
cd src/_clones/pymdp && git pull origin textbook
```

## Integration with Curriculum Pipeline

### Knowledge Graph Integration
- **cognitive** repository provides structured concept relationships
- Used by domain analysis scripts to validate Active Inference concepts
- Enhances curriculum content with authoritative concept definitions

### Code Example Integration
- **pymdp** and **ActiveInference.jl** provide working code examples
- Integrated into hands-on curriculum sections
- Used for generating programming exercises and computational labs

### Educational Resource Enhancement
- **RxInferExamples.jl** provides practical Bayesian inference examples
- Textbook branches focus on educational content and clear explanations
- Examples adapted for domain-specific curriculum applications

## Repository Structure After Cloning

```
src/_clones/
├── cognitive/                 # Knowledge graph and concept definitions
│   ├── content/              # Structured Active Inference content
│   └── ontologies/           # Formal concept relationships
├── RxInferExamples.jl/       # Bayesian inference examples
│   ├── notebooks/            # Jupyter notebooks with examples
│   └── scripts/              # Standalone example scripts
├── ActiveInference.jl/       # Julia Active Inference implementation
│   ├── docs/                 # Educational documentation
│   ├── examples/             # Code examples and tutorials
│   └── src/                  # Core implementation
└── pymdp/                    # Python Active Inference
    ├── notebooks/            # Educational notebooks
    ├── examples/             # Example scripts and demonstrations
    └── pymdp/                # Core Python package
```

## Usage in Curriculum Development

### Content Enhancement
- Reference cloned repositories for authoritative Active Inference content
- Adapt examples from implementation repositories for specific domains
- Use knowledge graph structure to ensure comprehensive concept coverage

### Technical Integration
- Import code examples into curriculum programming sections
- Generate domain-specific computational exercises
- Provide working implementations for hands-on learning

### Quality Assurance
- Validate curriculum content against authoritative sources
- Ensure technical accuracy using reference implementations
- Maintain consistency with Active Inference Institute standards
