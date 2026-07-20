# START: A Reviewable Filesystem Pipeline for Evidence-Labeled Learning Artifacts

## Abstract

START is a research and curriculum tool that assembles configured research
inputs, provider-assisted content, translations, and derived visualizations
into reviewable filesystem artifacts. Its central design claim is operational:
an artifact is safer to publish when its identity, inputs, evidence status,
quality result, and generation history are visible at the point of review.
START therefore uses a typed, resumable pipeline with atomic writes and a run
manifest rather than treating a successful process exit as evidence of a valid
publication.

This document is a manuscript-facing engineering note. It does not claim that
generated content is independently verified, that synthetic foundation
material is live research, or that the pipeline has demonstrated learning
outcomes in human subjects.

## Contribution and scope

The contribution is a compact operating contract for a single-user research
and curriculum workflow:

1. stable configuration and item identifiers;
2. dependency-aware stages (`acquire → prepare → process → parse → render`);
3. provider boundaries with bounded retries, cancellation, redaction, and
   usage telemetry;
4. quality and provenance gates before publication;
5. deterministic offline fixtures and hashed visualization bundles;
6. staged entrypoints that delegate to one canonical orchestration layer.

The system is not a multi-user platform, a fact-checking service, an automated
ethics decision-maker, or a substitute for domain-expert review.

## Method

The methods protocol is recorded in [Methods and Evidence Protocol](methods.md).
The first-principles function is to make reviewable artifacts, not to maximize
the number of generated files. The scientific method is applied as a sequence
of falsifiable engineering hypotheses, controlled offline fixtures, measured
quality outputs, and iterative repairs.

The primary unit of analysis is an artifact record. It contains a stable item
identity, producing stage, regular-file path, content hash, status, and
provenance. The primary unit of execution is a run manifest. It records the
configuration digest, stage results, provider and prompt metadata, usage,
quality status, errors, and artifact records.

## Evidence boundary

START makes a deliberate distinction between:

- evidence obtained from a live provider;
- source material supplied as an input;
- synthetic or offline fixture content;
- derived visual summaries.

`Synthetic_FEP-ActInf.md` is foundational synthetic material. It is useful for
offline execution but is not a live source and is not independently verified.
The same distinction is carried into generated metadata and publication-mode
validation.

## Results reporting

Results must be generated from the current checkout rather than copied into a
static claim. Use:

```bash
uv run pytest --collect-only -q
uv run pytest --cov=src --cov-branch --cov-report=term-missing -q
uv run python -m scripts.validate_repository
uv run mkdocs build --strict
uv run start-regenerate-offline --output-dir /tmp/start-manuscript-fixture --json
```

The commands above report current counts and gates. They are intentionally not
hard-coded here because counts, dependencies, and generated inputs change.

## Limitations and next study

The present record evaluates software contracts and artifact integrity, not
learner outcomes or provider factuality. A future study should preregister a
human-review rubric, define a comparison condition, measure reviewer agreement,
and obtain appropriate consent before evaluating educational effectiveness.
Any live pilot must be explicitly budgeted, source-reviewed, and kept separate
from the offline reproducibility evidence.
