# External Repositories & Clone Management

The START project can optionally clone several Active Inference and
computational neuroscience repositories into `src/_clones/` for local
inspection and curriculum development. Cloned content is reference material
only: it is not automatically treated as verified evidence, imported into
generated curricula, or included in the release bundle.

## Repository Ecosystem

### Core Knowledge Resources

#### **cognitive** (Active Inference Institute Knowledge Graph)

- **URL**: [github.com/ActiveInferenceInstitute/cognitive](https://github.com/ActiveInferenceInstitute/cognitive)
- **Destination**: `src/_clones/cognitive`
- **Purpose**: Knowledge graph backing for curriculum development, providing structured Active Inference concepts and relationships
- **Integration**: Optional reference material; any use in a published artifact must be cited and reviewed

#### **RxInferExamples.jl** (Bayesian Inference Examples)

- **URL**: [github.com/docxology/RxInferExamples.jl](https://github.com/docxology/RxInferExamples.jl/)
- **Destination**: `src/_clones/RxInferExamples.jl`
- **Purpose**: Practical examples of Bayesian inference and probabilistic programming
- **Integration**: Optional source of examples; copied material requires licensing and technical review

### Implementation Resources

#### **ActiveInference.jl** (Julia Implementation)

- **URL**: [github.com/docxology/ActiveInference.jl/tree/textbook](https://github.com/docxology/ActiveInference.jl/tree/textbook)
- **Destination**: `src/_clones/ActiveInference.jl`
- **Branch**: `textbook` (educational focus)
- **Purpose**: Julia-based Active Inference implementation with educational documentation
- **Integration**: Optional technical reference; generated claims require independent source review

#### **pymdp** (Python Active Inference)

- **URL**: [github.com/docxology/pymdp/tree/textbook](https://github.com/docxology/pymdp/tree/textbook)
- **Destination**: `src/_clones/pymdp`
- **Branch**: `textbook` (educational focus)
- **Purpose**: Python implementation of Active Inference and Free Energy Principle
- **Integration**: Optional implementation reference; generated examples require execution and review

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

- Clone utility: `uv run start-clone` (the module is also importable as a Python API)

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
uv run start-clone --url https://github.com/ActiveInferenceInstitute/cognitive --dest src/_clones/cognitive --shallow

# Bayesian inference examples
uv run start-clone --url https://github.com/docxology/RxInferExamples.jl --dest src/_clones/RxInferExamples.jl --shallow

# Julia Active Inference (textbook branch)
uv run start-clone --url https://github.com/docxology/ActiveInference.jl --dest src/_clones/ActiveInference.jl --branch textbook --shallow

# Python Active Inference (textbook branch)  
uv run start-clone --url https://github.com/docxology/pymdp --dest src/_clones/pymdp --branch textbook --shallow

# Lean theorem proving (LeanNiche)
uv run start-clone --url https://github.com/docxology/lean_niche --dest src/_clones/lean_niche --shallow

# Research manuscript template (Thin Orchestrator)
uv run start-clone --url https://github.com/docxology/template --dest src/_clones/template --shallow

# VERSES AXIOM
uv run start-clone --url https://github.com/VersesTech/axiom --dest src/_clones/axiom --shallow
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
- Available for manual inspection when explicitly cloned
- Does not by itself make generated content authoritative or independently verified

### Code Example Integration

- **pymdp** and **ActiveInference.jl** provide working code examples
- May inform hands-on sections when explicitly selected by a human
- Examples must be tested, attributed, and checked against their license requirements

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

- Consult cloned repositories as candidate sources for Active Inference content
- Adapt examples only after checking provenance, license, version, and technical behavior
- Use graph structure as an organizing aid, not as independent validation

### Technical Integration

- Import code examples only through an explicit, reviewed workflow
- Generate domain-specific exercises only after executing or otherwise validating them
- Provide working implementations with source attribution and version metadata

### Quality Assurance

- Validate curriculum content against cited, independently reviewed sources
- Check technical accuracy using reference implementations without treating them as proof
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
uv run start-clone --url https://github.com/docxology/ActiveInference.jl --dest src/_clones/ActiveInference.jl --branch textbook --shallow
```
