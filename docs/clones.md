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

#### **lean_niche** (Lean Theorem Proving & Verification)

- **URL**: [github.com/docxology/lean_niche](https://github.com/docxology/lean_niche)
- **Destination**: `src/_clones/lean_niche`
- **Purpose**: Lean environment for formal methods, proofs, and verification
- **Integration**: Formal verification examples and references for rigorous curricula

#### **template** (Thin Orchestrator Research Template)

- **URL**: [github.com/docxology/template](https://github.com/docxology/template)
- **Destination**: `src/_clones/template`
- **Purpose**: Research manuscript utilities using thin orchestrator pattern
- **Integration**: Reference for TDD-first pipelines and PDF generation

#### **axiom** (VERSES AXIOM)

- **URL**: [github.com/VersesTech/axiom](https://github.com/VersesTech/axiom)
- **Destination**: `src/_clones/axiom`
- **Purpose**: Knowledge operating system components and interfaces
- **Integration**: Reference architecture and potential data integration

## Clone Management

Steps

- Select repository (knowledge, implementation, examples)
- If not present, run clone utility
- If present, update via `git pull`
- Verify destination and integration
- Use in pipeline (concept validation, examples, exercises)

Links

- Clone utility: `src/repos/clone_repo.py`

### Interactive (recommended)

Use the Repository Manager from the main runner for a guided flow:

```bash
./run.sh
# Choose: "Repository Manager"
```

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

# Lean theorem proving (LeanNiche)
uv run python src/repos/clone_repo.py --url https://github.com/docxology/lean_niche --dest src/_clones/lean_niche --shallow

# Research manuscript template (Thin Orchestrator)
uv run python src/repos/clone_repo.py --url https://github.com/docxology/template --dest src/_clones/template --shallow

# VERSES AXIOM
uv run python src/repos/clone_repo.py --url https://github.com/VersesTech/axiom --dest src/_clones/axiom --shallow
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

```text
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
└── lean_niche/               # Lean theorem proving & verification environment
    ├── src/                  # Lean and Python sources
    ├── docs/                 # Project docs and verification workflows
    └── examples/             # Example proofs and verification scripts
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

## Verification & Maintenance

### Verify Clone Integrity

```bash
# Path exists and is a git repo
test -d src/_clones/cognitive/.git && echo OK

# Show remote and branch
git -C src/_clones/cognitive remote -v
git -C src/_clones/cognitive branch --show-current
```

### Update Clones Safely

```bash
git -C src/_clones/cognitive fetch --prune
git -C src/_clones/cognitive pull --ff-only origin main

git -C src/_clones/pymdp fetch --prune
git -C src/_clones/pymdp pull --ff-only origin textbook
```

### Re-clone When Needed

```bash
rm -rf src/_clones/ActiveInference.jl
uv run python src/repos/clone_repo.py --url https://github.com/docxology/ActiveInference.jl --dest src/_clones/ActiveInference.jl --branch textbook --shallow
```
